"""
OCR Pipeline Pipe for Open WebUI
- Step 1: If images are provided, run OCR via OCR_MODEL_ID to extract text.
- Step 2: Call MAIN_MODEL_ID with the user's prompt and the OCR text.
- No external dependencies; uses internal open_webui.generate_chat_completion.
- Compatible with latest Open WebUI unified endpoint.
"""
from typing import Any, Dict, List, Optional, Tuple
from copy import deepcopy

from pydantic import BaseModel, Field
from fastapi import Request

from open_webui.models.users import Users
from open_webui.utils.chat import generate_chat_completion


class Pipe:
    class Valves(BaseModel):
        OCR_MODEL_ID: str = Field(
            default="mistral-small3.2:24b-instruct-2506-q8_0",
            description="Model used for OCR (vision-enabled).",
        )
        MAIN_MODEL_ID: str = Field(
            default="gpt-oss:20b",
            description="Model used to answer using OCR text + user prompt.",
        )
        OCR_MAX_CHARS: int = Field(
            default=60000,
            description="Maximum characters from OCR to inject into the main prompt (truncated if longer).",
        )

    def __init__(self):
        self.valves = self.Valves()

    def pipes(self) -> List[Dict[str, str]]:
        # Expose this Pipe as a single selectable "model" in Open WebUI
        return [
            {"id": "pipe/ocr-compose", "name": "PIPE: OCR ➜ Compose"},
        ]

    async def pipe(
        self,
        body: Dict[str, Any],
        __user__: Dict[str, Any],
        __request__: Request,
    ):
        """
        Main entrypoint. Optionally runs an OCR step, then composes the final answer with MAIN_MODEL_ID.
        This uses the internal generate_chat_completion endpoint to ensure maximum compatibility.
        """
        user = Users.get_user_by_id(__user__["id"])

        # Detect whether the incoming payload contains images
        has_imgs, last_user_images, last_user_files, content_image_parts = self._extract_image_artifacts(body)

        ocr_text = ""
        if has_imgs:
            # Build a minimal OCR prompt using the last user message's images/files
            ocr_body = {
                "model": self.valves.OCR_MODEL_ID,
                "stream": False,  # Do not stream intermediary OCR to the UI
                "messages": self._build_ocr_messages(
                    body,
                    last_user_images=last_user_images,
                    last_user_files=last_user_files,
                    content_image_parts=content_image_parts,
                ),
            }
            try:
                ocr_resp = await generate_chat_completion(__request__, ocr_body, user)
                ocr_text = self._extract_text_from_response(ocr_resp)
            except Exception as e:
                # If OCR step fails for any reason, fallback to empty OCR text
                ocr_text = ""

        # Prepare the final body for MAIN_MODEL_ID
        final_body = deepcopy(body)
        final_body["model"] = self.valves.MAIN_MODEL_ID

        # Sanitize messages for MAIN_MODEL_ID (e.g., strip images if the model is not vision capable)
        final_body["messages"] = self._sanitize_messages_for_main(final_body.get("messages", []))

        if ocr_text:
            # Respect max length to avoid blowing token budgets
            if len(ocr_text) > self.valves.OCR_MAX_CHARS:
                ocr_text = ocr_text[: self.valves.OCR_MAX_CHARS] + "\n\n[...truncated]"

            ocr_context = {
                "role": "system",
                "content": (
                    "OCR_TEXT extracted from user-provided images follows.\n"
                    "Use it alongside the user's prompt to answer accurately.\n\n"
                    f"{ocr_text}"
                ),
            }
            # Prepend our OCR context at the beginning so it's available to the model
            final_body["messages"].insert(0, ocr_context)

        # Delegate to Open WebUI's unified chat completion (streams if requested)
        return await generate_chat_completion(__request__, final_body, user)

    def _extract_image_artifacts(
        self, body: Dict[str, Any]
    ) -> Tuple[bool, List[str], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Attempts to detect images from the last user message and the conversation.
        Returns:
          - has_images: bool
          - last_user_images: list of image URLs (message-level 'images')
          - last_user_files: list of file dicts from last message where type is image/*
          - content_image_parts: list of content parts of type image_url/input_image
        """
        messages = body.get("messages", []) or []
        if not messages:
            return False, [], [], []

        last_user_msg = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg
                break

        last_user_images: List[str] = []
        last_user_files: List[Dict[str, Any]] = []
        content_image_parts: List[Dict[str, Any]] = []

        def collect_from_message(msg: Dict[str, Any]):
            nonlocal last_user_images, last_user_files, content_image_parts
            # Direct images array (common in Open WebUI)
            if isinstance(msg.get("images"), list):
                for u in msg["images"]:
                    if isinstance(u, str) and u:
                        last_user_images.append(u)

            # Files list that might include images
            if isinstance(msg.get("files"), list):
                for f in msg["files"]:
                    if isinstance(f, dict):
                        ftype = (f.get("type") or f.get("mimetype") or "").lower()
                        if ftype.startswith("image"):
                            last_user_files.append(f)

            # OpenAI-format content parts (image_url/input_image)
            content = msg.get("content")
            if isinstance(content, list):
                for part in content:
                    if not isinstance(part, dict):
                        continue
                    ptype = str(part.get("type", "")).lower()
                    if ptype in ("image_url", "input_image", "image"):
                        content_image_parts.append(part)
                    elif ptype == "tool_result":
                        # Some providers wrap image results; ignore here
                        pass

        # Collect from the last user message first
        if last_user_msg:
            collect_from_message(last_user_msg)

        has_any = bool(last_user_images or last_user_files or content_image_parts)
        return has_any, last_user_images, last_user_files, content_image_parts

    def _build_ocr_messages(
        self,
        original_body: Dict[str, Any],
        last_user_images: List[str],
        last_user_files: List[Dict[str, Any]],
        content_image_parts: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Build a minimal, robust OCR prompt that passes through the user's images.
        We favor using the last user message's image artifacts for clarity.
        """
        messages: List[Dict[str, Any]] = []
        messages.append(
            {
                "role": "system",
                "content": (
                    "You are an OCR engine. Extract all visible text verbatim from the provided image(s).\n"
                    "- Preserve natural reading order, line breaks and headings.\n"
                    "- Do not translate; keep original language.\n"
                    "- If multiple images, separate each image's text by a blank line and a line with three dashes (---).\n"
                    "- Return plain text only, no explanations."
                ),
            }
        )

        user_msg: Dict[str, Any] = {
            "role": "user",
            "content": "Transcribe all text from the attached image(s).",
        }

        # Provide multiple representations to maximize compatibility with providers
        if last_user_images:
            user_msg["images"] = list(last_user_images)

        if last_user_files:
            user_msg["files"] = list(last_user_files)

        if content_image_parts:
            user_msg["content"] = [
                {"type": "text", "text": "Transcribe all text from the attached image(s)."}
            ] + content_image_parts

        messages.append(user_msg)
        return messages

    def _extract_text_from_response(self, resp: Dict[str, Any]) -> str:
        """
        Extract assistant text from a non-streaming response in OpenAI-like format.
        """
        try:
            if isinstance(resp, dict):
                choices = resp.get("choices") or []
                if choices:
                    msg = choices[0].get("message") or {}
                    content = msg.get("content")
                    if isinstance(content, str):
                        return content.strip()
        except Exception:
            pass
        return ""

    def _sanitize_messages_for_main(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove image artifacts from messages to avoid issues with non-vision MAIN_MODEL_ID.
        """
        sanitized: List[Dict[str, Any]] = []
        for msg in messages or []:
            m = dict(msg)  # shallow copy
            m.pop("images", None)
            m.pop("files", None)
            content = m.get("content")
            if isinstance(content, list):
                cleaned_parts: List[Dict[str, Any]] = []
                for part in content:
                    if not isinstance(part, dict):
                        cleaned_parts.append(part)
                        continue
                    ptype = str(part.get("type", "")).lower()
                    if ptype in ("image_url", "input_image", "image"):
                        # Drop image parts for non-vision models
                        continue
                    cleaned_parts.append(part)
                m["content"] = cleaned_parts
            sanitized.append(m)
        return sanitized