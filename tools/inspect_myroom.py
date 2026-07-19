# -*- coding: utf-8 -*-
"""메인 메뉴 myroom_00.ark의 실제 TXOS 크롭 좌표를 시각화한다."""
from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw

import gaslib as G
from inspect_vs import decode_gim, parse_texs, parse_txos


BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "myroom_inspect")


def main():
    os.makedirs(OUT, exist_ok=True)
    bundle = next(x for x in G.fsets() if x["name"] == "main_menu")
    entries = G.fset_entries(bundle)
    decoded = {}
    for entry in entries:
        base = entry["name"].split("/")[-1]
        data = G.fset_read(bundle, entry)
        if base.endswith(".gim"):
            decoded[base] = decode_gim(data)
        elif base == "myroom_00.ark":
            ark = data
    names = parse_texs(ark)
    rects = parse_txos(ark)
    print("textures:", names)
    with open(os.path.join(OUT, "myroom_00.txos.txt"), "w", encoding="utf-8") as f:
        for row in rects:
            f.write(
                f"{row['id']:03d} tex={row['texture']} "
                f"x={row['x']} y={row['y']} w={row['w']} h={row['h']}\n"
            )
    for texture_id, name in enumerate(names):
        image = decoded[name]
        canvas = Image.new("RGBA", image.size, (42, 48, 64, 255))
        canvas.alpha_composite(image)
        draw = ImageDraw.Draw(canvas)
        for row in rects:
            if row["texture"] != texture_id:
                continue
            x, y, w, h = row["x"], row["y"], row["w"], row["h"]
            draw.rectangle((x, y, x + w - 1, y + h - 1), outline=(255, 60, 60, 255))
            draw.text((x + 1, y), str(row["id"]), fill=(255, 255, 0, 255))
        canvas.resize(
            (canvas.width * 4, canvas.height * 4), Image.Resampling.NEAREST
        ).save(os.path.join(OUT, name + ".grid.png"))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
