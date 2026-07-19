# -*- coding: utf-8 -*-
"""번역 워크시트를 게임 CSV에 되돌려 넣는다(재조립).
- translate/*.csv 의 '번역' 열을 읽어 key(파일|행|열)로 원본 셀을 덮어씀.
- 검증: 제어코드({...},%s,%d) 집합이 원문과 번역에서 일치하는지, \\n 개수 동일한지.
  → 지피티가 코드를 깨먹거나 줄 수를 바꾸면 경고.
- 출력: csv_ko_utf8/ (사람 검수용 UTF-8). ※게임 주입용 SJIS-슬롯 인코딩은 별도 단계(폰트 PoC 확정 후).
"""
import csv, io, os, re, glob

SRC   = r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gas\csv_src"
WS    = r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gas\translate"
OUT   = r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gas\csv_ko_utf8"
CODE_RE = re.compile(r"\{[^}]*\}|%[sd]")

def codeset(s):
    return sorted(CODE_RE.findall(s))

# 워크시트 로드 → key -> (원문, 번역)
trans = {}
warns = []
for wp in glob.glob(os.path.join(WS, "*.csv")):
    with io.open(wp, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            ko = row["번역"].strip()
            if not ko:
                continue
            key, ja = row["key"], row["원문"]
            # 검증
            if codeset(ja) != codeset(ko):
                warns.append(f"[코드불일치] {key}\n   원문코드={codeset(ja)}\n   번역코드={codeset(ko)}")
            if ja.count("\\n") != ko.count("\\n"):
                warns.append(f"[줄수변경] {key}  원문\\n={ja.count(chr(92)+'n')} 번역\\n={ko.count(chr(92)+'n')}")
            trans[key] = ko

if not trans:
    print("번역된 셀이 없습니다. translate/*.csv 의 '번역' 열을 채운 뒤 다시 실행하세요.")
    raise SystemExit(0)

# 파일별로 적용
by_file = {}
for key, ko in trans.items():
    rel, ri, ci = key.rsplit("|", 2)
    by_file.setdefault(rel, []).append((int(ri), int(ci), ko))

applied = 0
for rel, cells in by_file.items():
    path = os.path.join(SRC, rel.replace("/", os.sep))
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    for ri, ci, ko in cells:
        rows[ri][ci] = ko
        applied += 1
    outp = os.path.join(OUT, rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    with io.open(outp, "w", encoding="utf-8-sig", newline="") as w:
        csv.writer(w).writerows(rows)

print(f"적용 셀 {applied}개 → {OUT}")
if warns:
    print(f"\n!! 경고 {len(warns)}건 (번역 검토 필요):")
    for w in warns[:40]:
        print("  " + w)
else:
    print("제어코드/줄수 검증 통과.")
