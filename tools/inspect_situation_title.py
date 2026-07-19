# -*- coding: utf-8 -*-
"""시추에이션 시작 타이틀의 GIM과 intro_start_vs.ark 구조를 추출한다."""
from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw

import gaslib as G
from inspect_vs import decode_gim, parse_texs, parse_txos


BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "situation_inspect")
BUNDLE = "mv_0000_o"


def main():
    os.makedirs(OUT, exist_ok=True)
    bundle = next(x for x in G.fsets() if x["name"] == BUNDLE)
    decoded = {}
    ark = None
    for entry in G.fset_entries(bundle):
        base = entry["name"].split("/")[-1]
        data = G.fset_read(bundle, entry)
        if base.startswith("2d_fude_") and base.endswith(".gim"):
            image = decode_gim(data)
            decoded[base] = image
            bg = Image.new("RGBA", image.size, (42, 48, 64, 255))
            bg.alpha_composite(image)
            bg.resize((image.width * 3, image.height * 3), Image.Resampling.NEAREST).save(
                os.path.join(OUT, base + ".png")
            )
            print(base, image.size, entry["csize"])
        elif base == "intro_start_vs.ark":
            ark = data
            with open(os.path.join(OUT, base), "wb") as f:
                f.write(data)
    names = parse_texs(ark)
    rects = parse_txos(ark)
    print("textures:", names)
    with open(os.path.join(OUT, "intro_start_vs.txos.txt"), "w", encoding="utf-8") as f:
        for row in rects:
            f.write(
                f"{row['id']:03d} tex={row['texture']} "
                f"x={row['x']} y={row['y']} w={row['w']} h={row['h']}\n"
            )
    for texture_id, name in enumerate(names):
        if name not in decoded:
            continue
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
            (canvas.width * 3, canvas.height * 3), Image.Resampling.NEAREST
        ).save(os.path.join(OUT, name + ".grid.png"))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
