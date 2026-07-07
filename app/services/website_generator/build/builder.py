import logging
import os
import platform
import shutil
import subprocess
import tempfile
import time
from typing import List, Optional, Tuple

from app.services.website_generator.build.schemas import BuildResult
from app.services.website_generator.build.validator import ProjectValidator
from app.services.website_generator.schemas import GeneratedFile, WebsiteProject

logger = logging.getLogger(__name__)

_INSTALL_TIMEOUT = 120
_BUILD_TIMEOUT = 180


class ProjectBuilder:
    _USE_SHELL = platform.system() == "Windows"

    def __init__(self, validator: ProjectValidator | None = None) -> None:
        self._validator = validator or ProjectValidator()
        self._temp_dir: str | None = None

    def build(self, project: WebsiteProject) -> BuildResult:
        start_time = time.time()
        result = BuildResult()

        validation = self._validator.validate(project)
        if not validation.valid:
            result.errors = (
                validation.missing_files
                + validation.invalid_files
                + validation.folder_errors
            )
            result.logs.append(f"Validation failed: {len(result.errors)} issues")
            logger.error("ProjectBuilder: Validation failed — aborting build")
            return result

        logger.info(
            "ProjectBuilder: Writing %d files...",
            len(project.files),
        )

        try:
            self._temp_dir = self._safe_mkdtemp()
            result.project_path = self._temp_dir
            self._write_project_files(project, self._temp_dir)
            result.logs.append(
                f"Wrote {len(project.files)} files to {self._temp_dir}"
            )
            logger.info(
                "ProjectBuilder: %d files written to %s",
                len(project.files),
                self._temp_dir,
            )
        except OSError as e:
            result.errors.append(f"Failed to write project files: {e}")
            result.total_duration = time.time() - start_time
            return result

        install_ok, install_log, install_err, install_dur = self._run_npm_install(
            self._temp_dir
        )
        result.install_duration = install_dur
        result.logs.append(install_log) if install_log else None
        result.npm_install_success = install_ok
        if install_err:
            result.errors.append(install_err)
        if result.install_duration is not None:
            result.logs.append(
                f"npm install completed in {result.install_duration:.1f}s"
            )

        if not install_ok:
            result.total_duration = time.time() - start_time
            logger.error("ProjectBuilder: npm install failed")
            return result

        build_ok, build_log, build_err, build_dur = self._run_npm_build(self._temp_dir)
        result.build_duration = build_dur
        result.logs.append(build_log) if build_log else None
        result.build_success = build_ok
        if build_err:
            result.errors.append(build_err)
        if result.build_duration is not None:
            result.logs.append(
                f"npm build completed in {result.build_duration:.1f}s"
            )

        if build_ok:
            result.build_path = os.path.join(self._temp_dir, ".next")

        result.success = build_ok
        result.total_duration = time.time() - start_time

        if result.success:
            logger.info(
                "ProjectBuilder: Build completed in %.1fs",
                result.total_duration,
            )
        else:
            logger.error("ProjectBuilder: Build failed")

        return result

    def _safe_mkdtemp(self) -> str:
        """Create a temp dir in a location that doesn't conflict with
        tools that have issues with short DOS-style Windows paths."""
        candidates = []
        if platform.system() == "Windows":
            for base in [os.environ.get("LOCALAPPDATA"), os.environ.get("USERPROFILE"), os.getcwd()]:
                if base and os.path.isdir(base):
                    candidates.append(os.path.join(base, "leadforge_builds"))
        if not candidates:
            candidates.append(os.path.join(tempfile.gettempdir(), "leadforge_builds"))

        for parent in candidates:
            try:
                os.makedirs(parent, exist_ok=True)
                return tempfile.mkdtemp(prefix="leadforge_", dir=parent)
            except OSError:
                continue
        return tempfile.mkdtemp(prefix="leadforge_")

    def _write_project_files(
        self, project: WebsiteProject, temp_dir: str
    ) -> None:
        for file_obj in project.files:
            file_path = file_obj.path.replace("\\", "/")
            abs_path = os.path.join(temp_dir, file_path)
            parent = os.path.dirname(abs_path)
            os.makedirs(parent, exist_ok=True)
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(file_obj.content)

    def _run_npm_install(
        self, project_dir: str
    ) -> Tuple[bool, str, str, Optional[float]]:
        logger.info("ProjectBuilder: Running npm install...")
        start = time.time()
        try:
            proc = subprocess.run(
                "npm install" if self._USE_SHELL else ["npm", "install"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=_INSTALL_TIMEOUT,
                shell=self._USE_SHELL,
            )
            duration = time.time() - start
            stdout = proc.stdout.strip()
            stderr = proc.stderr.strip()
            if proc.returncode == 0:
                logger.info(
                    "npm install completed in %.1fs", duration
                )
                return True, stdout[:500] if stdout else "npm install completed", "", duration
            else:
                err_msg = stderr[:1000] if stderr else f"npm install failed with code {proc.returncode}"
                logger.error("npm install failed: %s", err_msg)
                return False, stdout[:500] if stdout else "", err_msg, duration
        except subprocess.TimeoutExpired:
            duration = time.time() - start
            msg = f"npm install timed out after {_INSTALL_TIMEOUT}s"
            logger.error(msg)
            return False, "", msg, duration
        except FileNotFoundError:
            msg = "npm command not found — is Node.js installed?"
            logger.error(msg)
            return False, "", msg, None

    def _run_npm_build(
        self, project_dir: str
    ) -> Tuple[bool, str, str, Optional[float]]:
        logger.info("ProjectBuilder: Running npm run build...")
        start = time.time()
        try:
            proc = subprocess.run(
                "npm run build" if self._USE_SHELL else ["npm", "run", "build"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=_BUILD_TIMEOUT,
                shell=self._USE_SHELL,
            )
            duration = time.time() - start
            stdout = proc.stdout.strip()
            stderr = proc.stderr.strip()
            if proc.returncode == 0:
                lines = stdout.split("\n")
                summary = [l for l in lines if "✓" in l or "ready" in l.lower() or "compiled" in l.lower()]
                log = "\n".join(summary[-5:]) if summary else f"Build completed in {duration:.1f}s"
                logger.info("npm build completed in %.1fs", duration)
                return True, log[:1000], "", duration
            else:
                err_msg = stderr[:1000] if stderr else f"npm build failed with code {proc.returncode}"
                logger.error("npm build failed: %s", err_msg)
                return False, stdout[:500] if stdout else "", err_msg, duration
        except subprocess.TimeoutExpired:
            duration = time.time() - start
            msg = f"npm build timed out after {_BUILD_TIMEOUT}s"
            logger.error(msg)
            return False, "", msg, duration
        except FileNotFoundError:
            msg = "npm command not found — is Node.js installed?"
            logger.error(msg)
            return False, "", msg, None

    def cleanup(self) -> None:
        if self._temp_dir and os.path.isdir(self._temp_dir):
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            logger.info(
                "ProjectBuilder: Cleaned up temp dir %s", self._temp_dir
            )
            self._temp_dir = None

    def _record_install_duration(self, duration: float) -> None:
        self._install_duration = duration

    def _record_build_duration(self, duration: float) -> None:
        self._build_duration = duration
