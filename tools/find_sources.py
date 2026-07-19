# -*- coding: utf-8 -*-
"""화면의 미번역 문자열들이 어느 소스(EBOOT / fileset CSV·파일 / gundam.dat)에서 오는지 탐색."""
import sys, io, os, struct
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gaslib as G

TARGETS=["地球連邦宇宙軍","はじまりの峡谷","偵察部隊掃討作戦","のシチュエーションです","時代切替","クリア情報","メインメニューに戻る","決定"]

elf=open(os.path.join(G.BASE,"EBOOT_dec.elf"),"rb").read()
def find_in(buf,needle):
    b=needle.encode("cp932"); hits=[]; p=0
    while True:
        j=buf.find(b,p)
        if j<0: break
        hits.append(j); p=j+1
    return hits

print("=== EBOOT_dec.elf ===")
for t in TARGETS:
    h=find_in(elf,t)
    print(f"  {t}: {len(h)}건 {'@'+hex(h[0]) if h else ''}")

# gundam.dat 트리에서 텍스트 파일(csv/txt/dat) + fileset 전 파일에서 검색
print("\n=== gundam.dat 파일들에서 검색(미션명/소속군) ===")
tree=G.gtree()
for t in ["はじまりの峡谷","地球連邦宇宙軍"]:
    found=[]
    for p in sorted(tree):
        if not p.lower().endswith((".csv",".txt",".dat",".bin",".tbl")): continue
        try: d=G.gfile(p)
        except: continue
        if t.encode("cp932") in d: found.append(p)
        if len(found)>=5: break
    print(f"  {t}: {found[:5]}")

# fileset 전 파일에서 미션명 검색(압축 해제 포함)
print("\n=== fileset에서 미션명(はじまりの峡谷) 검색 ===")
cnt=0
for s in G.fsets():
    if s["nfiles"]==0: continue
    try: ents=G.fset_entries(s)
    except: continue
    for e in ents:
        try: d=G.fset_read(s,e)
        except: continue
        if "はじまりの峡谷".encode("cp932") in d:
            print(f"  {s['name']} / {e['name']}"); cnt+=1
            if cnt>=8: break
    if cnt>=8: break
