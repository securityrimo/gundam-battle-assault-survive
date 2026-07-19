# -*- coding: utf-8 -*-
"""fileset.dat 정밀 분석: 디렉토리 레이아웃, 번들 doff 정렬, FSTS 내부 파일 off 정렬."""
import sys, io, os, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gaslib as G

head=G.rd(G.FSET_LBA,0,0x50)
print("header[0:0x50]:", head.hex())
magic=head[:8]
s1_off,s1_size,s2_off,s2_size=struct.unpack_from("<4I",head,0x18)
print(f"magic={magic}  s1(off={s1_off},size={s1_size})  s2(off={s2_off},size={s2_size})")
print(f"디렉토리 끝: {s2_off+s2_size}  (첫 번들 시작 전)")

sets=[s for s in G.fsets() if s["nfiles"]>0]
sd=sorted(sets,key=lambda s:s["off"])
print(f"\n번들 수(파일有): {len(sd)}  첫 doff={sd[0]['off']}  마지막 끝={sd[-1]['off']+sd[-1]['size']}")
# 번들 doff 정렬 추정
import math
def align_of(vals):
    a=0
    for p in (0x800,0x100,0x80,0x40,0x20,0x10,0x8,0x4,0x2):
        if all(v% p==0 for v in vals): return p
    return 1
print("번들 doff 정렬:", hex(align_of([s['off'] for s in sd])))
# 번들간 갭
gaps=[sd[i+1]['off']-(sd[i]['off']+sd[i]['size']) for i in range(len(sd)-1)]
print("번들간 갭: min",min(gaps),"max",max(gaps),"합",sum(gaps),"0이아닌개수",sum(1 for g in gaps if g))

# FSTS 내부: 한 번들 파일 off 정렬 + 헤더 필드
s=next(s for s in sets if s["name"]=="scene_custom_chara")
b=G.rd(G.FSET_LBA,s["off"],min(s["size"],0x40))
magic,nf,tbl,ntbl,dstart=struct.unpack_from("<4s4I",b,0)
print(f"\n[scene_custom_chara] FSTS magic={magic} nf={nf} tbl={tbl} ntbl={ntbl} dstart={dstart} size={s['size']}")
ents=G.fset_entries(s)
offs=[e["off"] for e in ents]
print("파일 off 정렬:", hex(align_of(offs)))
print("파일 off/usize/csize 앞 5개:")
for e in ents[:5]: print("  ",e["name"],"off",e["off"],"usize",e["usize"],"csize",e["csize"])
# 파일 데이터 사이 갭(csize 뒤 정렬 패딩)
so=sorted(ents,key=lambda x:x["off"])
fgaps=[so[i+1]["off"]-(so[i]["off"]+so[i]["csize"]) for i in range(len(so)-1)]
print("파일간 갭 min",min(fgaps),"max",max(fgaps),"합",sum(fgaps))
print("첫 파일 off",so[0]["off"],"vs dstart",dstart)
