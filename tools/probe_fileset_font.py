# -*- coding: utf-8 -*-
"""GAS fileset.dat(FSTS 번들) 안에 폰트 사본이 있는지 탐색.
GBU 함정: 게임이 fileset의 gameinit 번들 RAIC 사본을 로드 → gundam.dat만 패치하면 무효.
GAS도 같은 구조인지 확인."""
import struct, os
ISO=r"C:\Emul\Switch\패치유틸.xdeltaUI\Gundam Assault Survive (Japan).iso"
SECTOR=2048
FSET_LBA=325328   # memory 기록
f=open(ISO,"rb")
def rd(lba,off,size): f.seek(lba*SECTOR+off); return f.read(size)

head=rd(FSET_LBA,0,0x50)
print("fileset head:", head[:0x50].hex())
# GBU 구조: 0x18 에 s1_off,s1_size,s2_off,s2_size
s1_off,s1_size,s2_off,s2_size=struct.unpack_from("<4I",head,0x18)
print(f"s1_off={s1_off} s1_size={s1_size} s2_off={s2_off} s2_size={s2_size}")
sec1=rd(FSET_LBA,s1_off,s1_size)
sec2=rd(FSET_LBA,s2_off,s2_size)
cnt=struct.unpack_from("<I",sec1,0)[0]
print("번들 수:", cnt)
offs=struct.unpack_from(f"<{cnt}I",sec1,4)
sets=[]
for i in range(cnt):
    nameoff,flags,doff,dsize,nf=struct.unpack_from("<5I",sec1,offs[i])
    e=sec2.index(b"\x00",nameoff)
    nm=sec2[nameoff:e].decode("ascii","replace")
    sets.append({"name":nm,"off":doff,"size":dsize,"nfiles":nf})

# 각 번들의 파일명에서 font 검색
hits=[]
for s in sets:
    if s["nfiles"]==0: continue
    b=rd(FSET_LBA,s["off"],min(s["size"],0x40))
    if b[:4]!=b"FSTS":
        continue
    bb=rd(FSET_LBA,s["off"],s["size"])
    magic,nf,tbl,ntbl,dstart=struct.unpack_from("<4s4I",bb,0)
    for i in range(nf):
        nameoff,off,usize,csize=struct.unpack_from("<4I",bb,tbl+16*i)
        e=bb.index(b"\x00",ntbl+nameoff)
        fn=bb[ntbl+nameoff:e].decode("ascii","replace")
        if "font" in fn.lower() or fn.lower().endswith(".fnt"):
            d=rd(FSET_LBA, s["off"]+off, min(csize,8))
            comp = d[:4]==b" 3;1"
            hits.append((s["name"],fn,usize,csize,"RAIC" if comp else "flat"))
print(f"\nfileset 내 폰트 후보 {len(hits)}건:")
for h in hits:
    print(f"  번들={h[0]:20s} 파일={h[1]:30s} usize={h[2]:,} csize={h[3]:,} {h[4]}")
f.close()
