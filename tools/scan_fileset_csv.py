# -*- coding: utf-8 -*-
"""fileset 전 CSV(1569)의 번역대상 일본어 셀 수 집계 + UI CSV 식별."""
import sys, io, os, csv, re
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gaslib as G
jp=re.compile(r"[぀-ゟ゠-ヿ一-鿿]")

# 이미 처리한 10개 basename(중복 스킵)
DONE={"inst_ms.csv","inst_mission.csv","inst_pilot.csv","inst_parts.csv","inst_skill.csv",
      "inst_sfs.csv","inst_operator.csv","charamake_data.csv","main_menu_text.csv","event.csv"}

seen={}  # name -> (jp_cell_count, sample)
for s in G.fsets():
    if s["nfiles"]==0: continue
    try: ents=G.fset_entries(s)
    except: continue
    for e in ents:
        nm=e["name"]
        if not nm.lower().endswith(".csv") or nm in seen: continue
        try: d=G.fset_read(s,e)
        except: continue
        try: txt=d.decode("cp932")
        except: continue
        cells=0; sample=""
        for line in txt.splitlines():
            for c in line.split(","):
                if jp.search(c):
                    cells+=1
                    if not sample: sample=c[:20]
        seen[nm]=(cells,sample)

arb=[(n,v) for n,v in seen.items() if "/ar_b/" in n]
other=[(n,v) for n,v in seen.items() if "/ar_b/" not in n and n.split("/")[-1] not in DONE]
arb_cells=sum(v[0] for n,v in arb)
other_cells=sum(v[0] for n,v in other)
print(f"fileset CSV {len(seen)}개")
print(f"ar_b/*.csv {len(arb)}개, 일본어셀 합 {arb_cells}")
print(f"기타(비ar_b, 미처리) {len(other)}개, 일본어셀 합 {other_cells}")
print(f"\n=== 비ar_b UI/텍스트 CSV (일본어셀>0, 셀많은순) ===")
for n,(c,samp) in sorted(other,key=lambda x:-x[1][0])[:40]:
    if c>0: print(f"  {c:5d}  {n}   ex={samp}")
print(f"\n=== ar_b 중 일본어셀 많은 것 top10 ===")
for n,(c,samp) in sorted(arb,key=lambda x:-x[1][0])[:10]:
    print(f"  {c:5d}  {n}  ex={samp}")
