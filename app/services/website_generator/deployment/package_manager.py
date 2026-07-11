import json
import logging
import os
from typing import Any, Dict, List

from app.services.website_generator.build.schemas import BuildResult
from app.services.website_generator.deployment.manifest_builder import (
    ManifestBuilder,
)
from app.services.website_generator.deployment.schemas import (
    DeploymentArtifact,
    DeploymentManifest,
    DeploymentPackage,
)
from app.services.website_generator.parsers.schemas import (
    GeneratedAsset,
)
from app.services.website_generator.preview.schemas import (
    PreviewResult,
)
from app.services.website_generator.schemas import WebsiteProject

logger = logging.getLogger(__name__)


class PackageManager:
    def __init__(self) -> None:
        self._manifest_builder = ManifestBuilder()

    def create_package(
        self,
        project: WebsiteProject,
        build_result: BuildResult,
        preview_result: PreviewResult,
    ) -> DeploymentPackage:
        logger.info(
            "PackageManager: Creating package for project '%s'",
            project.project_name,
        )

        package_id = self._generate_package_id()

        errors: List[str] = []
        warnings: List[str] = []

        artifacts = self._collect_artifacts(
            project, build_result, warnings
        )

        total_size = self._calculate_package_size(artifacts)

        manifest_valid = True
        try:
            manifest = self._manifest_builder.build_manifest(
                project, build_result, preview_result, artifacts
            )
            manifest_valid = self._manifest_builder.verify_artifacts(
                artifacts
            )
            if not manifest_valid:
                warnings.append(
                    "Some artifacts missing content or empty"
                )
        except Exception as e:
            errors.append(f"Manifest build failed: {e}")
            manifest = DeploymentManifest()

        serialized_build = self._serialize_build_result(build_result)
        serialized_preview = (
            self._serialize_preview_result(preview_result)
        )

        package = DeploymentPackage(
            package_id=package_id,
            project_name=project.project_name,
            framework=project.framework,
            created_at=manifest.generated_at,
            project_path=build_result.project_path,
            preview_url=preview_result.preview_url,
            build_result=serialized_build,
            manifest=manifest.model_dump(),
            artifacts=[a.model_dump() for a in artifacts],
            metadata={
                "package_size": total_size,
                "artifact_count": len(artifacts),
                "generation_id": project.generation_id,
                "preview_status": preview_result.status,
                "manifest_valid": manifest_valid,
            },
            errors=errors,
            warnings=warnings,
        )

        logger.info(
            "PackageManager: Package %s created (%d artifacts, %d bytes)",
            package_id,
            len(artifacts),
            total_size,
        )
        return package

    def _collect_artifacts(
        self,
        project: WebsiteProject,
        build_result: BuildResult,
        warnings: List[str],
    ) -> List[DeploymentArtifact]:
        artifacts: List[DeploymentArtifact] = []

        for gf in project.files:
            checksum = None
            if gf.content:
                import hashlib

                checksum = (
                    "sha256:"
                    + hashlib.sha256(
                        gf.content.encode("utf-8")
                    ).hexdigest()
                )

            art = DeploymentArtifact(
                name=os.path.basename(gf.path),
                path=gf.path,
                type=gf.type or "file",
                size=gf.size or len((gf.content or "").encode("utf-8")),
                checksum=checksum,
                content=gf.content,
                metadata={
                    "source": "generated_file",
                },
            )
            artifacts.append(art)

        for raw_asset in project.assets:
            try:
                if isinstance(raw_asset, str):
                    asset_dict = json.loads(raw_asset)
                elif isinstance(raw_asset, dict):
                    asset_dict = raw_asset
                else:
                    continue

                name = asset_dict.get("filename") or asset_dict.get("name", "asset")
                path = asset_dict.get("path") or asset_dict.get("reference", name)
                asset_type = asset_dict.get("type") or asset_dict.get("asset_type", "asset")
                content_b64 = asset_dict.get("content_base64") or asset_dict.get("content")
                size = asset_dict.get("size") or asset_dict.get("size_bytes", 0)
                encoding = asset_dict.get("encoding")

                art = DeploymentArtifact(
                    name=name,
                    path=path,
                    type=asset_type,
                    size=size or len(content_b64) if content_b64 else 0,
                    content=content_b64,
                    encoding=encoding or "base64" if content_b64 and asset_type in ("image", "binary") else None,
                    metadata={
                        "source": "generated_asset",
                        **(asset_dict.get("metadata", {})),
                    },
                )
                artifacts.append(art)
            except Exception as e:
                warnings.append(
                    f"Failed to parse asset: {e}"
                )

        if build_result.logs:
            logs_content = "\n".join(build_result.logs)
            art = DeploymentArtifact(
                name="build.log",
                path="logs/build.log",
                type="file",
                size=len(logs_content.encode("utf-8")),
                content=logs_content,
                metadata={"source": "build_logs"},
            )
            artifacts.append(art)

        if build_result.errors:
            errs_content = "\n".join(build_result.errors)
            art = DeploymentArtifact(
                name="errors.log",
                path="logs/errors.log",
                type="file",
                size=len(errs_content.encode("utf-8")),
                content=errs_content,
                metadata={"source": "build_errors"},
            )
            artifacts.append(art)

        return artifacts

    @staticmethod
    def _calculate_package_size(
        artifacts: List[DeploymentArtifact],
    ) -> int:
        return sum(a.size for a in artifacts)

    @staticmethod
    def _generate_package_id() -> str:
        import uuid

        return uuid.uuid4().hex[:12]

    @staticmethod
    def _serialize_build_result(
        build_result: BuildResult,
    ) -> Dict[str, Any]:
        return {
            "success": build_result.success,
            "build_success": build_result.build_success,
            "build_id": build_result.build_id,
            "project_path": build_result.project_path,
            "npm_install_success": build_result.npm_install_success,
            "total_duration": build_result.total_duration,
        }

    @staticmethod
    def _serialize_preview_result(
        preview_result: PreviewResult,
    ) -> Dict[str, Any]:
        return {
            "success": preview_result.success,
            "status": preview_result.status,
            "preview_url": preview_result.preview_url,
            "local_url": preview_result.local_url,
            "server_pid": preview_result.server_pid,
            "health_check": preview_result.health_check,
            "startup_time": preview_result.startup_time,
        }
