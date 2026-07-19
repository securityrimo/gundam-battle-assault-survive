# -*- coding: utf-8 -*-
"""빌드 ISO의 VS 배틀 GIM을 원본에서 계산한 기대 결과와 대조한다."""
from __future__ import annotations

import os
import sys

import fileset_repack as R
import gaslib as G
import patch_vs as PVS


BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
ORIG_ISO = os.path.join(ROOT, "Gundam Assault Survive (Japan).iso")
KR_ISO = os.path.join(ROOT, "Gundam Assault Survive (Korean_PoC).iso")


def stored(fs, bundle, entry):
    start = bundle["doff"] + entry["off"]
    return bytes(fs.data[start:start + entry["csize"]])


def unpack(data):
    return G.raic_decompress(data) if data[:4] == b" 3;1" else data


def main():
    original = R.Fileset(ORIG_ISO)
    korean = R.Fileset(KR_ISO)
    korean_bundles = {b["name"]: b for b in korean.bundles}
    checked = 0
    failures = []
    for ob in original.bundles:
        kb = korean_bundles.get(ob["name"])
        if kb is None:
            continue
        oi = original.parse_bundle_files(ob)
        ki = korean.parse_bundle_files(kb)
        if not oi or not ki:
            continue
        kfiles = {f["name"]: f for f in ki["files"]}
        for of in oi["files"]:
            base = of["name"].split("/")[-1]
            if base not in PVS.TARGETS:
                continue
            kf = kfiles.get(of["name"])
            if kf is None:
                failures.append((ob["name"], of["name"], "누락"))
                continue
            patcher, labels = PVS.TARGETS[base]
            expected, _, _, _ = patcher(unpack(stored(original, ob, of)), labels)
            actual = unpack(stored(korean, kb, kf))
            checked += 1
            ok = actual == expected
            print(f"{ob['name']}/{base}: {'OK' if ok else 'FAIL'}")
            if not ok:
                failures.append((ob["name"], of["name"], "패치 결과 불일치"))
    if checked == 0:
        raise RuntimeError("검사할 VS GIM을 찾지 못했습니다.")
    if failures:
        for failure in failures:
            print("FAIL:", *failure)
        raise SystemExit(1)
    print(f"VS GIM 정적검증 통과: {checked}사본")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
