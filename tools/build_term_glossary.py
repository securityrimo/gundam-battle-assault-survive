# -*- coding: utf-8 -*-
"""기체·미션·스킬·부품 등 표시 명칭을 표준화하고 통합 사전을 만든다."""
from __future__ import annotations

import csv
import glob
import io
import os
import re


BASE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.join(BASE, "translate")
OUT = os.path.join(BASE, "TERM_GLOSSARY.csv")
NAME_KINDS = {"名前", "ミッション名", "スキル名", "パーツ名"}

OVERRIDES = {
    "ゼーゴック": "제고크",
    "オッゴ": "옥고",
    "ジ・Ｏ": "디 오",
    "リ・ガズィ": "리 가지",
    "ジェガンＡ": "제간 A",
    "Ｇキャノン": "G 캐논",
    "プロトジン": "프로토 진",
    "ラゴゥ": "라고우",
    "スローネアイン": "스로네 아인",
    "スローネツヴァイ": "스로네 츠바이",
    "スローネドライ": "스로네 드라이",
    "イナクトカスタム・アグリッサ型": "이낙트 커스텀 아그리사형",
    "アグリッサ": "아그리사",
    "アルヴァアロン": "알바아론",
    "Ｇブル": "G불",
    "ビグラング": "비그 랑",
    "α・アジール": "α 아질",
    "Ｍ１アストレイ": "M1 아스트레이",
    "ＧＮフラッグ": "GN 플래그",
    "ＧＮアームズ（エクシア）": "GN 암즈(엑시아)",
    "ＧＮアームズ（デュナメス）": "GN 암즈(듀나메스)",
    "Ｖ２ガンダム（ＡＢ仕様）": "V2 건담(어설트 버스터)",
}


def normalize(text: str) -> str:
    text = text.strip().replace("・", " ")
    text = text.replace("（", "(").replace("）", ")")
    text = re.sub(r"\s+\(", "(", text)
    text = re.sub(r" {2,}", " ", text)
    return text


def main() -> None:
    glossary = []
    changed = 0
    for path in sorted(glob.glob(os.path.join(WS, "*.csv"))):
        with io.open(path, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.reader(f))
        touched = False
        for row in rows[1:]:
            if not row or row[1] not in NAME_KINDS:
                continue
            standard = OVERRIDES.get(row[3].strip(), normalize(row[4]))
            if row[4] != standard:
                row[4] = standard
                changed += 1
                touched = True
            glossary.append([
                os.path.basename(path), row[0], row[1], row[3], standard, "표준화 완료"
            ])
        if touched:
            tmp = path + ".tmp"
            with io.open(tmp, "w", encoding="utf-8-sig", newline="") as f:
                csv.writer(f).writerows(rows)
            os.replace(tmp, path)

    with io.open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["file", "key", "kind", "original_jp", "standard_ko", "status"])
        writer.writerows(glossary)
    print(f"표시 명칭 교정: {changed}셀")
    print(f"통합 용어 사전: {len(glossary)}항목 -> {OUT}")


if __name__ == "__main__":
    main()
