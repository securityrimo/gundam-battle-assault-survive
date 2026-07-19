# -*- coding: utf-8 -*-
"""시추에이션 시작 연출의 미션명 GIM 181장을 한글로 재도색한다.

각 미션의 ``<mission>_o`` 번들에는 ``intro_<mission>.gim``이 있으며,
이 파일에 붓글씨 일본어 제목이 이미지로 직접 들어 있다. EBOOT의 같은 제목은
선택 화면용이므로 시작 연출을 바꾸려면 이 GIM을 별도로 패치해야 한다.
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys

sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gbu")

import gimutil as GU
from PIL import Image, ImageDraw, ImageFont

import gaslib as G


BASE = os.path.dirname(os.path.abspath(__file__))
FONT = r"C:\Windows\Fonts\malgunbd.ttf"
TITLE_MIN = 3_064_000
TITLE_MAX = 3_089_000


def load_titles():
    """EBOOT 레코드에서 mission id를 얻고 최종 한글 제목을 반환한다."""
    elf = open(os.path.join(BASE, "EBOOT_dec.elf"), "rb").read()
    short_path = os.path.join(BASE, "eboot_ui_short.json")
    short = json.load(open(short_path, encoding="utf-8")) if os.path.exists(short_path) else {}
    out = {}
    with open(
        os.path.join(BASE, "translate", "eboot_ui.csv"),
        encoding="utf-8-sig",
        newline="",
    ) as f:
        for row in csv.DictReader(f):
            try:
                off = int(row["key"].split("|")[-1])
            except (KeyError, ValueError):
                continue
            if not (TITLE_MIN <= off < TITLE_MAX):
                continue
            original = row.get("원문", "")
            korean = short.get(original, row.get("번역", "")).strip()
            if not korean:
                continue
            match = re.search(rb"m[a-z]_[0-9]{4}", elf[off : off + 160])
            if match:
                out[match.group().decode("ascii")] = korean
    return out


TITLES = load_titles()


def _gim_image_and_palette(data):
    image_info = None
    palette = None
    for block in GU.gim_blocks(data):
        info = GU.gim_sub_info(data, block)
        if info.get("bpp") in (4, 8) and info.get("w", 0) > 4 and info.get("h", 0) > 4:
            if image_info is None:
                image_info = info
        else:
            try:
                palette = GU.gim_palette(data, info)
            except Exception:
                pass
    if image_info is None or palette is None:
        raise ValueError("지원하지 않는 GIM 구조")
    return image_info, palette


def _text_masks(text, width, height, max_font_px=42):
    """원본 384x48 틀 안에 맞는 본문/외곽선 안티앨리어스 마스크."""
    scale = 4
    max_w = (width - 6) * scale
    max_h = (height - 4) * scale
    chosen = None
    for px in range(max_font_px, 17, -1):
        font = ImageFont.truetype(FONT, px * scale)
        box = font.getbbox(text, stroke_width=2 * scale)
        if box[2] - box[0] <= max_w and box[3] - box[1] <= max_h:
            chosen = (font, box)
            break
    if chosen is None:
        font = ImageFont.truetype(FONT, 18 * scale)
        box = font.getbbox(text, stroke_width=2 * scale)
    else:
        font, box = chosen

    x = 3 * scale - box[0]
    y = ((height * scale - (box[3] - box[1])) // 2) - box[1]
    fill = Image.new("L", (width * scale, height * scale), 0)
    stroke = Image.new("L", fill.size, 0)
    ImageDraw.Draw(stroke).text(
        (x, y), text, font=font, fill=255, stroke_width=2 * scale, stroke_fill=255
    )
    ImageDraw.Draw(fill).text((x, y), text, font=font, fill=255)
    fill = fill.resize((width, height), Image.Resampling.LANCZOS)
    stroke = stroke.resize((width, height), Image.Resampling.LANCZOS)
    return fill, stroke


def patch(data, text, max_font_px=42):
    """한 장의 intro_*.gim을 투명 배경 + 주황 제목으로 다시 그린다."""
    info, palette = _gim_image_and_palette(data)
    raw = data[info["pix_start"] : info["pix_start"] + info["pix_len"]]
    linear = (
        GU.unswizzle(raw, info["rowbytes"], info["halign"])
        if info["order"] == 1
        else raw
    )
    grid = GU.read_indices(linear, info)
    for y in range(info["h"]):
        for x in range(info["w"]):
            grid[y][x] = 0

    fill, stroke = _text_masks(text, info["w"], info["h"], max_font_px)
    fp = fill.load()
    sp = stroke.load()
    for y in range(info["h"]):
        for x in range(info["w"]):
            fa = fp[x, y]
            sa = sp[x, y]
            if fa >= 12:
                # 원본 팔레트 8~15: 짙은 갈색 → 밝은 주황
                grid[y][x] = 8 + min(7, (fa * 8) // 256)
            elif sa >= 12:
                # 원본 팔레트 1~7: 투명 검정 → 불투명 갈색 외곽선
                grid[y][x] = 1 + min(6, (sa * 7) // 256)

    new_linear = GU.write_indices(grid, info)
    packed = (
        GU.swizzle(new_linear, info["rowbytes"], info["halign"])
        if info["order"] == 1
        else bytes(new_linear)
    )
    out = bytearray(data)
    out[info["pix_start"] : info["pix_start"] + info["pix_len"]] = packed
    return bytes(out), info, palette, grid


def preview(mission="me_0050"):
    bundle = next(x for x in G.fsets() if x["name"] == mission + "_o")
    entry = next(
        x
        for x in G.fset_entries(bundle)
        if x["name"].endswith("intro_" + mission + ".gim")
    )
    patched, info, palette, grid = patch(G.fset_read(bundle, entry), TITLES[mission])
    image = Image.new("RGBA", (info["w"], info["h"]))
    pixels = image.load()
    for y in range(info["h"]):
        for x in range(info["w"]):
            pixels[x, y] = tuple(palette[grid[y][x]])
    path = os.path.join(BASE, "situation_inspect", "intro_" + mission + "_ko.png")
    image.save(path)
    return path, len(G.raic_compress(patched)), entry["csize"]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    path, compressed, limit = preview()
    print(f"제목 매핑: {len(TITLES)}종")
    print(f"미리보기: {path}")
    print(f"me_0050 압축: {compressed}/{limit} {'OK' if compressed <= limit else 'OVER'}")
