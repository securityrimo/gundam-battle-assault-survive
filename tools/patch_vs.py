# -*- coding: utf-8 -*-
"""VS 배틀 메뉴의 조합형 GIM 문자 아틀라스를 한글화한다.

taisen_01/02는 작은 문자 조각을 이어 붙여 모드명과 REGULATION 표를
구성한다. 반드시 ARK의 TXOS 크롭 경계 안에서만 다시 그린다.
"""
from __future__ import annotations

import io
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gaslib as G
from patch_shop import patch_alpha


# taisen_0.ark TXOS 20~47의 정확한 크롭 좌표.
LABELS_01 = [
    ("대전", 76, 1, 101, 14),
    ("점수", 103, 1, 128, 15),
    ("컨테이너 쟁탈전", 1, 16, 81, 29),
    ("격추수", 83, 16, 120, 29),
    ("소대전", 1, 30, 38, 43),
    ("제한", 40, 30, 64, 43),
    ("시간", 66, 30, 89, 43),
    ("점수", 91, 30, 115, 43),
    ("재", 116, 30, 128, 43),
    ("상한", 1, 44, 25, 57),
    ("값", 27, 44, 39, 57),
    ("맵", 41, 44, 76, 57),
    ("날씨", 78, 44, 102, 57),
    ("시각", 104, 44, 128, 57),
    ("출격", 1, 58, 25, 71),
    ("(지형)", 27, 58, 55, 71),
    ("(파일럿)", 57, 58, 121, 71),
    ("오퍼레이터", 1, 72, 63, 85),
    ("팀 내", 71, 72, 118, 85),
    # BGM(1,86~32,99)과 MS의 M이 겹쳐 있는 원본 재사용 구조.
    ("MS 랭크", 22, 86, 78, 99),
    ("튜닝", 80, 86, 127, 99),
    ("SP 게이지", 1, 100, 59, 113),
    ("I 필드", 61, 100, 127, 113),
    ("커스텀 파츠", 1, 114, 83, 127),
    ("자동", 85, 114, 118, 127),
]

# 같은 ARK의 TXOS 8~12. 규정표 공용 조각과 우하단 버튼.
LABELS_02 = [
    ("스킬", 1, 1, 37, 14),
    ("스페셜", 39, 1, 99, 14),
    ("결정", 101, 1, 125, 14),
    ("페이즈 시프트", 1, 15, 82, 28),
    ("초기 설정 복원", 1, 29, 85, 42),
]

# VS 편성/참가자 선택 화면의 일본어 조각(taisen_2.ark TXOS 27~33).
LABELS_03 = [
    ("로", 26, 83, 39, 97),
    ("파일럿", 42, 83, 100, 97),
    ("자동", 3, 98, 27, 112),
    ("선택", 31, 98, 57, 112),
    ("사용 안 함", 1, 113, 68, 127),
]


TARGETS = {
    "taisen_01.gim": (patch_alpha, LABELS_01),
    "taisen_02.gim": (patch_alpha, LABELS_02),
    "taisen_03.gim": (patch_alpha, LABELS_03),
}


def load(bundle_name, base_name):
    bundle = next(x for x in G.fsets() if x["name"] == bundle_name)
    entry = next(x for x in G.fset_entries(bundle) if x["name"].endswith(base_name))
    return G.fset_read(bundle, entry), entry["csize"]


def preview(base_name, patched, info, palette, grid):
    image = Image.new("RGBA", (info["w"], info["h"]))
    px = image.load()
    for y in range(info["h"]):
        for x in range(info["w"]):
            px[x, y] = tuple(palette[grid[y][x]])
    bg = Image.new("RGBA", image.size, (42, 48, 64, 255))
    bg.alpha_composite(image)
    bg.convert("RGB").resize(
        (image.width * 4, image.height * 4), Image.Resampling.NEAREST
    ).save(os.path.join(G.BASE, base_name.replace(".gim", "_vs_after.png")))


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    for name, (patcher, labels) in TARGETS.items():
        data, slot = load("scene_vsbattle_rule", name)
        patched, info, palette, grid = patcher(data, labels)
        packed = G.raic_compress(patched)
        print(f"{name}: {slot} -> {len(packed)} {'OK' if len(packed) <= slot else 'OVER'}")
        preview(name, patched, info, palette, grid)
