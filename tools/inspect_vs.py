# -*- coding: utf-8 -*-
"""VS 배틀 UI GIM/ARK 구조를 원본 ISO에서 추출해 확인한다."""
from __future__ import annotations

import os
import struct
import sys

from PIL import Image, ImageDraw

import fileset_repack as R
import gaslib as G

sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gbu")
import gimutil as GU


BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
ISO = os.path.join(ROOT, "Gundam Assault Survive (Japan).iso")
OUT = os.path.join(BASE, "vs_inspect")


def stored(fs, bundle, entry):
    off = bundle["doff"] + entry["off"]
    return bytes(fs.data[off:off + entry["csize"]])


def unpack(data):
    return G.raic_decompress(data) if data[:4] == b" 3;1" else data


def decode_gim(data):
    img = pal = None
    for block in GU.gim_blocks(data):
        info = GU.gim_sub_info(data, block)
        if info["bpp"] in (4, 8) and info["w"] > 1 and info["h"] > 1 and img is None:
            img = info
        else:
            try:
                pal = GU.gim_palette(data, info)
            except Exception:
                pass
    if img is None:
        raise ValueError("image block not found")
    raw = data[img["pix_start"]:img["pix_start"] + img["pix_len"]]
    linear = GU.unswizzle(raw, img["rowbytes"], img["halign"]) if img["order"] == 1 else raw
    grid = GU.read_indices(linear, img)
    out = Image.new("RGBA", (img["w"], img["h"]))
    px = out.load()
    for y in range(img["h"]):
        for x in range(img["w"]):
            px[x, y] = tuple(pal[grid[y][x]])
    return out


def chunks(data):
    """ARK 내부의 4바이트 태그/크기 청크를 느슨하게 찾는다."""
    for tag in (b"TEXS", b"TXOS", b"LAYO"):
        start = 0
        while True:
            pos = data.find(tag, start)
            if pos < 0:
                break
            size = struct.unpack_from("<I", data, pos + 4)[0] if pos + 8 <= len(data) else 0
            yield tag.decode(), pos, size
            start = pos + 4


def parse_texs(data):
    pos = data.find(b"TEXS")
    count, stride, rel = struct.unpack_from("<3I", data, pos + 12)
    start = pos + 12 + rel
    names = []
    for i in range(count):
        raw = data[start + i * stride:start + (i + 1) * stride]
        names.append(raw.split(b"\0", 1)[0].decode("ascii"))
    return names


def parse_txos(data):
    pos = data.find(b"TXOS")
    count, stride, rel = struct.unpack_from("<3I", data, pos + 12)
    start = pos + 12 + rel
    rows = []
    for i in range(count):
        vals = struct.unpack_from("<12I", data, start + i * stride)
        rows.append({
            "id": i, "texture": vals[2], "x": vals[3], "y": vals[4],
            "w": vals[5], "h": vals[6], "raw": vals,
        })
    return rows


def save_rect_overlays(ark_name, data, decoded):
    names = parse_texs(data)
    rects = parse_txos(data)
    with open(os.path.join(OUT, ark_name + ".txos.txt"), "w", encoding="utf-8") as f:
        for row in rects:
            f.write(
                f"{row['id']:03d} tex={row['texture']} "
                f"x={row['x']} y={row['y']} w={row['w']} h={row['h']}\n"
            )
    for texture_id, gim_name in enumerate(names):
        source = decoded.get(gim_name)
        if source is None:
            continue
        canvas = Image.new("RGBA", source.size, (42, 48, 64, 255))
        canvas.alpha_composite(source)
        draw = ImageDraw.Draw(canvas)
        for row in rects:
            if row["texture"] != texture_id:
                continue
            x, y, w, h = row["x"], row["y"], row["w"], row["h"]
            draw.rectangle((x, y, x + w - 1, y + h - 1), outline=(255, 60, 60, 255))
            draw.text((x + 1, y), str(row["id"]), fill=(255, 255, 0, 255))
        canvas.resize(
            (canvas.width * 4, canvas.height * 4), Image.Resampling.NEAREST
        ).save(os.path.join(OUT, f"{ark_name}_{gim_name}_grid.png"))


def main():
    os.makedirs(OUT, exist_ok=True)
    fs = R.Fileset(ISO)
    bundle = next(b for b in fs.bundles if b["name"] == "scene_vsbattle_rule")
    info = fs.parse_bundle_files(bundle)
    decoded = {}
    arks = {}
    for entry in info["files"]:
        base = entry["name"].split("/")[-1]
        if not (base.startswith("taisen_") or base.startswith("2d_setng_") or base == "2d_hensei_00.gim"):
            continue
        raw = unpack(stored(fs, bundle, entry))
        with open(os.path.join(OUT, base), "wb") as f:
            f.write(raw)
        if base.endswith(".gim"):
            try:
                image = decode_gim(raw)
                decoded[base] = image
                bg = Image.new("RGBA", image.size, (42, 48, 64, 255))
                bg.alpha_composite(image)
                scale = 4
                bg.convert("RGB").resize(
                    (image.width * scale, image.height * scale), Image.Resampling.NEAREST
                ).save(os.path.join(OUT, base + ".png"))
                print(base, image.size, "slot", entry["csize"])
            except Exception as exc:
                print(base, "render failed:", exc)
        elif base.endswith(".ark"):
            arks[base] = raw
            print(base, "slot", entry["csize"], "usize", len(raw), list(chunks(raw)))
    for ark_name, data in arks.items():
        save_rect_overlays(ark_name, data, decoded)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
