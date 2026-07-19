# -*- coding: utf-8 -*-
"""전체 워크시트 반영 타당성 측정: 채움상태, 총 음절, donor 가용, 대상 CSV 사본수."""
import sys, io, os, csv, glob, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gaslib as G

WS=glob.glob(os.path.join(G.BASE,"translate","*.csv"))
allsyl=set(); percsv={}
for wp in WS:
    rows=list(csv.reader(io.open(wp,encoding="utf-8-sig",newline="")))
    if not rows or rows[0][:1]!=["key"]: continue
    base=rows[1][0].split("|")[0].split("/")[-1] if len(rows)>1 else "?"
    filled=0; syl=set()
    for r in rows[1:]:
        ko=r[4] if len(r)>4 else ""
        if ko.strip(): filled+=1
        syl|={c for c in ko if "가"<=c<="힣"}
    allsyl|=syl
    percsv[base]=(len(rows)-1, filled, len(syl))
print("워크시트별 (총셀, 채움, 고유음절):")
for b,(t,f,s) in sorted(percsv.items()): print(f"  {b:24s} {t:4d} {f:4d} {s:4d}")
print(f"\n전체 고유 한글 음절: {len(allsyl)}")

# donor 가용량(charset 미사용 한자, 앞 1/3 제외)
cs=G.charset()
def dec(c):
    try: return struct.pack(">H",c).decode("cp932")
    except: return None
used=set()
for root,_,fs in os.walk(os.path.join(G.BASE,"csv_src")):
    for fn in fs:
        if fn.endswith(".csv"):
            try: used.update(io.open(os.path.join(root,fn),encoding="utf-8-sig").read())
            except: pass
donors=[ti for ti in range(len(cs)) if (lambda ch: ch and ch not in used and "一"<=ch<="鿿")(dec(cs[ti]))]
print(f"donor 후보(미사용 한자): {len(donors)}, 앞1/3제외 후: {len(donors)-len(donors)//3}")
print(f"글리프 여유(6976-6953): 폰트 슬롯은 charset 범위(6953) 내여야 함")

# 대상 CSV 사본 수(fileset)
print("\nfileset 내 대상 CSV 사본:")
bases=set(percsv.keys())
cnt={}
for s in G.fsets():
    if s["nfiles"]==0: continue
    try: ents=G.fset_entries(s)
    except: continue
    for e in ents:
        bn=e["name"].split("/")[-1]
        if bn in bases: cnt[bn]=cnt.get(bn,0)+1
for b in sorted(bases): print(f"  {b:24s} x{cnt.get(b,0)}")
