import logging
from datetime import datetime
from typing import Optional

from app.services.website_generator.build.schemas import BuildResult
from app.services.website_generator.preview.preview_manager import PreviewManager
from app.services.website_generator.preview.preview_monitor import PreviewMonitor
from app.services.website_generator.preview.schemas import PreviewResult

logger = logging.getLogger(__name__)


class PreviewEngine:
    def __init__(self) -> None:
        self._manager = PreviewManager()
        self._monitor = PreviewMonitor()

    def start_preview(
        self,
        build_result: BuildResult,
        port: int = 3000,
    ) -> PreviewResult:
        logger.info(
            "PreviewEngine: Starting preview for build: %s",
            build_result.build_id,
        )

        result = PreviewResult(port=port)

        if not build_result.build_success:
            msg = "Build not completed — cannot start preview"
            result.errors.append(msg)
            result.status = "error"
            logger.error("PreviewEngine: %s", msg)
            return result

        if not build_result.project_path:
            msg = "No project path in build result"
            result.errors.append(msg)
            result.status = "error"
            logger.error("PreviewEngine: %s", msg)
            return result

        logger.info(
            "PreviewEngine: Build verified (success=True)"
        )
        result.logs.append(
            f"Build verified: {build_result.build_id}"
        )

        logger.info("PreviewEngine: Launching preview server...")
        ok, pid, url_or_error = self._manager.start_server(
            build_result.project_path, port=port
        )

        if not ok or pid is None:
            result.errors.append(url_or_error)
            result.status = "error"
            logger.error(
                "PreviewEngine: Preview failed: %s", url_or_error
            )
            return result

        result.server_pid = pid
        result.local_url = url_or_error
        result.preview_url = url_or_error
        result.logs.append(
            f"Dev server started (PID: {pid})"
        )
        logger.info(
            "PreviewEngine: Preview server running at %s",
            url_or_error,
        )

        healthy, response_time, status_str = self._monitor.wait_for_health(
            url_or_error, timeout=30
        )
        result.health_check = healthy
        result.response_time_ms = round(response_time * 1000, 1)
        result.last_checked = datetime.now()

        if healthy:
            result.success = True
            result.status = "running"
            result.startup_time = response_time
            result.logs.append(
                f"Server healthy (response: {result.response_time_ms}ms)"
            )
            logger.info(
                "PreviewEngine: Server healthy (%.0fms)",
                result.response_time_ms,
            )
        else:
            result.status = "error"
            msg = (
                f"Server not responding after {response_time:.0f}s"
            )
            result.errors.append(msg)
            logger.error("PreviewEngine: %s", msg)

        return result

    def get_preview_status(
        self, preview_result: PreviewResult
    ) -> PreviewResult:
        pid = preview_result.server_pid
        if pid is None:
            preview_result.status = "stopped"
            preview_result.health_check = False
            return preview_result

        if not self._manager.is_running(pid):
            preview_result.status = "stopped"
            preview_result.health_check = False
            crash = self._monitor.detect_crash(pid)
            if crash:
                preview_result.errors.append(
                    f"Server (PID {pid}) has crashed"
                )
            return preview_result

        healthy, elapsed, status = self._monitor.check_health(
            preview_result.local_url
        )
        preview_result.health_check = healthy
        preview_result.response_time_ms = round(elapsed * 1000, 1)
        preview_result.last_checked = datetime.now()
        preview_result.status = "running" if healthy else "degraded"

        return preview_result

    def stop_preview(
        self, preview_result: PreviewResult
    ) -> bool:
        pid = preview_result.server_pid
        if pid is None:
            return False

        ok = self._manager.stop_server(pid)
        if ok:
            preview_result.status = "stopped"
            preview_result.server_pid = None
            preview_result.health_check = False
            preview_result.logs.append("Server stopped")
        return ok

    @property
    def manager(self) -> PreviewManager:
        return self._manager

    @property
    def monitor(self) -> PreviewMonitor:
        return self._monitor
