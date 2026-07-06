import logging
import os
import platform
import signal
import subprocess
import time
from typing import Optional, Tuple

import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

_HEALTH_CHECK_INTERVAL = 1.0
_HEALTH_CHECK_TIMEOUT = 30


class ProjectRunner:
    _USE_SHELL = platform.system() == "Windows"

    def __init__(self) -> None:
        self._process: subprocess.Popen | None = None

    def start_dev_server(
        self, project_dir: str, port: int = 3000
    ) -> Tuple[bool, str, str, Optional[int]]:
        logger.info("ProjectRunner: Starting dev server...")

        if not os.path.isdir(project_dir):
            msg = f"Project directory not found: {project_dir}"
            logger.error(msg)
            return False, "", msg, None

        if not os.path.isfile(os.path.join(project_dir, "package.json")):
            msg = "No package.json found in project directory"
            logger.error(msg)
            return False, "", msg, None

        url = f"http://localhost:{port}"

        try:
            args = "npm run dev -- -p %d" % port if self._USE_SHELL else ["npm", "run", "dev", "--", "-p", str(port)]
            self._process = subprocess.Popen(
                args,
                cwd=project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=self._USE_SHELL,
            )
        except FileNotFoundError:
            msg = "npm command not found — is Node.js installed?"
            logger.error(msg)
            return False, "", msg, None
        except OSError as e:
            msg = f"Failed to start dev server: {e}"
            logger.error(msg)
            return False, "", msg, None

        pid = self._process.pid
        logger.info(
            "ProjectRunner: Dev server started (PID %d), polling %s...",
            pid,
            url,
        )

        ready = self.wait_for_server(url, timeout=_HEALTH_CHECK_TIMEOUT)

        if ready:
            logs = f"Dev server running at {url} (PID {pid})"
            logger.info("Dev server running at %s", url)
            return True, url, logs, pid
        else:
            stdout, stderr = "", ""
            try:
                stdout, stderr = self._process.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                pass
            msg = f"Server failed to start within {_HEALTH_CHECK_TIMEOUT}s"
            if stderr:
                msg += f": {stderr[:500]}"
            logger.error(msg)
            self.stop_dev_server(pid)
            return False, url, msg, None

    @staticmethod
    def wait_for_server(
        url: str, timeout: int = _HEALTH_CHECK_TIMEOUT
    ) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            try:
                resp = urllib.request.urlopen(url, timeout=3)
                if resp.status == 200:
                    duration = time.time() - start
                    logger.info(
                        "Server ready in %.1fs", duration
                    )
                    return True
            except (urllib.error.URLError, urllib.error.HTTPError):
                pass
            except OSError:
                pass
            time.sleep(_HEALTH_CHECK_INTERVAL)
        return False

    @staticmethod
    def stop_dev_server(pid: Optional[int]) -> bool:
        if pid is None:
            return False
        if platform.system() == "Windows":
            # On Windows, kill the entire process tree (npm -> node -> next)
            try:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(pid)],
                    capture_output=True, text=True, shell=True,
                )
                logger.info("ProjectRunner: Stopped dev server (PID %d tree)", pid)
                return True
            except Exception as e:
                logger.warning("ProjectRunner: Could not stop PID %d tree: %s", pid, e)
                # Fallback to os.kill
                try:
                    os.kill(pid, signal.SIGTERM)
                    return True
                except (OSError, ProcessLookupError):
                    logger.warning(
                        "ProjectRunner: Could not stop PID %d (may already be dead)",
                        pid,
                    )
                    return False
        else:
            try:
                os.kill(pid, signal.SIGTERM)
                logger.info("ProjectRunner: Stopped dev server (PID %d)", pid)
                return True
            except (OSError, ProcessLookupError):
                logger.warning(
                    "ProjectRunner: Could not stop PID %d (may already be dead)",
                    pid,
                )
                return False

    def stop(self) -> bool:
        if self._process is not None:
            pid = self._process.pid
            if platform.system() == "Windows":
                # Kill the process tree on Windows
                try:
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(pid)],
                        capture_output=True, text=True, shell=True,
                    )
                except Exception:
                    pass
            else:
                self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None
            logger.info(
                "ProjectRunner: Stopped dev server (PID %d)", pid
            )
            return True
        return False
