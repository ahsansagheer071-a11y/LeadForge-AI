import logging
import os
import signal
import time
from datetime import datetime
from typing import Optional, Tuple

import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

_STARTUP_INTERVAL = 2.0
_STARTUP_TIMEOUT = 30
_BACKGROUND_INTERVAL = 30


class PreviewMonitor:
    def __init__(self) -> None:
        self._health_check_count = 0
        self._last_health_status: Optional[bool] = None

    def wait_for_health(
        self, url: str, timeout: int = _STARTUP_TIMEOUT
    ) -> Tuple[bool, float, str]:
        logger.info("PreviewMonitor: Checking health at %s...", url)
        start = time.time()

        while time.time() - start < timeout:
            healthy, elapsed, status = self.check_health(url)
            self._health_check_count += 1

            if healthy:
                duration = time.time() - start
                self._last_health_status = True
                logger.info(
                    "PreviewMonitor: Health check passed "
                    "(status=%s, time=%.1fs, startup=%.1fs)",
                    status,
                    elapsed,
                    duration,
                )
                return True, duration, str(status)

            if status == 0:
                logger.debug(
                    "PreviewMonitor: Server not ready yet "
                    "(attempt %d, %.1fs elapsed)",
                    self._health_check_count,
                    time.time() - start,
                )

            time.sleep(_STARTUP_INTERVAL)

        elapsed = time.time() - start
        self._last_health_status = False
        logger.warning(
            "PreviewMonitor: Health check timeout after %.1fs",
            elapsed,
        )
        return False, elapsed, "timeout"

    def check_health(
        self, url: str
    ) -> Tuple[bool, float, int]:
        start = time.time()
        try:
            resp = urllib.request.urlopen(url, timeout=5)
            elapsed = time.time() - start
            status = resp.status
            healthy = 200 <= status < 400

            if healthy:
                if elapsed < 0.5:
                    logger.debug(
                        "Health: %s -> %d (%.0fms) [good]",
                        url,
                        status,
                        elapsed * 1000,
                    )
                elif elapsed < 2.0:
                    logger.debug(
                        "Health: %s -> %d (%.0fms) [degraded]",
                        url,
                        status,
                        elapsed * 1000,
                    )
                else:
                    logger.warning(
                        "Health: %s -> %d (%.0fms) [slow]",
                        url,
                        status,
                        elapsed * 1000,
                    )
            return healthy, elapsed, status
        except urllib.error.HTTPError as e:
            elapsed = time.time() - start
            return 100 <= e.code < 400, elapsed, e.code
        except (urllib.error.URLError, OSError) as e:
            elapsed = time.time() - start
            return False, elapsed, 0

    def monitor_loop(
        self,
        pid: int,
        url: str,
        interval: int = _BACKGROUND_INTERVAL,
    ) -> None:
        logger.info(
            "PreviewMonitor: Starting background loop (PID %d, %s)",
            pid,
            url,
        )
        while True:
            if not self._is_process_alive(pid):
                logger.error(
                    "PreviewMonitor: Process %d died — stopping monitor",
                    pid,
                )
                break

            healthy, elapsed, status = self.check_health(url)
            self._health_check_count += 1

            if not healthy:
                logger.warning(
                    "PreviewMonitor: Health check %d failed (PID %d)",
                    self._health_check_count,
                    pid,
                )

            time.sleep(interval)

    def detect_crash(self, pid: int) -> bool:
        if not self._is_process_alive(pid):
            logger.error("PreviewMonitor: Process %d has crashed", pid)
            return True
        return False

    @property
    def health_check_count(self) -> int:
        return self._health_check_count

    @property
    def last_health_status(self) -> Optional[bool]:
        return self._last_health_status

    @staticmethod
    def categorize_response_time(elapsed: float) -> str:
        if elapsed < 0.5:
            return "good"
        elif elapsed < 2.0:
            return "degraded"
        return "slow"

    @staticmethod
    def _is_process_alive(pid: int) -> bool:
        if pid <= 0:
            return False
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False
