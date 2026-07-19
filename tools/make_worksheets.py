# -*- coding: utf-8 -*-
"""번역 워크시트 생성기.
csv_src/ 의 게임 CSV에서 '번역 대상 열'만 뽑아, 지피티가 채우기 쉬운 워크시트를 만든다.
- 헤더 행(row0)은 제외(컬럼명 자체는 화면표시 아님).
- 각 셀에 안정 키(파일|행|열)를 부여 → apply 단계에서 결정론적 재조립.
- ID/수치 열은 애초에 뽑지 않으므로 훼손 불가.
출력: work_gas/translate/<name>.csv  컬럼 = key, kind, note, 원문, 번역
"""
import csv, io, os, re

SRC  = r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gas\csv_src"
OUT  = r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gas\translate"
os.makedirs(OUT, exist_ok=True)

# 파일별 번역 대상 열 인덱스 (직접 확인해 확정)
CONFIG = {
    "data/menu/text/inst_ms.csv":        [1, 2],
    "data/menu/text/inst_pilot.csv":     [1, 2],
    "data/menu/text/inst_operator.csv":  [1, 2],
    "data/menu/text/inst_sfs.csv":       [1, 2],
    "data/menu/text/inst_mission.csv":   [0, 2],   # col1=ME_xxxx ID
    "data/menu/text/inst_parts.csv":     [0, 2],   # col1=ID
    "data/menu/text/inst_skill.csv":     [0, 1, 2, 3, 4, 5],
    "data/menu/main_menu/main_menu_text.csv": [2], # col1=개발용 라벨 제외
    "data/menu/mission/event/event.csv": [8, 9],   # 텍스트1,2
    "data/ark/custom_pilot/charamake_data.csv": [1, 2],  # quiz, ans
}

CODE_RE = re.compile(r"\{[^}]*\}|%[sd]")
jp = re.compile(r"[぀-ゟ゠-ヿ一-鿿]")

def note_for(s):
    n = []
    codes = CODE_RE.findall(s)
    if codes:
        n.append("CODE:" + "".join(sorted(set(codes))))
    nl = s.count("\\n")
    if nl:
        n.append(f"줄={nl+1}")
    return " ".join(n)

total = 0
summary = []
for rel, cols in CONFIG.items():
    path = os.path.join(SRC, rel.replace("/", os.sep))
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    header = rows[0] if rows else []
    name = os.path.splitext(os.path.basename(rel))[0]
    outp = os.path.join(OUT, name + ".csv")
    cnt = 0
    with io.open(outp, "w", encoding="utf-8-sig", newline="") as w:
        wr = csv.writer(w)
        wr.writerow(["key", "kind", "note", "원문", "번역"])
        for ri in range(1, len(rows)):        # 헤더 제외
            r = rows[ri]
            for ci in cols:
                if ci >= len(r):
                    continue
                cell = r[ci]
                if not cell.strip():
                    continue
                if not jp.search(cell):        # 일본어 없으면(순수 숫자/기호) 건너뜀
                    continue
                kind = header[ci] if ci < len(header) else f"col{ci}"
                key = f"{rel}|{ri}|{ci}"
                wr.writerow([key, kind, note_for(cell), cell, ""])
                cnt += 1
    total += cnt
    summary.append((name, cnt, outp))

print("워크시트 생성 완료:")
for name, cnt, outp in summary:
    print(f"  {name:22s} {cnt:5d} 셀")
print(f"  {'합계':22s} {total:5d} 셀")
print(f"\n출력 폴더: {OUT}")
