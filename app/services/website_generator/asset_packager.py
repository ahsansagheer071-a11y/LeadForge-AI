"""AssetPackager — downloads approved source images and rewrites HTML to use local paths.

After AI generation produces HTML with remote image URLs (pointing to the original
source website), AssetPackager downloads the approved images, rewrites <img> src
attributes to local assets/images/ paths, and returns the image artifacts for ZIP
packaging.
"""

import asyncio
import base64
import logging
import os
import re
import tempfile
from typing import Dict, List, Optional, Set, Tuple

from app.services.markdown_engine.asset_manifest import (
    AssetManifest,
    AssetManifestItem,
    ImageDownloader,
)
from app.services.website_generator.schemas import ImageArtifact

logger = logging.getLogger(__name__)

_ASSET_DIR = "assets/images"


class AssetPackager:
    """Downloads approved source images and rewrites generated HTML to local paths."""

    def __init__(self, workspace_dir: Optional[str] = None):
        self._workspace_dir = workspace_dir or tempfile.mkdtemp(prefix="leadforge_assets_")

    @property
    def workspace_dir(self) -> str:
        return self._workspace_dir

    async def package_assets_async(
        self,
        html: str,
        manifest: AssetManifest,
    ) -> Tuple[str, List[ImageArtifact], List[str]]:
        """Async version: download approved images, rewrite HTML, return artifacts.

        Returns:
            (rewritten_html, image_artifacts, warnings)
        """
        if not manifest or not manifest.items:
            return html, [], ["No AssetManifest provided; images not packaged locally."]

        warnings: List[str] = []
        artifacts: List[ImageArtifact] = []
        url_to_local: Dict[str, str] = {}
        downloaded_count = 0
        failed_count = 0

        downloader = ImageDownloader(workspace_dir=self._workspace_dir)
        downloaded_manifest = await downloader.download_all(manifest)

        for item in downloaded_manifest.items:
            original_url = item.original_url or item.absolute_url
            if not original_url:
                continue

            if item.download_status.value == "downloaded" and item.local_filename:
                local_path = f"{_ASSET_DIR}/{item.local_filename}"
                url_to_local[original_url] = local_path
                if item.absolute_url and item.absolute_url != original_url:
                    url_to_local[item.absolute_url] = local_path

                # Read the downloaded file and encode as base64
                file_path = os.path.join(self._workspace_dir, item.local_filename)
                if os.path.exists(file_path):
                    try:
                        with open(file_path, "rb") as f:
                            data = f.read()
                        b64 = base64.b64encode(data).decode("ascii")
                        artifacts.append(ImageArtifact(
                            filename=item.local_filename,
                            path=local_path,
                            content_base64=b64,
                            size=len(data),
                            original_url=original_url,
                        ))
                        downloaded_count += 1
                    except Exception as e:
                        warnings.append(f"Failed to read downloaded image {item.local_filename}: {e}")
                        failed_count += 1
                else:
                    warnings.append(f"Downloaded image file not found: {file_path}")
                    failed_count += 1
            elif item.download_status.value == "failed":
                failed_count += 1
                if item.failure_reason:
                    warnings.append(
                        f"Image download failed for {original_url}: {item.failure_reason}"
                    )

        if not url_to_local:
            logger.warning("AssetPackager: no images were successfully downloaded.")
            return html, artifacts, warnings or ["No images could be downloaded from source."]

        # Rewrite HTML img src attributes to local paths
        rewritten = self._rewrite_html_src(html, url_to_local, warnings)

        logger.info(
            "AssetPackager: %d/%d images downloaded and packaged (%d failed)",
            downloaded_count, len(manifest.items), failed_count,
        )
        return rewritten, artifacts, warnings

    def _rewrite_html_src(
        self,
        html: str,
        url_to_local: Dict[str, str],
        warnings: List[str],
    ) -> str:
        """Replace remote image URLs in HTML with local asset paths."""

        def _replace_src(match: re.Match) -> str:
            full_tag = match.group(0)
            src_value = match.group(1)
            local = url_to_local.get(src_value)
            if local:
                return full_tag.replace(f'src="{src_value}"', f'src="{local}"')
            # Try matching with common URL variations
            for remote, local in url_to_local.items():
                if src_value in remote or remote in src_value:
                    return full_tag.replace(f'src="{src_value}"', f'src="{local}"')
            return full_tag

        # Replace <img src="..."> patterns
        rewritten = re.sub(
            r'<img[^>]+src\s*=\s*"([^"]+)"[^>]*>',
            _replace_src,
            html,
            flags=re.IGNORECASE,
        )

        # Also replace src='...' patterns
        rewritten = re.sub(
            r"<img[^>]+src\s*=\s*'([^']+)'[^>]*>",
            _replace_src,
            rewritten,
            flags=re.IGNORECASE,
        )

        changed = rewritten != html
        if changed:
            # Count how many were replaced
            src_count_before = len(re.findall(r'<img[^>]+src\s*=', html, re.IGNORECASE))
            logger.info(
                "AssetPackager: rewrote HTML image references (%d <img> tags processed)",
                src_count_before,
            )
        return rewritten

    def cleanup(self) -> None:
        """Remove the temporary workspace directory."""
        import shutil
        if self._workspace_dir and os.path.exists(self._workspace_dir):
            try:
                shutil.rmtree(self._workspace_dir)
                logger.info("AssetPackager: cleaned up workspace %s", self._workspace_dir)
            except Exception as e:
                logger.warning("AssetPackager: cleanup failed: %s", e)
