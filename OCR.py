"""
Multimodal Reasoning Pipeline Function for Open WebUI
- Step 1: If images are provided, run OCR via OCR_MODEL_ID to extract text and (when relevant) describe the images.
- Step 2: Call MAIN_MODEL_ID with the user's prompt plus OCR text/description/category to a reasoning capable model.
- No external dependencies; uses internal open_webui.generate_chat_completion.
- Compatible with latest Open WebUI unified endpoint.
"""

from typing import Any, Dict, List, Optional, Tuple, Callable, Awaitable
from copy import deepcopy
import re

from pydantic import BaseModel, Field
from fastapi import Request

from open_webui.models.users import Users
from open_webui.utils.chat import generate_chat_completion


class Pipe:
    class Valves(BaseModel):
        OCR_MODEL_ID: str = Field(
            default="mistral-small3.2:24b-instruct-2506-q8_0",
            description="Model used for OCR extraction/description (vision-enabled).",
        )
        MAIN_MODEL_ID: str = Field(
            default="gpt-oss:20b",
            description="Model used to reason the image + prompt.",
        )
        OCR_MAX_CHARS: int = Field(
            default=50000,
            description="Maximum characters from OCR to inject into the main prompt (truncated if longer).",
        )
        OCR_INCLUDE_DESCRIPTION: bool = Field(
            default=True,
            description="When true, the OCR step also asks for a detailed image description and a coarse category if relevant.",
        )
        OCR_DESC_MAX_CHARS: int = Field(
            default=50000,
            description="Maximum characters from OCR description to inject into the main prompt (truncated if longer).",
        )
        SHOW_OCR_RESULTS: bool = Field(
            default=True,
            description="Emit OCR results to the chat via event emitter as a preview message.",
        )
        SHOW_OCR_STATUS: bool = Field(
            default=True,
            description="Emit OCR status updates (start/complete/skip/fail).",
        )

    def __init__(self):
        self.valves = self.Valves()

    def pipes(self) -> List[Dict[str, str]]:
        # Expose this Pipe as a single selectable "model" in Open WebUI
        return [
            {"id": "multimodal-reasoner", "name": "Multimodal Reasoner"},
        ]

    async def pipe(
        self,
        body: Dict[str, Any],
        __user__: Dict[str, Any],
        __request__: Request,
        __event_emitter__: Optional[Callable[[Any], Awaitable[None]]] = None,
        __model__: Optional[dict] = None,
        __id__: Optional[str] = None,
    ):
        """
        Main entrypoint. Optionally runs an OCR step, then composes the final answer with MAIN_MODEL_ID.
        This uses the internal generate_chat_completion endpoint to ensure maximum compatibility.
        """
        user = Users.get_user_by_id(__user__["id"])

        # Detect whether the incoming payload contains images
        has_imgs, last_user_images, last_user_files, content_image_parts = (
            self._extract_image_artifacts(body)
        )

        ocr_text, ocr_desc, ocr_category = "", "", ""
        if has_imgs:
            if __event_emitter__ and self.valves.SHOW_OCR_STATUS:
                await __event_emitter__({
                    "type": "status",
                    "data": {"description": "Running OCR on attached image(s)...", "done": False},
                })
            # Build OCR+description prompt using the last user message's images/files
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
                ocr_raw = self._extract_text_from_response(ocr_resp)
                ocr_text, ocr_desc, ocr_category = self._parse_ocr_structured_output(
                    ocr_raw, include_description=self.valves.OCR_INCLUDE_DESCRIPTION
                )

                # Emit OCR preview to user
                if __event_emitter__ and self.valves.SHOW_OCR_RESULTS:
                    preview_text = ocr_text or ""
                    preview_desc = ocr_desc or ""
                    if self.valves.OCR_MAX_CHARS and len(preview_text) > self.valves.OCR_MAX_CHARS:
                        preview_text = preview_text[: self.valves.OCR_MAX_CHARS] + "\n\n[...truncated]"
                    if self.valves.OCR_DESC_MAX_CHARS and len(preview_desc) > self.valves.OCR_DESC_MAX_CHARS:
                        preview_desc = preview_desc[: self.valves.OCR_DESC_MAX_CHARS] + "\n\n[...truncated]"

                    parts: List[str] = []
                    parts.append("<details><summary>OCR Results</summary>")
                    if ocr_category:
                        parts.append(f"<p><strong>Category:</strong> {ocr_category}</p>")
                    if preview_text:
                        parts.append("<p><strong>Text:</strong></p>")
                        parts.append(f"<pre><code>{preview_text}</code></pre>")
                    else:
                        parts.append("<p><strong>Text:</strong> (no visible text)</p>")
                    if self.valves.OCR_INCLUDE_DESCRIPTION:
                        if preview_desc:
                            parts.append("<p><strong>Description:</strong></p>")
                            parts.append(f"<blockquote>{preview_desc}</blockquote>")
                        else:
                            parts.append("<p><strong>Description:</strong> (none)</p>")
                    parts.append("</details>")

                    await __event_emitter__({
                        "type": "message",
                        "data": {"content": "\n".join(parts)},
                    })

                if __event_emitter__ and self.valves.SHOW_OCR_STATUS:
                    await __event_emitter__({
                        "type": "status",
                        "data": {"description": "OCR complete.", "done": True},
                    })
            except Exception as e:
                # Fallback to empty results if OCR step fails
                ocr_text, ocr_desc, ocr_category = "", "", ""
                if __event_emitter__ and self.valves.SHOW_OCR_STATUS:
                    await __event_emitter__({
                        "type": "status",
                        "data": {"description": f"OCR failed: {e}", "done": True},
                    })
        else:
            if __event_emitter__ and self.valves.SHOW_OCR_STATUS:
                await __event_emitter__({
                    "type": "status",
                    "data": {"description": "No images detected; skipping OCR.", "done": True},
                })

        # Prepare the final body for MAIN_MODEL_ID
        final_body = deepcopy(body)
        final_body["model"] = self.valves.MAIN_MODEL_ID

        # Sanitize messages for MAIN_MODEL_ID (e.g., strip images if the model is not vision capable)
        final_body["messages"] = self._sanitize_messages_for_main(
            final_body.get("messages", [])
        )

        if ocr_text or ocr_desc or ocr_category:
            # Truncate long sections to respect context limits
            if ocr_text and len(ocr_text) > self.valves.OCR_MAX_CHARS:
                ocr_text = ocr_text[: self.valves.OCR_MAX_CHARS] + "\n\n[...truncated]"
            if ocr_desc and len(ocr_desc) > self.valves.OCR_DESC_MAX_CHARS:
                ocr_desc = (
                    ocr_desc[: self.valves.OCR_DESC_MAX_CHARS] + "\n\n[...truncated]"
                )

            context_lines: List[str] = [
                "Image understanding results extracted from user-provided image(s).",
                "Use these alongside the user's prompt to answer accurately.",
                "",
            ]
            if ocr_text:
                context_lines.append("OCR_TEXT:")
                context_lines.append(ocr_text)
                context_lines.append("")
            if self.valves.OCR_INCLUDE_DESCRIPTION and ocr_desc:
                context_lines.append("OCR_DESCRIPTION:")
                context_lines.append(ocr_desc)
                context_lines.append("")
            if ocr_category:
                context_lines.append(f"OCR_CATEGORY: {ocr_category}")

            ocr_context = {
                "role": "system",
                "content": "\n".join(context_lines).strip(),
            }
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
        sys_content = (
            (
                "You are an OCR and image-understanding assistant. Extract all visible text verbatim from the provided image(s).\n"
                "- Preserve natural reading order, line breaks and headings.\n"
                "- Do not translate; keep original language.\n"
                "- Additionally, when it is relevant to understanding user intent (e.g., quiz questions, UI screenshots, diagrams, charts, math problems, slides, whiteboards, handwritten notes, or complex scenes), include a detailed but concise description of the image(s).\n"
                "- Always format your response using this schema:\n"
                "TEXT:\n"
                "<transcribed text>\n\n"
                "---\n"
                "DESCRIPTION:\n"
                "<description or 'N/A'>\n\n"
                "---\n"
                "CATEGORY: screenshot|document|diagram|math|slide|whiteboard|handwritten_note|photo|other\n"
                "- If multiple images are present, separate each image's transcribed text in TEXT with blank lines and a line containing three dashes (---)."
            )
            if self.valves.OCR_INCLUDE_DESCRIPTION
            else (
                "You are an OCR engine. Extract all visible text verbatim from the provided image(s).\n"
                "- Preserve natural reading order, line breaks and headings.\n"
                "- Do not translate; keep original language.\n"
                "- If multiple images, separate each image's text by a blank line and a line with three dashes (---).\n"
                "- Return plain text only, no explanations."
            )
        )
        messages.append({"role": "system", "content": sys_content})

        user_msg: Dict[str, Any] = {
            "role": "user",
            "content": "Transcribe all text from the attached image(s). If requested, also provide a description and a category following the schema.",
        }

        # Provide multiple representations to maximize compatibility with providers
        if last_user_images:
            user_msg["images"] = list(last_user_images)

        if last_user_files:
            user_msg["files"] = list(last_user_files)

        if content_image_parts:
            user_msg["content"] = [
                {
                    "type": "text",
                    "text": "Transcribe all text from the attached image(s). If requested, also provide a description and a category following the schema.",
                }
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

    def _parse_ocr_structured_output(
        self, text: str, include_description: bool
    ) -> Tuple[str, str, str]:
        """
        Parse OCR model output into (text, description, category).
        Accepts both the structured schema (TEXT/DESCRIPTION/CATEGORY) and plain text.
        Returns empty strings for missing parts.
        """
        if not isinstance(text, str) or not text.strip():
            return "", "", ""

        raw = text.strip()

        # If the schema isn't present at all, treat entire content as text
        lowered = raw.lower()
        has_markers = (
            ("text:" in lowered)
            or ("description:" in lowered)
            or ("category:" in lowered)
        )

        text_lines: List[str] = []
        desc_lines: List[str] = []
        category: str = ""

        if not has_markers:
            # No structured markers: best-effort fallback
            return raw, "", ""

        current = None  # "text" or "description"
        # Precompile regex patterns
        re_text_hdr = re.compile(r"^\s*text\s*:\s*$", re.IGNORECASE)
        re_desc_hdr = re.compile(r"^\s*description\s*:\s*$", re.IGNORECASE)
        re_cat_line = re.compile(r"^\s*category\s*:\s*(.+?)\s*$", re.IGNORECASE)
        re_sep_line = re.compile(r"^\s*---\s*$")

        for line in raw.splitlines():
            if re_text_hdr.match(line):
                current = "text"
                continue
            if re_desc_hdr.match(line):
                current = "description"
                continue
            m = re_cat_line.match(line)
            if m:
                category = m.group(1).strip()
                continue
            if re_sep_line.match(line):
                # explicit separator, skip
                continue

            if current == "description":
                desc_lines.append(line)
            else:
                # default to text section when current is None or "text"
                text_lines.append(line)

        ocr_text = "\n".join(text_lines).strip()
        ocr_desc = "\n".join(desc_lines).strip()

        # Normalize category
        if category:
            c = category.strip().lower()
            c = c.replace("-", "_").replace(" ", "_")
            allowed = {
                "screenshot",
                "document",
                "diagram",
                "math",
                "slide",
                "whiteboard",
                "handwritten_note",
                "photo",
                "other",
            }
            # Simple normalization for a few common synonyms
            synonyms = {
                "handwritten": "handwritten_note",
                "handwriting": "handwritten_note",
                "webpage": "screenshot",
                "ui": "screenshot",
                "screen": "screenshot",
                "picture": "photo",
                "image": "photo",
            }
            c = synonyms.get(c, c)
            if c not in allowed:
                # Try to map by prefix
                for a in allowed:
                    if c.startswith(a):
                        c = a
                        break
                else:
                    c = ""
            category = c

        # If description is not included, drop it
        if not include_description:
            ocr_desc = ""

        # Treat "N/A" as empty
        if ocr_desc.lower() in {"n/a", "na", "none", "no description"}:
            ocr_desc = ""

        return ocr_text, ocr_desc, category

    def _sanitize_messages_for_main(
        self, messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
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
