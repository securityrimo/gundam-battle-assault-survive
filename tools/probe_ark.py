# -*- coding: utf-8 -*-
"""title.ark 포맷 조사 + main_menu/operator 번들에 grown-CSV 뒤 .ark/GIM 있는지 확인."""
import sys, io, os, struct
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gaslib as G

def bundle_files(name):
    s=next(x for x in G.fsets() if x["name"]==name)
    ents=G.fset_entries(s)
    return s,sorted(ents,key=lambda e:e["off"])

# title.ark 덤프
s,ents=bundle_files("scene_title")
ark=next(e for e in ents if e["name"].endswith("title.ark"))
data=G.fset_read(s,ark)
print(f"title.ark usize={len(data)} (csize={ark['csize']}) head32={data[:32].hex()}")
print("앞 128바이트:")
for o in range(0,128,16):
    row=data[o:o+16]; txt=''.join(chr(c) if 32<=c<127 else '.' for c in row)
    print(f"  {o:04x}: {row.hex(' ')}  {txt}")
# u32 배열로 해석 시 title 파일 크기/오프셋 닮은 값 있나 (title_0=78439 등)
u32s=struct.unpack_from(f"<{min(len(data)//4,24)}I",data,0)
print("앞 u32들:", [hex(x) for x in u32s])
# scene_title 파일 크기들
print("scene_title 파일(off,csize):")
for e in ents: print(f"  {e['name'].split('/')[-1]:20s} off={e['off']} csize={e['csize']} usize={e['usize']}")

# main_menu / inst_operator 번들 구성
for bname in ["main_menu"]:
    print(f"\n[{bname}] 파일:")
    s2,ents2=bundle_files(bname)
    for e in ents2: print(f"  {e['name'].split('/')[-1]:24s} off={e['off']} csize={e['csize']}")
# operator 사본 번들 이름 찾기
print("\ninst_operator.csv 있는 번들:")
for s in G.fsets():
    if s["nfiles"]==0: continue
    try: es=G.fset_entries(s)
    except: continue
    if any(e["name"].endswith("inst_operator.csv") for e in es):
        so=sorted(es,key=lambda e:e["off"])
        oi=next(i for i,e in enumerate(so) if e["name"].endswith("inst_operator.csv"))
        after=so[oi+1]["name"].split("/")[-1] if oi+1<len(so) else "(마지막)"
        print(f"  {s['name']}: operator#{oi}/{len(so)}, 바로뒤={after}")
