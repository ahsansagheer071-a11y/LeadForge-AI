import logging
import os
import signal
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from app.services.website_generator.preview.schemas import InstanceInfo

logger = logging.getLogger(__name__)


class PreviewManager:
    def __init__(self) -> None:
        self._instances: Dict[int, InstanceInfo] = {}

    def start_server(
        self, project_path: str, port: int = 3000
    ) -> Tuple[bool, Optional[int], str]:
        logger.info("PreviewManager: Starting server on port %d...", port)

        if not self._is_port_available(port):
            existing = self._find_instance_by_port(port)
            if existing:
                msg = f"Server already running on port {port} (PID {existing.pid})"
                logger.warning(msg)
                return True, existing.pid, existing.url
            msg = f"Port {port} already in use by another process"
            logger.error(msg)
            return False, None, msg

        if not os.path.isdir(project_path):
            msg = f"Project directory not found: {project_path}"
            logger.error(msg)
            return False, None, msg

        url = f"http://localhost:{port}"

        try:
            proc = subprocess.Popen(
                ["npx", "next", "dev", "-p", str(port)],
                cwd=project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except FileNotFoundError:
            try:
                proc = subprocess.Popen(
                    ["npm", "exec", "next", "dev", "--", "-p", str(port)],
                    cwd=project_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
            except FileNotFoundError:
                msg = "npx/npm not found — is Node.js installed?"
                logger.error(msg)
                return False, None, msg
        except OSError as e:
            msg = f"Failed to start server: {e}"
            logger.error(msg)
            return False, None, msg

        pid = proc.pid
        instance = InstanceInfo(
            pid=pid,
            port=port,
            url=url,
            project_path=project_path,
            started_at=datetime.now(),
        )
        self._instances[pid] = instance

        logger.info("PreviewManager: Server started (PID: %d)", pid)
        return True, pid, url

    def stop_server(self, pid: int) -> bool:
        logger.info("PreviewManager: Stopping server (PID: %d)...", pid)

        if pid not in self._instances:
            logger.warning(
                "PreviewManager: PID %d not found in managed instances", pid
            )
            return False

        try:
            os.kill(pid, signal.SIGTERM)
            deadline = time.time() + 5
            while time.time() < deadline:
                try:
                    os.kill(pid, 0)
                    time.sleep(0.3)
                except ProcessLookupError:
                    break
            else:
                os.kill(pid, signal.SIGKILL)
        except (OSError, ProcessLookupError) as e:
            logger.warning(
                "PreviewManager: Error stopping PID %d: %s", pid, e
            )

        self._instances[pid].status = "stopped"
        del self._instances[pid]
        logger.info("PreviewManager: Server stopped (PID: %d)", pid)
        return True

    def restart_server(
        self, pid: int, project_path: str, port: int = 3000
    ) -> Tuple[bool, Optional[int], str]:
        logger.info(
            "PreviewManager: Restarting server (PID: %d)...", pid
        )
        self.stop_server(pid)
        return self.start_server(project_path, port=port)

    def is_running(self, pid: int) -> bool:
        if pid <= 0:
            return False
        if pid not in self._instances:
            return False
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            self._instances[pid].status = "stopped"
            del self._instances[pid]
            return False

    def list_running_instances(self) -> List[Dict]:
        alive: List[Dict] = []
        dead_pids: List[int] = []
        for pid, info in self._instances.items():
            try:
                os.kill(pid, 0)
                alive.append(info.model_dump())
            except (OSError, ProcessLookupError):
                dead_pids.append(pid)
        for pid in dead_pids:
            del self._instances[pid]
        return alive

    def stop_all(self) -> None:
        pids = list(self._instances.keys())
        for pid in pids:
            self.stop_server(pid)

    def get_instance(self, pid: int) -> Optional[InstanceInfo]:
        return self._instances.get(pid)

    def _find_instance_by_port(self, port: int) -> Optional[InstanceInfo]:
        for info in self._instances.values():
            if info.port == port:
                return info
        return None

    @staticmethod
    def _is_port_available(port: int) -> bool:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return True
            except OSError:
                return False
