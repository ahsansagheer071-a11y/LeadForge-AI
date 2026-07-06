import logging
from typing import Optional

from app.services.website_generator.build.builder import ProjectBuilder
from app.services.website_generator.build.runner import ProjectRunner
from app.services.website_generator.build.schemas import BuildResult
from app.services.website_generator.build.validator import ProjectValidator
from app.services.website_generator.schemas import WebsiteProject

logger = logging.getLogger(__name__)


def run_build(
    project: WebsiteProject,
    start_server: bool = False,
    port: int = 3000,
    auto_cleanup: bool = True,
) -> BuildResult:
    logger.info(
        "BuildEngine: Starting build for project '%s'...",
        project.project_name,
    )

    validator = ProjectValidator()
    builder = ProjectBuilder(validator)
    runner = ProjectRunner()

    result = builder.build(project)

    if not result.success:
        if auto_cleanup:
            builder.cleanup()
        return result

    if start_server and result.build_success:
        server_ok, url, server_log, pid = runner.start_dev_server(
            result.project_path, port=port
        )
        result.dev_server_started = server_ok
        result.server_url = url if server_ok else None
        result.server_pid = pid
        if server_log:
            result.logs.append(server_log)
        if not server_ok and url:
            result.errors.append(
                f"Dev server failed to start at {url}"
            )
    elif start_server and not result.build_success:
        logger.warning(
            "BuildEngine: Skipping dev server — build was not successful"
        )

    if auto_cleanup and not start_server:
        builder.cleanup()

    logger.info(
        "BuildEngine: Build %s (%.1fs)",
        "succeeded" if result.success else "failed",
        result.total_duration,
    )

    return result


__all__ = [
    "BuildResult",
    "ProjectBuilder",
    "ProjectRunner",
    "ProjectValidator",
    "run_build",
]
