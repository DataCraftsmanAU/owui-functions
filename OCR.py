"""
title: Multimodal Reasoning Pipe
author: Michael Jennings
author_url: https://datacraftsman.com.au
funding_url: https://github.com/DataCraftsmanAU/owui-functions/
version: 1.0
license: MIT
"""

from typing import Any, Dict, List, Optional, Tuple, Callable, Coroutine, Awaitable
from copy import deepcopy
import re
import time
import asyncio

from pydantic import BaseModel, Field
from fastapi import Request

from open_webui.models.users import Users
from open_webui.utils.chat import generate_chat_completion


class Pipe:
    class Valves(BaseModel):
        OCR_MODEL_ID: str = Field(
            default="gemma3:12b",
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
        OCR_DESC_MAX_CHARS: int = Field(
            default=50000,
            description="Maximum characters from OCR description to inject into the main prompt (truncated if longer).",
        )
        UI_MODEL_ID: str = Field(
            default="gpt-oss-20b-vision",
            description="Identifier of this pipe as shown in the model list.",
        )
        UI_MODEL_NAME: str = Field(
            default="gpt-oss-20b (vision)",
            description="Display name of this pipe as shown in the model list.",
        )
        SHOW_OCR_RESULTS: bool = Field(
            default=False,
            description="If true, emits OCR results as a message preview. Defaults to False (hidden).",
        )

    def __init__(self):
        self.valves = self.Valves()
        # Deduplicate repeating status messages across rapid successive invocations
        self._status_last_emit: Dict[str, float] = {}

    def pipes(self) -> List[Dict[str, str]]:
        # Expose this Pipe as a single selectable "model" in Open WebUI
        return [
            {"id": self.valves.UI_MODEL_ID, "name": self.valves.UI_MODEL_NAME},
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
            # Compute number of images to be processed
            try:
                image_count = 0
                # Normalize all detected image artifacts into a single list to count
                def _count_images_for_status(
                    last_user_images: List[str],
                    last_user_files: List[Dict[str, Any]],
                    content_image_parts: List[Dict[str, Any]],
                ) -> int:
                    urls: List[str] = []
                    # from images array
                    for u in last_user_images or []:
                        if isinstance(u, str) and u:
                            urls.append(u)
                    # from files
                    for f in last_user_files or []:
                        if isinstance(f, dict):
                            u = f.get("url") or f.get("path") or f.get("file_url")
                            if isinstance(u, str) and u:
                                urls.append(u)
                    # from content parts
                    for p in content_image_parts or []:
                        if isinstance(p, dict):
                            ptype = str(p.get("type", "")).lower()
                            if ptype in ("image_url", "input_image", "image"):
                                iu = p.get("image_url")
                                if isinstance(iu, dict):
                                    u = iu.get("url") or iu.get("file_url")
                                    if isinstance(u, str) and u:
                                        urls.append(u)
                                elif isinstance(iu, str) and iu:
                                    urls.append(iu)
                            else:
                                # fallback generic url fields
                                u = p.get("url") or p.get("path") or p.get("file_url")
                                if isinstance(u, str) and u:
                                    urls.append(u)
                    # dedupe
                    return len(list(dict.fromkeys([u for u in urls if isinstance(u, str) and u])))

                image_count = _count_images_for_status(
                    last_user_images, last_user_files, content_image_parts
                )
            except Exception:
                image_count = 0

            await self._emit_status_once(
                f"Running OCR on {image_count} image(s) using {self.valves.OCR_MODEL_ID}...",
                False,
                __event_emitter__,
                hidden=False,
            )

            # Define normalizer before first use to avoid UnboundLocalError
            def _normalize_to_image_content_parts_inline(
                last_user_images: List[str],
                last_user_files: List[Dict[str, Any]],
                content_image_parts: List[Dict[str, Any]],
            ) -> List[Dict[str, Any]]:
                parts: List[Dict[str, Any]] = []
                for p in content_image_parts or []:
                    if isinstance(p, dict):
                        ptype = str(p.get("type", "")).lower()
                        if ptype in ("image_url", "input_image", "image"):
                            if ptype == "image" and isinstance(p.get("url"), str):
                                parts.append(
                                    {
                                        "type": "image_url",
                                        "image_url": {"url": p["url"]},
                                    }
                                )
                            else:
                                parts.append(p)
                        elif "image_url" in p or "file_url" in p or "url" in p:
                            url = None
                            if isinstance(p.get("image_url"), dict):
                                url = p["image_url"].get("url")
                            url = url or p.get("file_url") or p.get("url")
                            if isinstance(url, str) and url:
                                parts.append(
                                    {"type": "image_url", "image_url": {"url": url}}
                                )

                for url in last_user_images or []:
                    if isinstance(url, str) and url:
                        parts.append({"type": "image_url", "image_url": {"url": url}})

                for f in last_user_files or []:
                    if isinstance(f, dict):
                        url = f.get("url") or f.get("path") or f.get("file_url")
                        if isinstance(url, str) and url:
                            parts.append(
                                {"type": "image_url", "image_url": {"url": url}}
                            )

                seen = set()
                dedup: List[Dict[str, Any]] = []
                for p in parts:
                    url = None
                    iu = p.get("image_url")
                    if isinstance(iu, dict):
                        url = iu.get("url")
                    if isinstance(url, str) and url:
                        if url in seen:
                            continue
                        seen.add(url)
                    dedup.append(p)
                return dedup

            # Build OCR+description prompt using the last user message's images/files
            # Normalize images into content parts and OCR each image individually
            image_parts: List[Dict[str, Any]] = (
                _normalize_to_image_content_parts_inline(
                    last_user_images, last_user_files, content_image_parts
                )
            )

            per_texts: List[str] = []
            per_descs: List[str] = []
            per_cats: List[str] = []

            try:
                for idx, img_part in enumerate(image_parts):
                    # Build messages for a single image (mirror inline flow below)
                    single_messages = [
                        {
                            "role": "system",
                            "content": "You are an OCR and image-understanding assistant. Extract all visible text verbatim from the provided image.\n- Preserve natural reading order, line breaks and headings.\n- Do not translate; keep original language.\n- Additionally, when it is relevant to understanding user intent, include a detailed but concise description of the image.\n- Always format your response using this schema:\nTEXT:\n<transcribed text>\n\n---\nDESCRIPTION:\n<description or 'N/A'>\n\n---\nCATEGORY: screenshot|document|diagram|math|slide|whiteboard|handwritten_note|photo|other",
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Transcribe the attached image per schema.",
                                },
                                img_part,
                            ],
                        },
                    ]
                    single_ocr_body = {
                        "model": self.valves.OCR_MODEL_ID,
                        "stream": False,
                        "messages": single_messages,
                    }
                    ocr_resp = await generate_chat_completion(
                        __request__, single_ocr_body, user, bypass_filter=True
                    )
                    ocr_raw = self._extract_text_from_response(ocr_resp)
                    t, d, c = self._parse_ocr_structured_output(ocr_raw)
                    per_texts.append(t)
                    per_descs.append(d)
                    per_cats.append(c)
                # Combine per-image results with explicit separators
                ocr_text = "\n\n---\n\n".join([t for t in per_texts if t]) or ""
                ocr_desc = "\n\n---\n\n".join([d for d in per_descs if d]) or ""
                uniq_cats = [c for c in dict.fromkeys([c for c in per_cats if c])]
                ocr_category = ", ".join(uniq_cats)

                # Emit OCR results as a normal assistant message (markdown with code blocks)
                if __event_emitter__ and self.valves.SHOW_OCR_RESULTS:
                    preview_text = ocr_text or ""
                    preview_desc = ocr_desc or ""
                    if (
                        self.valves.OCR_MAX_CHARS
                        and len(preview_text) > self.valves.OCR_MAX_CHARS
                    ):
                        preview_text = (
                            preview_text[: self.valves.OCR_MAX_CHARS]
                            + "\n\n[...truncated]"
                        )
                    if (
                        self.valves.OCR_DESC_MAX_CHARS
                        and len(preview_desc) > self.valves.OCR_DESC_MAX_CHARS
                    ):
                        preview_desc = (
                            preview_desc[: self.valves.OCR_DESC_MAX_CHARS]
                            + "\n\n[...truncated]"
                        )

                    preview_lines: List[str] = []
                    preview_lines.append("OCR Results")
                    if ocr_category:
                        preview_lines.append(f"Category: {ocr_category}")
                    preview_lines.append("")
                    preview_lines.append("Text:")
                    preview_lines.append("```")
                    preview_lines.append(preview_text or "(no visible text)")
                    preview_lines.append("```")
                    if preview_desc:
                        preview_lines.append("")
                        preview_lines.append("Description:")
                        preview_lines.append("```")
                        preview_lines.append(preview_desc)
                        preview_lines.append("```")

                    await __event_emitter__(
                        {
                            "type": "message",
                            "data": {
                                "id": f"ocr-preview-{int(time.time() * 1000)}",
                                "role": "assistant",
                                "content": "\n".join(preview_lines),
                                "mime_type": "text/markdown",
                                "persist": True,
                                "replace": False,
                            },
                        }
                    )

                await self._emit_status_once(
                    "OCR complete.", True, __event_emitter__, hidden=False
                )
            except Exception as e:
                # Fallback to empty results if OCR step fails
                ocr_text, ocr_desc, ocr_category = "", "", ""
                await self._emit_status_once(
                    f"OCR failed: {e}", True, __event_emitter__, hidden=False
                )
        else:
            # Intentionally do not emit a "No images detected" status to avoid overriding prior OCR status in the UI.
            pass

        # Helper added: normalize image artifacts into content parts for per-image OCR
        # Note: defined here for minimal diff safety; could be hoisted as a method if preferred.
        def _normalize_to_image_content_parts_inline(
            last_user_images: List[str],
            last_user_files: List[Dict[str, Any]],
            content_image_parts: List[Dict[str, Any]],
        ) -> List[Dict[str, Any]]:
            parts: List[Dict[str, Any]] = []
            # Existing content parts that already look like images
            for p in content_image_parts or []:
                if isinstance(p, dict):
                    ptype = str(p.get("type", "")).lower()
                    if ptype in ("image_url", "input_image", "image"):
                        if ptype == "image" and isinstance(p.get("url"), str):
                            parts.append(
                                {"type": "image_url", "image_url": {"url": p["url"]}}
                            )
                        else:
                            parts.append(p)
                    elif "image_url" in p or "file_url" in p or "url" in p:
                        # fallback: treat as image-ish content
                        url = None
                        if isinstance(p.get("image_url"), dict):
                            url = p["image_url"].get("url")
                        url = url or p.get("file_url") or p.get("url")
                        if isinstance(url, str) and url:
                            parts.append(
                                {"type": "image_url", "image_url": {"url": url}}
                            )

            # URLs from images array
            for url in last_user_images or []:
                if isinstance(url, str) and url:
                    parts.append({"type": "image_url", "image_url": {"url": url}})

            # Files with resolvable URL/path
            for f in last_user_files or []:
                if isinstance(f, dict):
                    url = f.get("url") or f.get("path") or f.get("file_url")
                    if isinstance(url, str) and url:
                        parts.append({"type": "image_url", "image_url": {"url": url}})

            # Deduplicate by URL
            seen = set()
            dedup: List[Dict[str, Any]] = []
            for p in parts:
                url = None
                iu = p.get("image_url")
                if isinstance(iu, dict):
                    url = iu.get("url")
                if isinstance(url, str) and url:
                    if url in seen:
                        continue
                    seen.add(url)
                dedup.append(p)
            return dedup

        # If we detected images, but previous block didn't emit, ensure OCR vars exist
        if has_imgs and not (ocr_text or ocr_desc or ocr_category):
            try:
                image_parts_inline = _normalize_to_image_content_parts_inline(
                    last_user_images, last_user_files, content_image_parts
                )
                if image_parts_inline:
                    per_texts: List[str] = []
                    per_descs: List[str] = []
                    per_cats: List[str] = []
                    for img_part in image_parts_inline:
                        single_messages = [
                            {
                                "role": "system",
                                "content": "You are an OCR and image-understanding assistant. Extract all visible text verbatim from the provided image.\n- Preserve natural reading order, line breaks and headings.\n- Do not translate; keep original language.\n- Additionally, when it is relevant to understanding user intent, include a detailed but concise description of the image.\n- Always format your response using this schema:\nTEXT:\n<transcribed text>\n\n---\nDESCRIPTION:\n<description or 'N/A'>\n\n---\nCATEGORY: screenshot|document|diagram|math|slide|whiteboard|handwritten_note|photo|other",
                            },
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": "Transcribe the attached image per schema.",
                                    },
                                    img_part,
                                ],
                            },
                        ]
                        single_ocr_body = {
                            "model": self.valves.OCR_MODEL_ID,
                            "stream": False,
                            "messages": single_messages,
                        }
                        ocr_resp = await generate_chat_completion(
                            __request__, single_ocr_body, user, bypass_filter=True
                        )
                        ocr_raw = self._extract_text_from_response(ocr_resp)
                        t, d, c = self._parse_ocr_structured_output(ocr_raw)
                        per_texts.append(t)
                        per_descs.append(d)
                        per_cats.append(c)
                    ocr_text = "\n\n---\n\n".join([t for t in per_texts if t]) or ""
                    ocr_desc = "\n\n---\n\n".join([d for d in per_descs if d]) or ""
                    uniq_cats = [c for c in dict.fromkeys([c for c in per_cats if c])]
                    ocr_category = ", ".join(uniq_cats)
            except Exception:
                pass

        # Prepare the final body for MAIN_MODEL_ID
        final_body = deepcopy(body)
        final_body["model"] = self.valves.MAIN_MODEL_ID
        # Ensure main call streams by default unless explicitly disabled
        final_body["stream"] = body.get("stream", True)

        # Sanitize messages for MAIN_MODEL_ID (e.g., strip images if the model is not vision capable)
        final_body["messages"] = self._sanitize_messages_for_main(
            final_body.get("messages", [])
        )

        # Incremental OCR merge: include any new images across the conversation since the last assistant turn
        try:
            # Find index of last assistant message; everything after it is "new"
            msgs = body.get("messages", []) or []
            last_assistant_idx = -1
            for i in range(len(msgs) - 1, -1, -1):
                if msgs[i].get("role") == "assistant":
                    last_assistant_idx = i
                    break

            # Collect image artifacts from all user messages after last assistant
            new_urls: List[str] = []
            new_files: List[Dict[str, Any]] = []
            new_parts: List[Dict[str, Any]] = []
            span = msgs[last_assistant_idx + 1 :] if last_assistant_idx >= 0 else msgs
            for m in span:
                if m.get("role") != "user":
                    continue
                imgs = m.get("images")
                if isinstance(imgs, list):
                    for u in imgs:
                        if isinstance(u, str) and u:
                            new_urls.append(u)
                        elif isinstance(u, dict):
                            url = (
                                u.get("url")
                                or u.get("src")
                                or u.get("image_url")
                                or u.get("file_url")
                            )
                            if isinstance(url, dict):
                                nested = url.get("url") or url.get("file_url")
                                if isinstance(nested, str) and nested:
                                    new_urls.append(nested)
                            elif isinstance(url, str) and url:
                                new_urls.append(url)
                files = m.get("files")
                if isinstance(files, list):
                    for f in files:
                        if isinstance(f, dict):
                            ftype = (f.get("type") or f.get("mimetype") or "").lower()
                            url = f.get("url") or f.get("path") or f.get("file_url")
                            if (
                                isinstance(ftype, str) and ftype.startswith("image")
                            ) or (isinstance(url, str) and url):
                                new_files.append(f)
                                if isinstance(url, str) and url:
                                    new_urls.append(url)
                content = m.get("content")
                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict):
                            ptype = str(part.get("type", "")).lower()
                            if (
                                ptype in ("image_url", "input_image", "image")
                                or "image_url" in part
                                or "file_url" in part
                                or "url" in part
                            ):
                                new_parts.append(part)

            # Normalize and dedupe these "new" images
            def _norm_many(
                urls: List[str],
                files: List[Dict[str, Any]],
                parts: List[Dict[str, Any]],
            ) -> List[Dict[str, Any]]:
                out: List[Dict[str, Any]] = []
                for p in parts or []:
                    if isinstance(p, dict):
                        ptype = str(p.get("type", "")).lower()
                        if ptype in ("image_url", "input_image", "image"):
                            if ptype == "image" and isinstance(p.get("url"), str):
                                out.append(
                                    {
                                        "type": "image_url",
                                        "image_url": {"url": p["url"]},
                                    }
                                )
                            else:
                                out.append(p)
                        elif "image_url" in p or "file_url" in p or "url" in p:
                            url = None
                            if isinstance(p.get("image_url"), dict):
                                url = p["image_url"].get("url")
                            url = url or p.get("file_url") or p.get("url")
                            if isinstance(url, str) and url:
                                out.append(
                                    {"type": "image_url", "image_url": {"url": url}}
                                )
                for u in urls or []:
                    if isinstance(u, str) and u:
                        out.append({"type": "image_url", "image_url": {"url": u}})
                for f in files or []:
                    if isinstance(f, dict):
                        u = f.get("url") or f.get("path") or f.get("file_url")
                        if isinstance(u, str) and u:
                            out.append({"type": "image_url", "image_url": {"url": u}})
                # Deduplicate by URL
                seen = set()
                dedup: List[Dict[str, Any]] = []
                for p in out:
                    url = None
                    iu = p.get("image_url")
                    if isinstance(iu, dict):
                        url = iu.get("url")
                    if isinstance(url, str) and url:
                        if url in seen:
                            continue
                        seen.add(url)
                    dedup.append(p)
                return dedup

            new_image_parts_all = _norm_many(new_urls, new_files, new_parts)

            # If we have new images since last assistant, OCR them and merge
            if new_image_parts_all:
                per_texts: List[str] = []
                per_descs: List[str] = []
                per_cats: List[str] = []
                for img_part in new_image_parts_all:
                    single_messages = [
                        {
                            "role": "system",
                            "content": "You are an OCR and image-understanding assistant. Extract all visible text verbatim from the provided image.\n- Preserve natural reading order, line breaks and headings.\n- Do not translate; keep original language.\n- Additionally, when it is relevant to understanding user intent, include a detailed but concise description of the image.\n- Always format your response using this schema:\nTEXT:\n<transcribed text>\n\n---\nDESCRIPTION:\n<description or 'N/A'>\n\n---\nCATEGORY: screenshot|document|diagram|math|slide|whiteboard|handwritten_note|photo|other",
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Transcribe the attached image per schema.",
                                },
                                img_part,
                            ],
                        },
                    ]
                    single_ocr_body = {
                        "model": self.valves.OCR_MODEL_ID,
                        "stream": False,
                        "messages": single_messages,
                    }
                    ocr_resp = await generate_chat_completion(
                        __request__, single_ocr_body, user, bypass_filter=True
                    )
                    ocr_raw = self._extract_text_from_response(ocr_resp)
                    t, d, c = self._parse_ocr_structured_output(ocr_raw)
                    if t:
                        per_texts.append(t)
                    if d:
                        per_descs.append(d)
                    if c:
                        per_cats.append(c)

                add_text = "\n\n---\n\n".join(per_texts) if per_texts else ""
                add_desc = "\n\n---\n\n".join(per_descs) if per_descs else ""
                if add_text:
                    if ocr_text:
                        ocr_text = ocr_text + "\n\n---\n\n" + add_text
                    else:
                        ocr_text = add_text
                if add_desc:
                    if ocr_desc:
                        ocr_desc = ocr_desc + "\n\n---\n\n" + add_desc
                    else:
                        ocr_desc = add_desc
                if per_cats:
                    uniq = [
                        c
                        for c in dict.fromkeys(
                            ([ocr_category] if ocr_category else []) + per_cats
                        )
                        if c
                    ]
                    ocr_category = ", ".join(uniq)
        except Exception:
            # Non-fatal: continue without incremental OCR merge
            pass

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
            if ocr_desc:
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
        # Emit a single "composing" status before the provider call
        await self._emit_status_once(
            f"Composing response using {self.valves.MAIN_MODEL_ID}...",
            False,
            __event_emitter__,
            hidden=False,
        )

        resp = await generate_chat_completion(__request__, final_body, user)

        # After the final response has finished (streaming or not), send a 'clear' instruction
        # so the UI hides/removes all prior status/preview emitters.
        try:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "done",
                            "done": True,
                            "hidden": True,
                            "clear": True,
                        },
                    }
                )
        except Exception:
            pass

        return resp

    # Helper: status dedupe + safe emitter
    async def _emit_status_once(
        self,
        description: str,
        done: bool,
        __event_emitter__: Optional[Callable[[Any], Awaitable[None]]] = None,
        hidden: bool = False,
    ) -> None:
        if not __event_emitter__:
            return
        try:
            # Strong de-duplication: suppress re-emitting the same final-completion marker entirely.
            completion_keys = {"Final answer complete.", "Answer composition finished."}
            if description in completion_keys:
                if getattr(self, "_completion_emitted", False):
                    return
                # mark as emitted
                self._completion_emitted = True

            now = time.time()
            # Lightweight dedupe for other statuses
            ttl = 3.0
            # Use a composite key that includes the 'done' flag to avoid re-sending a finished status
            key = f"{description}|{int(done)}"
            last = self._status_last_emit.get(key, 0.0)
            if ttl > 0 and (now - last) < ttl:
                return

            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": description,
                        "done": done,
                        "hidden": hidden,
                    },
                }
            )
            self._status_last_emit[key] = now
        except Exception:
            # Do not let status errors break the main flow
            pass

    # Helper: wrap provider stream so we can emit a completion status exactly once
    def _wrap_stream(
        self,
        stream_obj: Any,
        on_done: Callable[[], Coroutine[Any, Any, None]],
    ):
        # Reset completion flag for each new completion sequence
        self._completion_emitted = False
        # Reset flags for each new stream/completion sequence
        self._completion_emitted = False
        # Async stream
        if hasattr(stream_obj, "__aiter__"):

            async def agen():
                try:
                    async for chunk in stream_obj:
                        yield chunk
                finally:
                    try:
                        await on_done()
                    except Exception:
                        pass

            return agen()

        # Sync iterator
        if hasattr(stream_obj, "__iter__"):
            self._completion_emitted = False
            self._completion_emitted = False

            def gen():
                try:
                    for chunk in stream_obj:
                        yield chunk
                finally:
                    try:
                        loop = asyncio.get_event_loop()
                        coro = on_done()
                        if loop.is_running():
                            loop.create_task(coro)
                        else:
                            asyncio.run(coro)
                    except Exception:
                        pass

            return gen()

        # Unknown type: best-effort fire-and-forget completion
        try:
            loop = asyncio.get_event_loop()
            coro = on_done()
            if loop.is_running():
                loop.create_task(coro)
            else:
                asyncio.run(coro)
        except Exception:
            pass
        finally:
            # ensure flags reset even on unknown stream types
            self._composing_active = False
        return stream_obj

    def _extract_image_artifacts(
        self, body: Dict[str, Any]
    ) -> Tuple[bool, List[str], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Detect images from recent user messages and from top-level attachments.
        - Scans the last few user messages (up to 5) to capture multi-message image uploads.
        - Supports a variety of shapes: message['images'] (strings or dicts), message['files'],
          and message['content'] parts (image_url/input_image/image).
        - Deduplicates results and returns (has_any, image_urls, file_dicts, content_parts).
        """
        messages = body.get("messages", []) or []

        # Collect from the last N user messages (to support multi-message image uploads)
        last_user_msgs: List[Dict[str, Any]] = []
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msgs.append(msg)
                if len(last_user_msgs) >= 5:
                    break

        last_user_images: List[str] = []
        last_user_files: List[Dict[str, Any]] = []
        content_image_parts: List[Dict[str, Any]] = []

        def collect_from_message(msg: Dict[str, Any]):
            nonlocal last_user_images, last_user_files, content_image_parts
            # message['images'] can be a list of strings or dicts
            imgs = msg.get("images")
            if isinstance(imgs, list):
                for u in imgs:
                    if isinstance(u, str) and u:
                        last_user_images.append(u)
                    elif isinstance(u, dict):
                        # common keys that may hold a URL
                        url = (
                            u.get("url")
                            or u.get("src")
                            or u.get("image_url")
                            or u.get("file_url")
                        )
                        if isinstance(url, dict):
                            # nested: {"image_url": {"url": "..."}}
                            nested = url.get("url") or url.get("file_url")
                            if isinstance(nested, str) and nested:
                                last_user_images.append(nested)
                        elif isinstance(url, str) and url:
                            last_user_images.append(url)

            # message['files'] may contain image file dicts
            files = msg.get("files")
            if isinstance(files, list):
                for f in files:
                    if not isinstance(f, dict):
                        continue
                    ftype = (f.get("type") or f.get("mimetype") or "").lower()
                    url = f.get("url") or f.get("path") or f.get("file_url")
                    if isinstance(ftype, str) and ftype.startswith("image"):
                        last_user_files.append(f)
                    elif isinstance(url, str) and re.search(
                        r"\.(jpe?g|png|gif|bmp|webp|tiff)$", url, re.IGNORECASE
                    ):
                        last_user_files.append(f)

            # OpenAI-style content parts
            content = msg.get("content")
            if isinstance(content, list):
                for part in content:
                    if not isinstance(part, dict):
                        continue
                    ptype = str(part.get("type", "")).lower()
                    if ptype in ("image_url", "input_image", "image"):
                        content_image_parts.append(part)
                    elif "image_url" in part or "file_url" in part or "url" in part:
                        # fallback: include parts that look like images
                        content_image_parts.append(part)

        # Collect from the most recent user messages
        for m in last_user_msgs:
            collect_from_message(m)

        # Also consider top-level attachments (some UIs pass these outside messages)
        top_images = body.get("images")
        if isinstance(top_images, list):
            for u in top_images:
                if isinstance(u, str) and u:
                    last_user_images.append(u)
                elif isinstance(u, dict):
                    url = (
                        u.get("url")
                        or u.get("src")
                        or u.get("image_url")
                        or u.get("file_url")
                    )
                    if isinstance(url, dict):
                        nested = url.get("url") or url.get("file_url")
                        if isinstance(nested, str) and nested:
                            last_user_images.append(nested)
                    elif isinstance(url, str) and url:
                        last_user_images.append(url)

        top_files = body.get("files")
        if isinstance(top_files, list):
            for f in top_files:
                if not isinstance(f, dict):
                    continue
                ftype = (f.get("type") or f.get("mimetype") or "").lower()
                url = f.get("url") or f.get("path") or f.get("file_url")
                if isinstance(ftype, str) and ftype.startswith("image"):
                    last_user_files.append(f)
                elif isinstance(url, str) and re.search(
                    r"\.(jpe?g|png|gif|bmp|webp|tiff)$", url, re.IGNORECASE
                ):
                    last_user_files.append(f)

        # Deduplicate images (preserve order)
        last_user_images = list(dict.fromkeys(last_user_images))

        def _file_key(f: Dict[str, Any]) -> str:
            return str(f.get("url") or f.get("path") or f.get("name") or id(f))

        seen_files = set()
        dedup_files: List[Dict[str, Any]] = []
        for f in last_user_files:
            k = _file_key(f)
            if k in seen_files:
                continue
            seen_files.add(k)
            dedup_files.append(f)
        last_user_files = dedup_files

        # Deduplicate content parts by normalized URL where possible
        seen_urls = set()
        dedup_parts: List[Dict[str, Any]] = []
        for p in content_image_parts:
            url = None
            iu = p.get("image_url")
            if isinstance(iu, dict):
                url = iu.get("url") or iu.get("file_url")
            elif isinstance(iu, str):
                url = iu
            else:
                url = p.get("url") or p.get("path") or p.get("file_url")
            if isinstance(url, str) and url:
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                dedup_parts.append(p)
            else:
                key = repr(p)
                if key in seen_urls:
                    continue
                seen_urls.add(key)
                dedup_parts.append(p)
        content_image_parts = dedup_parts

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
        Build a robust OCR prompt and normalize all image artifacts into content parts
        for maximum multi-image compatibility across providers.
        """
        messages: List[Dict[str, Any]] = []
        sys_content = (
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
        messages.append({"role": "system", "content": sys_content})

        # Normalize into a single content list
        content_parts: List[Dict[str, Any]] = [
            {
                "type": "text",
                "text": "Transcribe all text from the attached image(s). If requested, also provide a description and a category following the schema.",
            }
        ]

        # Preserve any existing content image parts from the last user message
        if content_image_parts:
            content_parts.extend(content_image_parts)

        # Collect image URLs from various sources to maximize provider compatibility
        image_urls: List[str] = []

        # Add image URLs found in the 'images' array
        for url in last_user_images or []:
            if isinstance(url, str) and url:
                image_urls.append(url)

        # Add image files that expose a resolvable URL/path
        for f in last_user_files or []:
            if isinstance(f, dict):
                url = f.get("url") or f.get("path") or f.get("file_url")
                if isinstance(url, str) and url:
                    image_urls.append(url)

        # Also extract URLs from any existing content image parts
        for part in content_image_parts or []:
            if isinstance(part, dict) and part.get("type") in ("image_url", "image"):
                iu = part.get("image_url") or {}
                url = iu.get("url") if isinstance(iu, dict) else None
                if isinstance(url, str) and url:
                    image_urls.append(url)

        # Deduplicate while preserving order
        image_urls = list(dict.fromkeys(image_urls))

        user_msg: Dict[str, Any] = {"role": "user", "content": content_parts}
        if image_urls:
            user_msg["images"] = image_urls
        if last_user_files:
            user_msg["files"] = list(last_user_files)

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

    def _parse_ocr_structured_output(self, text: str) -> Tuple[str, str, str]:
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
