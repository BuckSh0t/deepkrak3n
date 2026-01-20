from __future__ import annotations

import math
from pathlib import Path
from typing import Tuple

from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
LOGO_PATH = ROOT / "deepkrak3nlogo.png"
OUT_PATH = ROOT / "public" / "deepkrak3n-glitch.gif"

BG = (6, 7, 13)  # matches app background
tint_red = (185, 28, 28)
tint_cyan = (37, 99, 235)
text_color = (230, 236, 255)
shadow = (20, 24, 36)

CANVAS = (720, 520)
FRAME_COUNT = 14
DURATION_MS = 70  # per frame


def load_font(size: int) -> ImageFont.FreeTypeFont:
    # DejaVuSans ships with Pillow; fallback to default.
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size=size)
    except Exception:
        return ImageFont.load_default()


def center_position(base_w: int, base_h: int, obj_w: int, obj_h: int, y: int) -> Tuple[int, int]:
    return (base_w - obj_w) // 2, y


def make_text_image(text: str, font: ImageFont.ImageFont) -> Image.Image:
    bbox = font.getbbox(text)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = 6
    img = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((pad, pad), text, font=font, fill=text_color)
    return img


def add_channel_glitch(base: Image.Image, offset: Tuple[int, int]) -> Image.Image:
    # Duplicate base into color channels and offset them slightly.
    r, g, b, a = base.split()
    r_shift = ImageChops.offset(r, offset[0], offset[1])
    b_shift = ImageChops.offset(b, -offset[0], -offset[1])
    merged = Image.merge("RGBA", (r_shift, g, b_shift, a))
    return merged


def add_scan_lines(img: Image.Image, opacity: int = 40) -> None:
    draw = ImageDraw.Draw(img)
    w, h = img.size
    for y in range(0, h, 3):
        draw.line([(0, y), (w, y)], fill=(255, 255, 255, opacity))


def main() -> None:
    logo = Image.open(LOGO_PATH).convert("RGBA")
    # Scale logo to fit top area
    max_logo_w = CANVAS[0] - 160
    scale = min(1.0, max_logo_w / logo.width)
    logo = logo.resize((int(logo.width * scale), int(logo.height * scale)), Image.LANCZOS)

    font = load_font(56)
    text_img = make_text_image("deepkrak3n", font)

    frames = []
    for i in range(FRAME_COUNT):
        frame = Image.new("RGBA", CANVAS, BG + (255,))
        # top logo position
        logo_x, logo_y = center_position(CANVAS[0], CANVAS[1], logo.width, logo.height, 26)
        # right-side text position
        text_x = CANVAS[0] - text_img.width - 38
        text_y = logo_y + logo.height // 2 - text_img.height // 2

        # subtle vertical bob for logo
        bob = int(math.sin(i / 2) * 2)
        frame.paste(logo, (logo_x, logo_y + bob), logo)

        # shadow behind text
        shadow_img = ImageChops.offset(text_img, 2, 2)
        shadow_base = Image.new("RGBA", text_img.size, shadow + (130,))
        shadow_img = ImageChops.multiply(shadow_img, shadow_base)
        frame.paste(shadow_img, (text_x, text_y), shadow_img)

        # glitch offsets
        dx = int(math.sin(i * 0.8) * 3)
        dy = int(math.cos(i * 0.6) * 2)
        glitch_text = add_channel_glitch(text_img, (dx, dy))
        glitch_logo = add_channel_glitch(logo, (-dx, dy))

        frame.paste(glitch_logo, (logo_x, logo_y + bob), glitch_logo)
        frame.paste(glitch_text, (text_x, text_y), glitch_text)

        # occasional slice shift
        if i % 3 == 0:
            slice_h = 12
            y0 = (i * 23) % (CANVAS[1] - slice_h)
            band = frame.crop((0, y0, CANVAS[0], y0 + slice_h))
            band = ImageChops.offset(band, dx * 3, 0)
            frame.paste(band, (0, y0))

        add_scan_lines(frame, opacity=26)
        frames.append(frame.convert("P", palette=Image.ADAPTIVE))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        OUT_PATH,
        save_all=True,
        append_images=frames[1:],
        loop=0,
        duration=DURATION_MS,
        transparency=0,
        disposal=2,
    )
    print(f"Wrote {OUT_PATH} ({len(frames)} frames)")


if __name__ == "__main__":
    main()
