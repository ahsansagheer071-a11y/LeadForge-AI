import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from app.services.website_generator.parsers.schemas import (
    GeneratedAsset,
    ProjectMetadata,
    ProjectStatistics,
)
from app.services.website_generator.providers.schemas import AIResponse
from app.services.website_generator.schemas import GeneratedFile, WebsiteProject

logger = logging.getLogger(__name__)

_FILE_PATH_PATTERN = re.compile(
    r"(?:[-*]\s+)?"
    r"(?:`|(?:\*\*))?"
    r"((?:src/)?"
    r"(?:app|pages|components|sections|utils|lib|hooks|styles|types|config)"
    r"(?:/[a-zA-Z0-9_\-]+)*\.[a-zA-Z0-9]+)"
    r"(?:`|(?:\*\*))?"
    r"(?:\s*-{1,2}\s*.*)?"
)
_IMAGE_PATTERN = re.compile(
    r"(?:`)?"
    r"((?:[a-zA-Z0-9_\-]+/"
    r")*[a-zA-Z0-9_\-]+\.(?:png|jpg|jpeg|gif|svg|webp|ico))"
    r"(?:`)?"
)
_HEADING_PATTERN = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_PROJECT_NAME_PATTERN = re.compile(
    r'project[_\s]name[:\s]+["\']?([a-zA-Z0-9_\- ]+)["\']?',
    re.IGNORECASE,
)


class ResponseParser:
    def parse(self, ai_response: AIResponse) -> WebsiteProject:
        logger.info("ResponseParser: Starting parse...")

        if not ai_response.success:
            raise ValueError(
                f"Cannot parse unsuccessful AI response: {ai_response.errors}"
            )

        raw = ai_response.raw_response
        if not raw:
            raise ValueError("AI response is empty")

        logger.info(
            "Validation complete: raw_response length = %d chars",
            len(raw),
        )

        project_name = self._extract_project_name(ai_response)
        framework = self._extract_framework(ai_response)
        generation_id = uuid.uuid4().hex[:12]

        files = self._extract_files(ai_response)
        assets = self._extract_assets(ai_response)

        meta = ProjectMetadata(
            provider=ai_response.provider,
            model=ai_response.model,
            generation_time=ai_response.latency,
            framework_version=self._infer_framework_version(framework),
            prompt_tokens=ai_response.usage.prompt_tokens
            if ai_response.usage
            else None,
            completion_tokens=ai_response.usage.completion_tokens
            if ai_response.usage
            else None,
            total_tokens=ai_response.usage.total_tokens
            if ai_response.usage
            else None,
        )

        stats = self._calculate_statistics(files, assets)

        logger.info(
            "Project: %s, Framework: %s, ID: %s",
            project_name,
            framework,
            generation_id,
        )
        logger.info(
            "Extracted %d files, %d assets",
            len(files),
            len(assets),
        )
        logger.info(
            "Statistics: %d files, %d assets, %d bytes",
            stats.total_files,
            stats.total_assets,
            stats.estimated_size_bytes,
        )

        website_project = WebsiteProject(
            project_name=project_name,
            framework=framework,
            generation_id=generation_id,
            version="1.0.0",
            generated_at=datetime.now(timezone.utc),
            files=files,
            assets=[json.dumps(a.model_dump(mode="json")) for a in assets],
            metadata=meta.model_dump(),
            statistics=stats.model_dump(),
        )

        logger.info("ResponseParser: WebsiteProject created successfully")
        return website_project

    @staticmethod
    def _extract_project_name(ai_response: AIResponse) -> str:
        raw = ai_response.raw_response
        match = _PROJECT_NAME_PATTERN.search(raw)
        if match:
            return match.group(1).strip()
        match = _HEADING_PATTERN.search(raw)
        if match:
            name = match.group(1).strip().lower().replace(" ", "_")
            return name
        return "leadforge_ai_website"

    @staticmethod
    def _extract_framework(ai_response: AIResponse) -> str:
        raw = ai_response.raw_response.lower()
        if re.search(r"\bnext[.\s]?js\b", raw):
            return "nextjs"
        if re.search(r"\breact\b", raw):
            return "react"
        if re.search(r"\bvue\b", raw):
            return "vue"
        if re.search(r"\bangular\b", raw):
            return "angular"
        if re.search(r"\bsvelte\b", raw):
            return "svelte"
        return "nextjs"

    @staticmethod
    def _extract_files(ai_response: AIResponse) -> List[GeneratedFile]:
        raw = ai_response.raw_response
        seen = set()
        files: List[GeneratedFile] = []
        for match in _FILE_PATH_PATTERN.finditer(raw):
            path = match.group(1)
            # Strip src/ prefix if present
            if path.startswith("src/"):
                path = path[4:]
            if path in seen:
                continue
            seen.add(path)
            ext = path.split(".")[-1] if "." in path else ""
            file_type = ResponseParser._infer_file_type(path, ext)
            files.append(
                GeneratedFile(
                    path=path,
                    content="# placeholder — real content generated in Phase 5.5",
                    type=file_type,
                    size=0,
                )
            )
        # If no files found, generate minimal fallback
        if not files:
            logger.warning("No files extracted from AI response, generating fallback")
            fallback_files = [
                ("app/layout.tsx", "layout"),
                ("app/page.tsx", "page"),
                ("styles/globals.css", "stylesheet"),
                ("lib/utils.ts", "script"),
                ("tailwind.config.ts", "configuration"),
                ("package.json", "configuration"),
                ("tsconfig.json", "configuration"),
                ("next.config.js", "configuration"),
                ("postcss.config.js", "configuration"),
            ]
            for fb_path, fb_type in fallback_files:
                files.append(
                    GeneratedFile(
                        path=fb_path,
                        content="# placeholder — fallback content",
                        type=fb_type,
                        size=0,
                    )
                )
        return files

    @staticmethod
    def _extract_assets(ai_response: AIResponse) -> List[GeneratedAsset]:
        raw = ai_response.raw_response
        seen = set()
        assets: List[GeneratedAsset] = []
        for match in _IMAGE_PATTERN.finditer(raw):
            ref = match.group(1)
            if ref in seen:
                continue
            seen.add(ref)
            ext = ref.split(".")[-1].lower()
            asset_type_map = {
                "png": "image",
                "jpg": "image",
                "jpeg": "image",
                "gif": "image",
                "svg": "image",
                "webp": "image",
                "ico": "image",
            }
            assets.append(
                GeneratedAsset(
                    filename=ref.split("/")[-1],
                    asset_type=asset_type_map.get(ext, "image"),
                    reference=ref,
                    metadata={"extension": ext},
                )
            )
        return assets

    @staticmethod
    def _calculate_statistics(
        files: List[GeneratedFile],
        assets: List[GeneratedAsset],
    ) -> ProjectStatistics:
        total_size = sum(f.size for f in files)
        total_lines = None
        if files:
            total_lines = sum(
                len(f.content.splitlines()) for f in files if f.content
            )
        components_count = sum(
            1 for f in files if "component" in f.type.lower()
        )
        pages_count = sum(
            1 for f in files if "page" in f.path.lower()
        )
        return ProjectStatistics(
            total_files=len(files),
            total_assets=len(assets),
            estimated_size_bytes=total_size,
            total_lines=total_lines,
            components_count=components_count or None,
            pages_count=pages_count or None,
        )

    @staticmethod
    def _infer_file_type(path: str, extension: str) -> str:
        ext = extension.lower()
        path_lower = path.lower()
        if "component" in path_lower or ext in ("tsx", "jsx"):
            return "react_component"
        if "page" in path_lower or path_lower.startswith("pages/"):
            return "page"
        if ext in ("css", "scss", "less", "sass"):
            return "stylesheet"
        if ext in ("ts", "js", "mjs"):
            if "config" in path_lower:
                return "configuration"
            if "util" in path_lower or "lib" in path_lower or "hook" in path_lower:
                return "script"
            return "script"
        if ext in ("json", "toml", "yaml", "yml"):
            return "configuration"
        if ext in ("md", "mdx"):
            return "documentation"
        return "unknown"

    @staticmethod
    def _infer_framework_version(framework: str) -> Optional[str]:
        versions = {
            "nextjs": "14.0.0",
            "react": "18.2.0",
            "vue": "3.3.0",
            "angular": "17.0.0",
            "svelte": "4.2.0",
        }
        return versions.get(framework)
