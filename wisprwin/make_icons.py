"""
make_icons.py — Generate system tray PNG icons via Pillow.

Run once to create assets/icon_idle.png, icon_recording.png, icon_processing.png.
Each icon is a 64x64 circle with a simple mic silhouette.

Colors:
  Idle       — white circle, dark mic
  Recording  — red (#E53935), white mic
  Processing — amber (#FFB300), dark mic
"""

from pathlib import Path
from PIL import Image, ImageDraw

SIZE = 64
ASSETS_DIR = Path(__file__).resolve().parent / "assets"


def _draw_icon(bg_color: str, mic_color: str) -> Image.Image:
    """Draw a circular icon with a mic silhouette."""
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background circle
    margin = 2
    draw.ellipse(
        [margin, margin, SIZE - margin, SIZE - margin],
        fill=bg_color,
    )

    # Mic body (rounded rectangle)
    mic_w, mic_h = 18, 24
    mic_x = (SIZE - mic_w) // 2
    mic_y = 10
    draw.rounded_rectangle(
        [mic_x, mic_y, mic_x + mic_w, mic_y + mic_h],
        radius=9,
        fill=mic_color,
    )

    # Mic stand arc (U-shape via partial ellipse trick)
    stand_margin = 8
    arc_box = [stand_margin, mic_y + mic_h // 2, SIZE - stand_margin, mic_y + mic_h + 14]
    draw.arc(arc_box, start=0, end=180, fill=mic_color, width=3)

    # Mic base line
    base_y = arc_box[3] + 1
    draw.line([(SIZE // 2, arc_box[3]), (SIZE // 2, base_y + 5)], fill=mic_color, width=3)
    draw.line([(SIZE // 2 - 7, base_y + 5), (SIZE // 2 + 7, base_y + 5)], fill=mic_color, width=3)

    return img


def make_icons() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    icons = {
        "icon_idle.png":       ("#FFFFFF", "#2D2D2D"),
        "icon_recording.png":  ("#E53935", "#FFFFFF"),
        "icon_processing.png": ("#FFB300", "#2D2D2D"),
    }

    for filename, (bg, mic) in icons.items():
        img = _draw_icon(bg, mic)
        path = ASSETS_DIR / filename
        img.save(path)
        print(f"[make_icons] Saved {path}")

    # Generate .ico for PyInstaller (multi-size)
    _make_ico()


def _make_ico() -> None:
    """Generate a multi-size .ico file from the idle icon for PyInstaller."""
    ico_path = ASSETS_DIR / "icon.ico"
    sizes = [16, 32, 48, 64, 128, 256]
    images = []

    for s in sizes:
        img = _draw_icon("#7C3AED", "#FFFFFF")  # Purple accent bg, white mic
        img = img.resize((s, s), Image.LANCZOS)
        images.append(img)

    # Save as ICO with multiple sizes
    images[0].save(
        ico_path,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:],
    )
    print(f"[make_icons] Saved {ico_path}")


if __name__ == "__main__":
    make_icons()
    print("[make_icons] All icons generated.")
