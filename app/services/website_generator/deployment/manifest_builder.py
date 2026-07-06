import hashlib
import json
import logging
from typing import List, Optional, Tuple

from app.services.website_generator.schemas import WebsiteProject
from app.services.website_generator.build.schemas import BuildResult
from app.services.website_generator.preview.schemas import (
    PreviewResult,
)
from app.services.website_generator.deployment.schemas import (
    DeploymentArtifact,
    DeploymentManifest,
)

logger = logging.getLogger(__name__)


class ManifestBuilder:
    def build_manifest(
        self,
        project: WebsiteProject,
        build_result: BuildResult,
        preview_result: PreviewResult,
        artifacts: List[DeploymentArtifact],
    ) -> DeploymentManifest:
        framework = project.framework or "unknown"
        version = self._get_framework_version(project)
        provider, model = self._get_provider_model(project)

        build_status = "success" if build_result.build_success else "failed"
        preview_status = preview_result.status

        total_files = sum(
            1 for a in artifacts if a.type in ("file",)
        )
        total_assets = sum(
            1 for a in artifacts if a.type in ("asset", "image")
        )
        total_size = sum(a.size for a in artifacts)

        checksum = self._calculate_checksum(artifacts)

        manifest = DeploymentManifest(
            framework=framework,
            version=version,
            generated_at=project.generated_at,
            provider=provider,
            model=model,
            build_status=build_status,
            preview_status=preview_status,
            total_files=total_files,
            total_assets=total_assets,
            total_size=total_size,
            generation_id=project.generation_id,
            build_id=build_result.build_id,
            checksum=checksum,
        )

        logger.info(
            "Manifest: framework=%s version=%s files=%d assets=%d size=%d",
            framework,
            version,
            total_files,
            total_assets,
            total_size,
        )
        return manifest

    def verify_artifacts(
        self, artifacts: List[DeploymentArtifact]
    ) -> bool:
        if not artifacts:
            logger.warning("verify_artifacts: no artifacts to verify")
            return False

        missing_content = 0
        zero_size = 0

        for art in artifacts:
            if art.type == "file" and not art.content:
                missing_content += 1
            if art.size <= 0:
                zero_size += 1

        if missing_content == len(artifacts):
            logger.warning(
                "verify_artifacts: all %d artifacts missing content",
                missing_content,
            )
            return False

        return True

    @staticmethod
    def _calculate_checksum(
        artifacts: List[DeploymentArtifact],
    ) -> Optional[str]:
        hasher = hashlib.sha256()
        contents = []

        for art in sorted(artifacts, key=lambda a: a.path):
            if art.content:
                contents.append(art.content)

        if not contents:
            return None

        for c in contents:
            hasher.update(c.encode("utf-8"))

        digest = hasher.hexdigest()
        return f"sha256:{digest}"

    @staticmethod
    def _get_framework_version(
        project: WebsiteProject,
    ) -> str:
        meta = project.metadata or {}
        pmeta = meta.get("project_metadata", {})
        if isinstance(pmeta, dict):
            fv = pmeta.get("framework_version")
            if fv:
                return str(fv)
        return project.version or "1.0.0"

    @staticmethod
    def _get_provider_model(
        project: WebsiteProject,
    ) -> Tuple[str, str]:
        meta = project.metadata or {}
        pmeta = meta.get("project_metadata", {})
        if isinstance(pmeta, dict):
            provider = pmeta.get("provider", "")
            model = pmeta.get("model", "")
            if provider:
                return provider, model
        return "", ""
