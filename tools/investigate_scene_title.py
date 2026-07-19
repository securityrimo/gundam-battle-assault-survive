# -*- coding: utf-8 -*-
"""scene_title 번들에서 charamake 뒤 파일들(밀리면 깨지는 것)의 오프셋이
fileset/gundam.idx/EBOOT 어디서 외부 참조되는지 탐색."""
import sys, io, os, struct
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gaslib as G

TOTAL=187423360
fdat=G.rd(G.FSET_LBA,0,TOTAL)
b=next(s for s in G.fsets() if s["name"]=="scene_title")
bb=fdat[b["off"]:b["off"]+b["size"]]
m,nf,tbl,ntbl,dstart=struct.unpack_from("<4s4I",bb,0)
print(f"[scene_title] doff={b['off']} dsize={b['size']} nf={nf}")
ents=[]
for i in range(nf):
    nameoff,off,usize,csize=struct.unpack_from("<4I",bb,tbl+16*i)
    e=bb.index(b"\x00",ntbl+nameoff); nm=bb[ntbl+nameoff:e].decode("ascii")
    ents.append((i,off,usize,csize,nm))
ents_by_off=sorted(ents,key=lambda x:x[1])
# charamake 위치와 그 뒤 파일들
ci=next(k for k,e in enumerate(ents_by_off) if e[4].endswith("charamake_data.csv"))
print(f"charamake off-순서 {ci}/{nf}. charamake와 뒤 6개:")
for e in ents_by_off[ci:ci+7]:
    i,off,usize,csize,nm=e
    abs_off=b["off"]+off
    print(f"  #{i} off={off}(abs 0x{abs_off:x}) csize={csize} {nm}")

# 뒤 파일들의 abs_off를 fileset/idx/eboot에서 검색
idx=G.rd(G.IDX_LBA,0,G.IDX_SIZE)
elf=open(os.path.join(G.BASE,"EBOOT_dec.elf"),"rb").read()
def cnt_u32(buf,val):
    pat=struct.pack("<I",val); c=0; p=0
    while True:
        j=buf.find(pat,p)
        if j<0: break
        c+=1; p=j+1
    return c
print("\n뒤 파일 abs_off 외부참조(fileset/idx/eboot 개수):")
for e in ents_by_off[ci+1:ci+7]:
    i,off,usize,csize,nm=e
    abs_off=b["off"]+off
    print(f"  {nm}: abs=0x{abs_off:x} → fileset {cnt_u32(fdat,abs_off)}, idx {cnt_u32(idx,abs_off)}, eboot {cnt_u32(elf,abs_off)} | off(rel)={off} fileset {cnt_u32(fdat,off)}")
