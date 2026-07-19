# -*- coding: utf-8 -*-
"""전체 워크시트의 반복 기계번역 오류와 표기/띄어쓰기를 최종 교정한다."""
from __future__ import annotations

import csv
import glob
import io
import os
import re


BASE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.join(BASE, "translate")

GLOBAL = [
    ("일년 전쟁", "1년 전쟁"),
    ("일년전쟁", "1년 전쟁"),
    ("모빌슈트", "모빌 슈트"),
    ("우군기", "아군기"),
    ("우군", "아군"),
    ("료기", "동료기"),
    ("자석 코팅", "마그넷 코팅"),
    ("전천 주위 모니터", "전방위 모니터"),
    ("사용자 정의 부품", "커스텀 파츠"),
    ("드문MS조종", "탁월한 MS 조종"),
    ("드문 MS조종", "탁월한 MS 조종"),
    ("드문 MS 조종", "탁월한 MS 조종"),
    ("기체관절부", "기체 관절부"),
    ("기체구동부", "기체 구동부"),
    ("운동성능", "운동 성능"),
    ("내구성능", "내구 성능"),
    ("메가 입자포", "메가입자포"),
    ("대파해 버렸다", "대파됐다"),
    ("베풀어진", "적용된"),
    ("발휘하는 것이 가능", "발휘할 수 있다"),
    ("끼워 쏘다", "협공한다"),
    ("위험을 인지하고 도움으로 향한다", "위험을 무릅쓰고 구하러 간다"),
    ("동료기의 일은 포기한다", "동료기는 포기한다"),
    ("목소리를 내지 않고 무시한다", "말을 걸지 않고 무시한다"),
    ("굳이 힘든 일을 말해", "일부러 엄하게 말한다"),
    ("알아내는 일이다", "찾아내라"),
    ("원호를 향해", "엄호하러 가라"),
    ("장착하지 않습니다", "장착하지 않는다"),
]

SOURCE_RULES = [
    ("ジム", "체육관", "짐"),
    ("兵装", "병장", "무장"),
    ("空間戦闘", "공간 전투", "우주 전투"),
    ("グレネードランチャー", "수류탄 발사기", "그레네이드 런처"),
    ("試作したＮＴ", "시작한 NT", "시험 제작한 NT"),
    ("機体背部", "기체 등의", "기체 후면의"),
    ("流用された", "유용된", "재활용된"),
    ("一年戦争時", "1년 전쟁시", "1년 전쟁 당시"),
    ("正に一年戦争時", "정확히 1년 전쟁 당시", "1년 전쟁 당시"),
    ("その分機体", "그 분기체", "그만큼 기체"),
    ("補充部品は常に不足がち", "보충 부품은 항상 부족해 경향이 있고", "보급 부품이 늘 부족했고"),
    ("実弾系の兵装", "실탄계의 무장이 되고 있다", "실탄 계열 무장을 사용한다"),
]


def main() -> None:
    changed_cells = 0
    replacements = 0
    for path in sorted(glob.glob(os.path.join(WS, "*.csv"))):
        with io.open(path, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.reader(f))
        touched = False
        for row in rows[1:]:
            if not row:
                continue
            before = row[4]
            text = before
            for old, new in GLOBAL:
                n = text.count(old)
                if n:
                    text = text.replace(old, new)
                    replacements += n
            for marker, old, new in SOURCE_RULES:
                if marker in row[3] and old in text:
                    replacements += text.count(old)
                    text = text.replace(old, new)
            text = re.sub(r"(?<=[A-Za-z0-9가-힣])MS(?=[가-힣])", "MS ", text)
            text = re.sub(r"(?<=[가-힣])MS", r" MS", text)
            text = re.sub(r"MS(?=[가-힣])", "MS ", text)
            text = re.sub(r"([+＋]\d+)(?=[가-힣A-Za-z])", r"\1 ", text)
            text = re.sub(r" {2,}", " ", text)
            if text != before:
                row[4] = text
                changed_cells += 1
                touched = True
        if touched:
            tmp = path + ".tmp"
            with io.open(tmp, "w", encoding="utf-8-sig", newline="") as f:
                csv.writer(f).writerows(rows)
            os.replace(tmp, path)
    print(f"최종 반복 오역 교정: {changed_cells}셀 / {replacements}건")


if __name__ == "__main__":
    main()
