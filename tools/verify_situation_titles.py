# -*- coding: utf-8 -*-
"""EBOOT 시추에이션명 181종의 번역/슬롯/ISO 기록 상태를 검증한다."""
from __future__ import annotations

import csv
import io
import json
import os
import struct
import sys

import build_kr as B
import patch_menu as PM


BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
ISO = os.path.join(ROOT, "Gundam Assault Survive (Korean_PoC).iso")
CSV = os.path.join(BASE, "translate", "eboot_ui.csv")
MAP = os.path.join(BASE, "kr_map_stable.json")
SHORT = os.path.join(BASE, "eboot_ui_short.json")
START, END = 3064000, 3089000


def main():
    kr = {ch: tuple(value) for ch, value in json.load(io.open(MAP, encoding="utf-8")).items()}
    short = {
        jp: B.sanitize(ko)
        for jp, ko in json.load(io.open(SHORT, encoding="utf-8")).items()
    }
    rows = []
    with io.open(CSV, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            off = int(row["key"].split("|")[1])
            if START <= off < END:
                rows.append((off, int(row["slot"]), row["원문"], B.sanitize(row["번역"].strip())))
    if len(rows) != 181:
        raise SystemExit(f"시추에이션명 개수 불일치: {len(rows)} != 181")
    blank = [jp for _, _, jp, ko in rows if not ko]
    if blank:
        raise SystemExit("미번역 시추에이션명: " + ", ".join(blank))
    failures = []
    with open(ISO, "rb") as f:
        for off, slot, jp, ko in rows:
            ko = short.get(jp, ko)
            encoded = PM.encode_text(ko, kr)
            if len(encoded) > slot:
                ko = ko.replace("　", "").replace(" ", "")
                encoded = PM.encode_text(ko, kr)
            if len(encoded) > slot:
                failures.append((jp, "슬롯 초과", len(encoded), slot))
                continue
            f.seek(B.EBOOT_LBA * 2048 + off)
            actual = f.read(slot)
            expected = encoded + b"\0" * (slot - len(encoded))
            if actual != expected:
                failures.append((jp, "ISO 불일치", off, slot))
    if failures:
        for failure in failures:
            print("FAIL:", failure)
        raise SystemExit(1)
    print(f"시추에이션명 검증 통과: {len(rows)}/181")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
