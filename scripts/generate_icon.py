#!/usr/bin/env python3
"""
Generate O.D.I.A. desktop icon — purple octopus DJ theme.

Produces desktop/resources/icon.png (1024×1024).
electron-builder auto-converts to .ico (Windows) and .icns (macOS).

Run:  python3 scripts/generate_icon.py
Deps: pip install pillow
"""

import math
import os
import struct
import zlib

# ---------------------------------------------------------------------------
# Pure-stdlib minimal PNG writer (no Pillow required for CI fallback)
# Used only when Pillow is unavailable.
# ---------------------------------------------------------------------------


def _write_png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    chunk_len = struct.pack(">I", len(data))
    chunk_data = chunk_type + data
    chunk_crc = struct.pack(">I", zlib.crc32(chunk_data) & 0xFFFFFFFF)
    return chunk_len + chunk_data + chunk_crc


def _make_minimal_png(size: int, bg_rgb: tuple, fg_rgb: tuple) -> bytes:
    """Create a solid-colour PNG with a simple 'STR' octopus placeholder."""
    width = height = size
    raw_rows = []
    for y in range(height):
        row = bytearray([0])  # filter byte
        cx, cy = width / 2, height / 2
        r_outer = width * 0.44
        r_inner = width * 0.28
        for x in range(width):
            dx, dy = x - cx, y - cy
            dist = math.sqrt(dx * dx + dy * dy)
            # Head circle
            if dist < r_inner:
                row += bytearray(fg_rgb)
            # Ring / tentacle halo
            elif r_inner * 1.1 < dist < r_outer:
                # Tentacles: 8 equally-spaced radial spokes
                angle = (math.atan2(dy, dx) + math.pi) / (2 * math.pi)
                spoke = (angle * 8) % 1.0
                row += bytearray(fg_rgb if spoke < 0.25 else bg_rgb)
            else:
                row += bytearray(bg_rgb)
        raw_rows.append(bytes(row))

    compressed = zlib.compress(b"".join(raw_rows), 9)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _write_png_chunk(b"IHDR", ihdr)
        + _write_png_chunk(b"IDAT", compressed)
        + _write_png_chunk(b"IEND", b"")
    )
    return png


# ---------------------------------------------------------------------------
# Pillow version — richer, used when available
# ---------------------------------------------------------------------------


def _make_pillow_icon(size: int, out_path: str) -> None:
    from PIL import Image, ImageDraw, ImageFilter

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = size // 2, size // 2
    pad = size // 16

    # ── Background circle ─────────────────────────────────────────────────
    draw.ellipse([pad, pad, size - pad, size - pad], fill=(30, 10, 60, 255))

    # ── Tentacles (8 rounded arcs radiating from bottom of head) ──────────
    head_r = int(size * 0.30)
    tent_len = int(size * 0.22)
    tent_w = max(4, size // 40)
    tentacle_color = (140, 60, 200, 230)
    for i in range(8):
        angle_deg = 180 + (i - 3.5) * 22
        angle_rad = math.radians(angle_deg)
        x0 = int(cx + head_r * 0.7 * math.cos(angle_rad))
        y0 = int(cy + head_r * 0.5 + head_r * 0.4 * abs(math.sin(angle_rad)))
        x1 = int(x0 + tent_len * math.cos(angle_rad))
        y1 = int(y0 + tent_len * math.sin(angle_rad) + tent_len * 0.3)
        draw.line([(x0, y0), (x1, y1)], fill=tentacle_color, width=tent_w)
        # Sucker dot
        draw.ellipse(
            [x1 - tent_w, y1 - tent_w, x1 + tent_w, y1 + tent_w],
            fill=(200, 100, 255, 200),
        )

    # ── Head ──────────────────────────────────────────────────────────────
    draw.ellipse(
        [cx - head_r, cy - head_r, cx + head_r, cy + head_r],
        fill=(120, 50, 180, 255),
    )
    # Head highlight
    hl = head_r // 3
    draw.ellipse(
        [cx - hl * 2, cy - head_r + hl // 2, cx - hl // 2, cy - head_r + hl * 2],
        fill=(200, 160, 255, 120),
    )

    # ── Headphones ────────────────────────────────────────────────────────
    hp_r = int(head_r * 1.15)
    hp_w = max(3, size // 50)
    hp_color = (60, 60, 80, 255)
    draw.arc(
        [cx - hp_r, cy - hp_r, cx + hp_r, cy + hp_r],
        start=200,
        end=340,
        fill=hp_color,
        width=hp_w,
    )
    # Ear-cups
    cup_r = int(head_r * 0.22)
    for side in [-1, 1]:
        ex = cx + side * hp_r
        ey = cy
        draw.ellipse(
            [ex - cup_r, ey - cup_r, ex + cup_r, ey + cup_r],
            fill=(50, 50, 70, 255),
        )
        # LED dot
        draw.ellipse(
            [ex - cup_r // 3, ey - cup_r // 3, ex + cup_r // 3, ey + cup_r // 3],
            fill=(180, 100, 255, 255),
        )

    # ── Goggles ───────────────────────────────────────────────────────────
    eye_y = cy - head_r // 6
    eye_x_off = int(head_r * 0.38)
    eye_r = int(head_r * 0.28)
    # Bridge
    draw.line(
        [(cx - eye_x_off + eye_r, eye_y), (cx + eye_x_off - eye_r, eye_y)],
        fill=(60, 60, 80, 255),
        width=max(2, size // 80),
    )
    for side in [-1, 1]:
        ex = cx + side * eye_x_off
        # Goggle frame
        draw.ellipse(
            [ex - eye_r, eye_y - eye_r, ex + eye_r, eye_y + eye_r],
            fill=(40, 40, 60, 255),
        )
        # Goggle lens
        lens_r = int(eye_r * 0.72)
        draw.ellipse(
            [ex - lens_r, eye_y - lens_r, ex + lens_r, eye_y + lens_r],
            fill=(100, 40, 160, 240),
        )
        # Pupil glow
        glow_r = lens_r // 2
        draw.ellipse(
            [ex - glow_r, eye_y - glow_r, ex + glow_r, eye_y + glow_r],
            fill=(180, 100, 255, 255),
        )

    # ── Keyboard hands ────────────────────────────────────────────────────
    kb_y = cy + head_r + int(size * 0.04)
    kb_h = int(size * 0.07)
    kb_w = int(size * 0.28)
    kb_color = (50, 50, 70, 255)
    for side in [-1, 1]:
        kx = cx + side * int(size * 0.16)
        draw.rounded_rectangle(
            [kx - kb_w // 2, kb_y, kx + kb_w // 2, kb_y + kb_h],
            radius=max(3, kb_h // 4),
            fill=kb_color,
        )
        # Key dots
        cols, rows = 5, 2
        kw_step = kb_w // (cols + 1)
        kh_step = kb_h // (rows + 1)
        dot_r = max(2, size // 200)
        for col in range(1, cols + 1):
            for row in range(1, rows + 1):
                dx = kx - kb_w // 2 + col * kw_step
                dy = kb_y + row * kh_step
                draw.ellipse(
                    [dx - dot_r, dy - dot_r, dx + dot_r, dy + dot_r],
                    fill=(150, 100, 220, 255),
                )

    # ── Amber "STR" brand text in corner ──────────────────────────────────
    # (text requires font; skip if default font is too small)
    try:
        from PIL import ImageFont

        font_size = max(16, size // 20)
        font = ImageFont.load_default(size=font_size)
        draw.text((pad * 2, pad * 2), "STR", font=font, fill=(255, 170, 0, 220))
    except Exception:
        pass

    # Slight outer glow via blur on a separate layer
    glow_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    glow_draw.ellipse([pad, pad, size - pad, size - pad], fill=(120, 50, 180, 60))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(size // 16))
    img = Image.alpha_composite(glow_layer, img)

    img.save(out_path, "PNG")
    print(f"Generated icon: {out_path} ({size}×{size})")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_path = os.path.join(repo_root, "desktop", "resources", "icon.png")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    size = 1024
    try:
        _make_pillow_icon(size, out_path)
    except ImportError:
        print("Pillow not available — generating minimal placeholder PNG")
        png_bytes = _make_minimal_png(
            size,
            bg_rgb=(30, 10, 60),  # dark purple
            fg_rgb=(180, 100, 255),  # bright purple
        )
        with open(out_path, "wb") as f:
            f.write(png_bytes)
        print(f"Generated fallback icon: {out_path}")


if __name__ == "__main__":
    main()
