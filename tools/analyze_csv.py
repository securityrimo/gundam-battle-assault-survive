# -*- coding: utf-8 -*-
"""추출된 CSV 전수 분석: 컬럼 구조, 번역 대상 열, 제어코드 패턴, 최장 라인 폭."""
import csv, io, os, re, glob

SRC = r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gas\csv_src"
CODE_RE = re.compile(r"\{[^}]*\}|%[sd]|\\n")

def analyze(path):
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    rel = os.path.relpath(path, SRC).replace("\\","/")
    # 각 열별로 일본어(가나/한자) 포함 여부 카운트 → 번역 대상 열 추정
    ncol = max((len(r) for r in rows), default=0)
    jp = re.compile(r"[぀-ゟ゠-ヿ一-鿿]")
    col_jp = [0]*ncol
    col_codes = set()
    max_seg = 0     # \n 로 분할했을 때 최장 세그먼트 문자수(텍스트 박스 폭 추정)
    trans_cells = 0
    for r in rows:
        for ci,cell in enumerate(r):
            if jp.search(cell):
                col_jp[ci]+=1
            for m in CODE_RE.findall(cell):
                col_codes.add(m if not m.startswith("{C=") else "{C=......}")
            for seg in cell.split("\\n"):
                # 제어코드 제거 후 폭
                clean = CODE_RE.sub("", seg)
                if jp.search(cell):
                    max_seg = max(max_seg, len(clean))
    # 번역 대상 열 = 일본어가 가장 많은 열들
    tgt = [i for i,c in enumerate(col_jp) if c>0]
    for r in rows[1:]:
        for ci in tgt:
            if ci < len(r) and jp.search(r[ci]):
                trans_cells += 1
    return rel, len(rows), ncol, col_jp, tgt, trans_cells, max_seg, sorted(col_codes)

files = sorted(glob.glob(os.path.join(SRC, "**", "*.csv"), recursive=True))
total_cells = 0
print(f"{'file':42s} rows col  번역열  셀수  최장폭  제어코드")
print("-"*110)
for p in files:
    rel,nrow,ncol,col_jp,tgt,tc,mx,codes = analyze(p)
    total_cells += tc
    codes_s = " ".join(codes) if codes else "-"
    print(f"{rel:42s} {nrow:4d} {ncol:3d}  {str(tgt):8s} {tc:4d}  {mx:4d}  {codes_s}")
print("-"*110)
print(f"번역 대상 셀 총합: {total_cells:,}개")
