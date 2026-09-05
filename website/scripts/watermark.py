"""
Apply XFTF watermark + DO NOT DUPLICATE badge to top-right of photos.
Run via Docker:
  docker run --rm -v "/c/Users/b2/source/repos/GoldenEagleConference/website:/work" -w /work python:3.12-slim sh -c "pip install -q pillow && python scripts/watermark.py [--single FILE]"
"""
import sys
import os
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
LOGO_PATH = ROOT / "assets" / "sftf-logo.png"

WATERMARK_TEXT_LINE1 = "DO NOT DUPLICATE"
WATERMARK_TEXT_LINE2 = "MOCS 2026 · XFTF.ORG"

# Tunables
LOGO_TARGET_WIDTH_PCT = 0.10   # logo width as % of image width
LOGO_MAX_PX = 180               # cap logo width
PADDING_PCT = 0.018             # margin from edges
BADGE_BG_OPACITY = 170          # 0-255, dark backing strip
BADGE_PADDING = 14              # internal padding inside the badge


def find_font(size: int) -> ImageFont.FreeTypeFont:
    """Find a usable bold font (DejaVu ships with Pillow on most Linux containers)."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()


def watermark_image(src: Path, dst: Path, logo: Image.Image) -> None:
    img = Image.open(src).convert("RGB")
    img = ImageOps.exif_transpose(img)  # respect EXIF orientation
    W, H = img.size

    # Resize logo
    target_w = min(int(W * LOGO_TARGET_WIDTH_PCT), LOGO_MAX_PX)
    ratio = target_w / logo.width
    target_h = int(logo.height * ratio)
    logo_resized = logo.resize((target_w, target_h), Image.LANCZOS)

    # Build badge: logo on top, two lines of text below
    text_size_1 = max(11, int(target_w * 0.16))   # DO NOT DUPLICATE — bigger
    text_size_2 = max(9, int(target_w * 0.11))    # MOCS · XFTF — smaller

    font1 = find_font(text_size_1)
    font2 = find_font(text_size_2)

    # Measure text bounds
    dummy_draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    t1_w, t1_h = dummy_draw.textbbox((0, 0), WATERMARK_TEXT_LINE1, font=font1)[2:]
    t2_w, t2_h = dummy_draw.textbbox((0, 0), WATERMARK_TEXT_LINE2, font=font2)[2:]

    badge_w = max(target_w, t1_w, t2_w) + 2 * BADGE_PADDING
    badge_h = target_h + t1_h + t2_h + 2 * BADGE_PADDING + 8  # small gaps
    badge = Image.new("RGBA", (badge_w, badge_h), (10, 24, 44, BADGE_BG_OPACITY))

    # Optional thin gold border on the badge
    border_layer = ImageDraw.Draw(badge)
    border_layer.rectangle([(0, 0), (badge_w - 1, badge_h - 1)], outline=(244, 195, 0, 220), width=1)

    # Paste logo centered horizontally near the top of the badge
    logo_x = (badge_w - target_w) // 2
    logo_y = BADGE_PADDING
    badge.alpha_composite(logo_resized.convert("RGBA"), (logo_x, logo_y))

    # Draw text
    draw = ImageDraw.Draw(badge)
    t1_x = (badge_w - t1_w) // 2
    t1_y = logo_y + target_h + 4
    draw.text((t1_x, t1_y), WATERMARK_TEXT_LINE1, font=font1, fill=(244, 195, 0, 255))

    t2_x = (badge_w - t2_w) // 2
    t2_y = t1_y + t1_h + 2
    draw.text((t2_x, t2_y), WATERMARK_TEXT_LINE2, font=font2, fill=(232, 243, 255, 230))

    # Paste badge top-right with padding
    pad_x = int(W * PADDING_PCT)
    pad_y = int(H * PADDING_PCT)
    pos_x = W - badge_w - pad_x
    pos_y = pad_y

    img_rgba = img.convert("RGBA")
    img_rgba.alpha_composite(badge, (pos_x, pos_y))

    out = img_rgba.convert("RGB")

    # EXIF / metadata
    out.info["copyright"] = "© Security For The Folks (XFTF) — MOCS 2026 · DO NOT DUPLICATE"

    dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(dst, "JPEG", quality=88, optimize=True, progressive=True)
    print(f"  wrote {dst.relative_to(ROOT)} ({W}x{H})")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--single", help="Process only this file")
    ap.add_argument("--src-dir", default="assets/recap-2026", help="Source directory of photos")
    ap.add_argument("--dst-dir", default="assets/recap-2026-wm", help="Destination directory for watermarked photos")
    args = ap.parse_args()

    if not LOGO_PATH.exists():
        print(f"ERROR: logo not found at {LOGO_PATH}", file=sys.stderr)
        return 1

    logo = Image.open(LOGO_PATH).convert("RGBA")
    src_dir = ROOT / args.src_dir
    dst_dir = ROOT / args.dst_dir

    if args.single:
        src = Path(args.single)
        if not src.is_absolute():
            src = src_dir / src
        if not src.exists():
            print(f"ERROR: {src} not found", file=sys.stderr)
            return 1
        watermark_image(src, dst_dir / src.name, logo)
        return 0

    files = sorted([p for p in src_dir.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png")])
    if not files:
        print(f"No photos found in {src_dir}", file=sys.stderr)
        return 1

    print(f"Processing {len(files)} photos from {src_dir} -> {dst_dir}")
    for p in files:
        watermark_image(p, dst_dir / p.name, logo)

    print(f"\nDone. Output: {dst_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
