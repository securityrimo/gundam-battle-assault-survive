# -*- coding: utf-8 -*-
"""빌드된 한국어 ISO의 샵 GIM 4종을 원본별 기대 결과와 대조한다."""
from __future__ import annotations

import os
import sys

import fileset_repack as R
import gaslib as G
import patch_shop as PS


BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
ORIG_ISO = os.path.join(ROOT, "Gundam Assault Survive (Japan).iso")
KR_ISO = os.path.join(ROOT, "Gundam Assault Survive (Korean_PoC).iso")


def stored(fs: R.Fileset, bundle, entry) -> bytes:
    start = bundle["doff"] + entry["off"]
    return bytes(fs.data[start:start + entry["csize"]])


def unpack(data: bytes) -> bytes:
    return G.raic_decompress(data) if data[:4] == b" 3;1" else data


def main() -> None:
    orig = R.Fileset(ORIG_ISO)
    kr = R.Fileset(KR_ISO)
    kr_bundles = {b["name"]: b for b in kr.bundles}
    checked = 0
    failures = []

    for ob in orig.bundles:
        kb = kr_bundles.get(ob["name"])
        if kb is None:
            continue
        oi = orig.parse_bundle_files(ob)
        ki = kr.parse_bundle_files(kb)
        if not oi or not ki:
            continue
        kfiles = {f["name"]: f for f in ki["files"]}
        for of in oi["files"]:
            base = of["name"].split("/")[-1]
            if base not in PS.TARGETS:
                continue
            kf = kfiles.get(of["name"])
            if kf is None:
                failures.append((ob["name"], of["name"], "한국어 ISO에서 누락"))
                continue
            patcher, labels = PS.TARGETS[base]
            source = unpack(stored(orig, ob, of))
            expected, _, _, _ = patcher(source, labels)
            actual = unpack(stored(kr, kb, kf))
            checked += 1
            if actual != expected:
                failures.append((ob["name"], of["name"], "패치 결과 불일치"))
            print(
                f"{base}: bundle={ob['name']} "
                f"slot={of['csize']} actual={kf['csize']} "
                f"{'OK' if actual == expected else 'FAIL'}"
            )

    if checked == 0:
        raise RuntimeError("검사할 샵 GIM을 찾지 못했습니다.")
    if failures:
        for item in failures:
            print("FAIL:", *item)
        raise SystemExit(1)
    print(f"샵 GIM 정적검증 통과: {checked}사본")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
