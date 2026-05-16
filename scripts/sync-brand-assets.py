"""Crop falcon mark, sync docs + frontend public icons."""
from __future__ import annotations

from pathlib import Path

from PIL import Image
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "assets" / "sandesh-icon.png"


def main() -> None:
    img = Image.open(SRC).convert("RGBA")
    arr = np.array(img)
    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
    dark = (r < 45) & (g < 45) & (b < 45) & (a > 128)
    arr[dark, 3] = 0
    visible = arr[:, :, 3] > 20
    ys, xs = np.where(visible)
    x0, x1 = xs.min(), xs.max()
    y0, y1 = ys.min(), ys.max()
    pad = 8
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
    x1, y1 = min(arr.shape[1] - 1, x1 + pad), min(arr.shape[0] - 1, y1 + pad)
    cropped = Image.fromarray(arr, "RGBA").crop((x0, y0, x1 + 1, y1 + 1))

    assets = ROOT / "docs" / "assets"
    pub = ROOT / "frontend" / "public"
    for dest in (assets / "sandesh-icon.png", assets / "sandesh-logo.png", pub / "sandesh-icon.png"):
        cropped.save(dest, "PNG")

    readme = Image.new("RGB", cropped.size, (255, 255, 255))
    readme.paste(cropped, mask=cropped.split()[3])
    readme.save(assets / "sandesh-logo-readme.png", "PNG")

    for size, name in ((192, "logo192.png"), (512, "logo512.png")):
        s = cropped.copy()
        s.thumbnail((size, size), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        ox, oy = (size - s.width) // 2, (size - s.height) // 2
        canvas.paste(s, (ox, oy), s)
        canvas.save(pub / name, "PNG")

    print(f"Synced brand assets ({cropped.size[0]}x{cropped.size[1]})")


if __name__ == "__main__":
    main()
