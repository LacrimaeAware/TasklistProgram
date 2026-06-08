"""Generate the app icon (PNG + ICO) from code, so it's reproducible.

Run:  python tools/make_icon.py
Outputs:
  tasklistprogram/ui/assets/icon.png   (256x256, used by the Tk window/taskbar)
  tasklistprogram/ui/assets/icon.ico   (multi-size, Windows)
  web/assets/icon.png                  (favicon / PWA icon for the web prototype)
"""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SS = 4          # supersample factor for anti-aliasing
SIZE = 256
S = SIZE * SS

TOP = (91, 108, 240)     # indigo  #5B6CF0
BOTTOM = (138, 92, 246)  # violet  #8A5CF6
CHECK = (255, 255, 255)


def _lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def build() -> Image.Image:
    # Vertical gradient background.
    grad = Image.new("RGB", (S, S), TOP)
    px = grad.load()
    for y in range(S):
        color = _lerp(TOP, BOTTOM, y / (S - 1))
        for x in range(S):
            px[x, y] = color

    # Rounded-square mask.
    mask = Image.new("L", (S, S), 0)
    md = ImageDraw.Draw(mask)
    radius = int(S * 0.23)
    md.rounded_rectangle([0, 0, S - 1, S - 1], radius=radius, fill=255)

    icon = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    icon.paste(grad, (0, 0), mask)

    # Checkmark (rounded caps via 'curve' joint + circular end caps).
    d = ImageDraw.Draw(icon)
    w = int(S * 0.085)
    pts = [(int(S * 0.28), int(S * 0.52)),
           (int(S * 0.44), int(S * 0.68)),
           (int(S * 0.74), int(S * 0.34))]
    d.line(pts, fill=CHECK, width=w, joint="curve")
    for (cx, cy) in (pts[0], pts[-1]):
        r = w // 2
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=CHECK)

    return icon.resize((SIZE, SIZE), Image.LANCZOS)


def main():
    icon = build()
    png_path = ROOT / "tasklistprogram" / "ui" / "assets" / "icon.png"
    ico_path = ROOT / "tasklistprogram" / "ui" / "assets" / "icon.ico"
    web_path = ROOT / "web" / "assets" / "icon.png"
    for p in (png_path, web_path):
        p.parent.mkdir(parents=True, exist_ok=True)
    icon.save(png_path)
    icon.save(web_path)
    icon.save(ico_path, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("wrote", png_path)
    print("wrote", ico_path)
    print("wrote", web_path)


if __name__ == "__main__":
    main()
