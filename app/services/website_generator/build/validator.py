import logging
import os
from typing import List, Set

from app.services.website_generator.build.schemas import ValidationReport
from app.services.website_generator.schemas import GeneratedFile, WebsiteProject

logger = logging.getLogger(__name__)

_REQUIRED_FILES: Set[str] = {
    "package.json",
    "tsconfig.json",
    "app/layout.tsx",
    "app/page.tsx",
}
_REQUIRED_DIRS: Set[str] = {"app"}

_REQUIRED_EXTENSIONS: Set[str] = {
    ".tsx", ".ts", ".js", ".jsx", ".css", ".json", ".mjs", ".cjs",
}

_NEXT_CONFIG_NAMES: Set[str] = {
    "next.config.js", "next.config.mjs", "next.config.ts",
}


class ProjectValidator:
    def validate(self, project: WebsiteProject) -> ValidationReport:
        logger.info("ProjectValidator: Validating project...")

        report = ValidationReport(
            total_files_validated=len(project.files),
        )

        if not project.files:
            report.folder_errors.append("Project has no files")
            logger.error("ProjectValidator: Project has no files")
            return report

        file_paths = {f.path.replace("\\", "/") for f in project.files}
        missing = self._check_required_files(file_paths)
        report.missing_files = missing

        invalid = self._check_file_contents(project.files)
        report.invalid_files = invalid

        folder_errors = self._check_folder_structure(file_paths)
        report.folder_errors = folder_errors

        warnings = self._check_warnings(project, file_paths)
        report.warnings = warnings

        report.valid = (
            len(missing) == 0
            and len(invalid) == 0
            and len(folder_errors) == 0
        )

        if report.valid:
            logger.info(
                "ProjectValidator: %d files validated successfully",
                len(project.files),
            )
        else:
            if missing:
                logger.error("ProjectValidator: Missing files: %s", missing)
            if invalid:
                logger.error("ProjectValidator: Invalid files: %s", invalid)
            if folder_errors:
                logger.error("ProjectValidator: Folder errors: %s", folder_errors)

        return report

    @staticmethod
    def _check_required_files(file_paths: Set[str]) -> List[str]:
        missing: List[str] = []
        for req in _REQUIRED_FILES:
            if req not in file_paths:
                missing.append(req)

        has_next_config = bool(file_paths & _NEXT_CONFIG_NAMES)
        if not has_next_config:
            missing.append("next.config.* (js/mjs/ts)")

        return missing

    @staticmethod
    def _check_file_contents(files: List[GeneratedFile]) -> List[str]:
        invalid: List[str] = []
        for f in files:
            if not f.content.strip():
                ext = os.path.splitext(f.path)[1].lower()
                if ext in _REQUIRED_EXTENSIONS:
                    invalid.append(f.path)
        return invalid

    @staticmethod
    def _check_folder_structure(file_paths: Set[str]) -> List[str]:
        errors: List[str] = []
        for req_dir in _REQUIRED_DIRS:
            has_file_in_dir = any(
                p.startswith(req_dir + "/") for p in file_paths
            )
            if not has_file_in_dir:
                errors.append(f"Missing directory: {req_dir}/")
        return errors

    @staticmethod
    def _check_warnings(
        project: WebsiteProject, file_paths: Set[str]
    ) -> List[str]:
        warnings: List[str] = []
        if not project.framework:
            warnings.append("No framework specified in project")
        has_public_assets = any(
            p.startswith("public/") for p in file_paths
        )
        if not has_public_assets:
            warnings.append("No files in public/ directory")
        has_components = any(
            p.startswith("components/") for p in file_paths
        )
        if not has_components:
            warnings.append("No files in components/ directory")
        return warnings
