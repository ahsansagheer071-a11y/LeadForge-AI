"""Regression test for _optimize_image: oversized PNG → WebP below 9.5 MB."""
import os
import sys
import tempfile
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Suppress logging noise during test
import logging
logging.disable(logging.CRITICAL)

from app.services.screenshot import _optimize_image, _CLOUDINARY_MAX_BYTES

PASS = 0
FAIL = 0

def _create_large_png(width: int, height: int, tmpdir: str) -> str:
    """Create a large PNG by filling with high-frequency noise."""
    path = os.path.join(tmpdir, f"test_{width}x{height}.png")
    img = Image.new("RGB", (width, height))
    import random
    rng = random.Random(42)
    pixels = img.load()
    for x in range(width):
        for y in range(height):
            pixels[x, y] = (rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255))
    img.save(path, "PNG", compress_level=1)
    return path


def t(name, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name}: {detail}")


def main():
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Test basic optimization: 2048×1080 RGB PNG → should compress well
        png_path = _create_large_png(2048, 1080, tmpdir)
        original_size = os.path.getsize(png_path)
        print(f"  PNG 2048×1080: {original_size} bytes ({original_size/1024/1024:.1f} MB)")

        opt_path = png_path.replace(".png", "_opt.webp")
        final_size = _optimize_image(png_path, opt_path)

        t("Optimized size below 9.5 MB", final_size <= _CLOUDINARY_MAX_BYTES,
          f"Got {final_size} bytes")
        t("Optimized file exists", os.path.exists(opt_path),
          f"Expected {opt_path}")

        with Image.open(opt_path) as img:
            t("Format is WebP", img.format == "WEBP", f"Got {img.format}")
            # 2048 > 1920, so resized to 1920
            expected_h = int(1080 * 1920 / 2048)
            t("Width ≤ 1920 after resize", img.width <= 1920,
              f"Width is {img.width}")
            t("Aspect ratio preserved ±1px",
              abs(img.height - expected_h) <= 1,
              f"Expected {expected_h}, got {img.height}")

        # 2. Test fallback resize: huge image that quality alone can't fix
        huge_path = _create_large_png(4096, 2160, tmpdir)
        huge_orig = os.path.getsize(huge_path)
        print(f"  PNG 4096×2160: {huge_orig} bytes ({huge_orig/1024/1024:.1f} MB)")
        huge_opt = huge_path.replace(".png", "_opt.webp")
        huge_size = _optimize_image(huge_path, huge_opt)

        t("Huge image fits after fallback resize",
          huge_size <= _CLOUDINARY_MAX_BYTES,
          f"Got {huge_size} bytes")
        t("Huge optimized file exists", os.path.exists(huge_opt), "")
        with Image.open(huge_opt) as img:
            t("Huge image width ≤ 1920", img.width <= 1920,
              f"Width is {img.width}")
            t("Huge format is WebP", img.format == "WEBP", f"Got {img.format}")

        # 3. Confirm temp files not auto-cleaned by _optimize_image
        t("Original PNG preserved (cleanup is caller's responsibility)",
          os.path.exists(png_path), str(png_path))

        # 4. Cleanup simulation
        for f in (opt_path, huge_opt):
            if os.path.exists(f):
                os.remove(f)
        t("Opt files can be cleaned after test",
          not os.path.exists(opt_path), "")

    print(f"\nResults: {PASS} passed, {FAIL} failed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
