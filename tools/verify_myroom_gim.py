# -*- coding: utf-8 -*-
"""빌드 ISO의 메인 메뉴 대시보드 GIM을 기대 결과와 대조한다."""
from __future__ import annotations

import os
import sys

import fileset_repack as R
import gaslib as G
import patch_myroom_gim as PMR


BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
ORIG_ISO = os.path.join(ROOT, "Gundam Assault Survive (Japan).iso")
KR_ISO = os.path.join(ROOT, "Gundam Assault Survive (Korean_PoC).iso")
TARGET = "data/menu/main_menu/2d_myroom_01.gim"


def unpack(data):
    return G.raic_decompress(data) if data[:4] == b" 3;1" else data


def stored(fs, bundle, entry):
    start = bundle["doff"] + entry["off"]
    return bytes(fs.data[start:start + entry["csize"]])


def main():
    original = R.Fileset(ORIG_ISO)
    korean = R.Fileset(KR_ISO)
    ob = next(b for b in original.bundles if b["name"] == "main_menu")
    kb = next(b for b in korean.bundles if b["name"] == "main_menu")
    of = next(f for f in original.parse_bundle_files(ob)["files"] if f["name"] == TARGET)
    kf = next(f for f in korean.parse_bundle_files(kb)["files"] if f["name"] == TARGET)
    expected, _, _, _ = PMR.patch(unpack(stored(original, ob, of)))
    actual = unpack(stored(korean, kb, kf))
    if actual != expected:
        raise SystemExit("메인 메뉴 대시보드 GIM 검증 실패")
    print(f"메인 메뉴 대시보드 GIM 검증 통과: slot={of['csize']}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
