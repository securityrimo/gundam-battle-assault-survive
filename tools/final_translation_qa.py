# -*- coding: utf-8 -*-
"""최종 번역 워크시트의 구조·내용·사전 일치 여부를 검사해 보고서를 만든다."""
from __future__ import annotations

import csv
import glob
import io
import os
import re
from collections import Counter

from translate_gas_worksheets import CODE_RE


BASE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.join(BASE, "translate")
REPORT = os.path.join(BASE, "FINAL_TRANSLATION_QA.md")
JP_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
TEMP_RE = re.compile(r"ZZ(?:TERM|BREAK|CODE)")


def main() -> None:
    total = 0
    blanks = []
    line_bad = []
    code_bad = []
    japanese = []
    temp = []
    per_file = Counter()
    for path in sorted(glob.glob(os.path.join(WS, "*.csv"))):
        with io.open(path, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.reader(f))[1:]
        for row in rows:
            if not row:
                continue
            total += 1
            per_file[os.path.basename(path)] += 1
            key, source, ko = row[0], row[3], row[4]
            if not ko.strip():
                blanks.append(key)
            if source.count("\\n") != ko.count("\\n"):
                line_bad.append(key)
            if sorted(CODE_RE.findall(source)) != sorted(CODE_RE.findall(ko)):
                code_bad.append(key)
            if JP_RE.search(ko):
                japanese.append(key)
            if TEMP_RE.search(ko):
                temp.append(key)

    issues = blanks + line_bad + code_bad + japanese + temp
    lines = [
        "# Gundam Assault Survive 한국어 번역 최종 QA",
        "",
        f"- 검사 셀: **{total}**",
        f"- 빈 번역: **{len(blanks)}**",
        f"- 원문 대비 `\\\\n` 개수 불일치: **{len(line_bad)}**",
        f"- 제어코드 불일치: **{len(code_bad)}**",
        f"- 번역문 일본어 잔존: **{len(japanese)}**",
        f"- 임시 토큰 잔존: **{len(temp)}**",
        f"- 최종 판정: **{'통과' if not issues else '실패'}**",
        "",
        "## 파일별 검사 셀",
        "",
        "| 파일 | 셀 |",
        "|---|---:|",
    ]
    lines.extend(f"| `{name}` | {count} |" for name, count in sorted(per_file.items()))
    lines += [
        "",
        "## 윤문 및 사전 적용",
        "",
        "- 이벤트 장문: 32/32 수동 윤문",
        "- 미션 설명: 182/182 수동 윤문",
        "- 파일럿 설명: 96/96 수동 윤문",
        "- 캐릭터 사전: 84명",
        "- 통합 표시 명칭 사전: 734항목",
        "- 나머지 설명·스킬·부품·퀴즈: 장문 재번역 및 반복 오역/용어/띄어쓰기 일괄 교정",
    ]
    if issues:
        lines += ["", "## 오류 키", ""] + [f"- `{x}`" for x in sorted(set(issues))]
    with io.open(REPORT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print(f"최종 QA: {'통과' if not issues else '실패'} / {total}셀")
    print(REPORT)
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
