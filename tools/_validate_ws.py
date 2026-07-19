# -*- coding: utf-8 -*-
"""워크시트 번역 vs csv_src 원문: {C=},{CE},%s,%d,\\n 개수 일치 검증."""
import sys, io, os, csv, glob, re
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
BASE=os.path.dirname(os.path.abspath(__file__))
def codes(s):
    return (len(re.findall(r"\{C=[0-9a-fA-F]+\}",s)), s.count("{CE}"),
            s.count("%s"), s.count("%d"), s.count("\\n"))
bad=0; total=0
for wp in glob.glob(os.path.join(BASE,"translate","*.csv")):
    rows=list(csv.reader(io.open(wp,encoding="utf-8-sig",newline="")))
    if not rows or rows[0][:1]!=["key"]: continue
    name=os.path.basename(wp)
    for r in rows[1:]:
        if len(r)<5 or not r[4].strip(): continue
        total+=1
        jp,ko=r[3],r[4]
        if codes(jp)!=codes(ko):
            bad+=1
            if bad<=25: print(f"[{name}] {r[0]}\n  JP{codes(jp)}: {jp[:40]}\n  KO{codes(ko)}: {ko[:40]}")
print(f"\n검증 {total}셀, 불일치 {bad}")
