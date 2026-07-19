# -*- coding: utf-8 -*-
"""charamake_data.csv의 FSTS 엔트리(off/usize/csize)를 확인하고,
그 값들이 fileset.dat/gundam.idx/EBOOT 어디에 또(중복) 참조되는지 탐색.
목표: FSTS 외에 파일 크기(csize)를 가리키는 stale 길이 필드 찾기."""
import sys, io, os, struct
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gaslib as G

TOTAL=187423360
fdat=G.rd(G.FSET_LBA,0,TOTAL)

# scene_custom_chara 번들에서 charamake_data.csv 엔트리
b=next(s for s in G.fsets() if s["name"]=="scene_custom_chara")
bb=fdat[b["off"]:b["off"]+b["size"]]
magic,nf,tbl,ntbl,dstart=struct.unpack_from("<4s4I",bb,0)
print(f"[scene_custom_chara] doff={b['off']} dsize={b['size']} nf={nf} tbl={tbl} ntbl={ntbl} dstart={dstart}")
print("FSTS 헤더 32B:", bb[:32].hex())
# 엔트리 stride 확인: tbl~ntbl / nf
stride=(ntbl-tbl)//nf
print(f"엔트리 stride = (ntbl-tbl)/nf = {ntbl-tbl}/{nf} = {stride} (16이면 4필드)")

cha=None
for i in range(nf):
    nameoff,off,usize,csize=struct.unpack_from("<4I",bb,tbl+16*i)
    e=bb.index(b"\x00",ntbl+nameoff); nm=bb[ntbl+nameoff:e].decode("ascii")
    if nm.endswith("charamake_data.csv"):
        cha=(i,nameoff,off,usize,csize)
        print(f"charamake 엔트리#{i}: nameoff={nameoff} off={off} usize={usize}(0x{usize:x}) csize={csize}(0x{csize:x})")
        print("  엔트리 16B:", bb[tbl+16*i:tbl+16*i+16].hex())
        # 절대 오프셋(fileset 내)
        abs_off=b["off"]+off
        print(f"  fileset 절대 오프셋 = {abs_off} (0x{abs_off:x})")

i,nameoff,off,usize,csize=cha
abs_off=b["off"]+off

# 값들을 u32 LE로 fileset 전체에서 검색(중복 참조 탐지)
def search_u32(buf, val, label, limit=20):
    pat=struct.pack("<I",val); hits=[]; p=0
    while True:
        j=buf.find(pat,p)
        if j<0: break
        hits.append(j); p=j+1
        if len(hits)>=limit: break
    print(f"  {label}={val}(0x{val:x}) → {len(hits)}곳: {[hex(h) for h in hits]}")
    return hits

print("\n=== fileset.dat 내 값 검색 ===")
search_u32(fdat, csize, "csize")
search_u32(fdat, usize, "usize")
search_u32(fdat, abs_off, "abs_off(fileset)")
search_u32(fdat, off, "off(bundle상대)")

# gundam.idx 검색
idx=G.rd(G.IDX_LBA,0,G.IDX_SIZE)
print("\n=== gundam.idx 내 값 검색 ===")
search_u32(idx, csize, "csize")
search_u32(idx, abs_off, "abs_off")

# EBOOT 검색
elf=open(os.path.join(G.BASE,"EBOOT_dec.elf"),"rb").read()
print("\n=== EBOOT 내 값 검색 ===")
search_u32(elf, csize, "csize")
search_u32(elf, abs_off, "abs_off")
