# -*- coding: utf-8 -*-
"""완성 ISO의 181개 시추에이션 시작 제목 GIM을 기대 결과와 대조한다."""
from __future__ import annotations

import os
import sys

import fileset_repack as R
import gaslib as G
import patch_situation_titles as PST


BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
ORIG_ISO = os.path.join(ROOT, "Gundam Assault Survive (Japan).iso")
KR_ISO = os.path.join(ROOT, "Gundam Assault Survive (Korean_PoC).iso")


def unpack(data):
    return G.raic_decompress(data) if data[:4] == b" 3;1" else data


def stored(fs, bundle, entry):
    start = bundle["doff"] + entry["off"]
    return bytes(fs.data[start : start + entry["csize"]])


def main():
    original = R.Fileset(ORIG_ISO)
    korean = R.Fileset(KR_ISO)
    obundles = {b["name"]: b for b in original.bundles}
    kbundles = {b["name"]: b for b in korean.bundles}
    checked = 0
    reduced = 0
    for mission, title in PST.TITLES.items():
        bundle_name = mission + "_o"
        ob = obundles[bundle_name]
        kb = kbundles[bundle_name]
        target = "intro_" + mission + ".gim"
        of = next(
            f for f in original.parse_bundle_files(ob)["files"] if f["name"].endswith(target)
        )
        kf = next(
            f for f in korean.parse_bundle_files(kb)["files"] if f["name"].endswith(target)
        )
        source = unpack(stored(original, ob, of))
        expected = None
        for font_px in (42, 40, 38, 36, 34, 32, 30, 28, 26, 24):
            trial, _, _, _ = PST.patch(source, title, font_px)
            if len(G.raic_compress(trial)) <= of["csize"]:
                expected = trial
                if font_px < 42:
                    reduced += 1
                break
        actual = unpack(stored(korean, kb, kf))
        if expected is None or actual != expected:
            raise SystemExit(f"시추에이션 제목 GIM 검증 실패: {mission}")
        checked += 1
    print(f"시추에이션 제목 GIM 검증 통과: {checked}/{len(PST.TITLES)} (축소 {reduced})")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
