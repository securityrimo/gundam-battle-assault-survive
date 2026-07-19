# -*- coding: utf-8 -*-
"""GAS 폰트 검증: font_data_j14x14.fnt 를 49B/글리프 14x14 2bpp 로 렌더.
가설: GBU와 달리 인터리브 없이 글리프가 49B씩 연속 저장.
LSB/MSB 두 비트순서로 아틀라스를 뽑아 눈으로 확정."""
import struct, os
import numpy as np
from PIL import Image

ISO = r"C:\Emul\Switch\패치유틸.xdeltaUI\Gundam Assault Survive (Japan).iso"
OUT = r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gas"
SECTOR = 2048
GDAT_LBA, IDX_LBA, IDX_SIZE = 133792, 416848, 479873
f = open(ISO, "rb")
def rd(lba, off, size):
    f.seek(lba*SECTOR+off); return f.read(size)
u32 = lambda b,o: struct.unpack_from("<I", b, o)[0]
idx = rd(IDX_LBA,0,IDX_SIZE)
hdr,n_ent,sec2_off = u32(idx,0xc),u32(idx,0x10),u32(idx,0x20)
def name_at(o):
    e=idx.index(b"\x00",sec2_off+o); return idx[sec2_off+o:e].decode("ascii","replace")
entries=[struct.unpack_from("<6I",idx,hdr+i*24) for i in range(n_ent)]
files={}
def walk(i,path,d=0):
    if d>12: return
    t,no,a,b,c,dd=entries[i]; nm=name_at(no)
    if t==1:
        for j in range(b,b+a): walk(j,path+"/"+nm,d+1)
    else: files[path+"/"+nm]={"off":b,"size":c}
walk(0,"")
def raic_decompress(data):
    usize=struct.unpack_from("<I",data,4)[0]
    p=bytes(x^0x72 for x in data[8:]); N,TH=4096,2
    ring=bytearray(N); r=N-18; out=bytearray(); pos=0; flags=0; fc=0
    while len(out)<usize:
        if fc==0: flags=p[pos]; pos+=1; fc=8
        if flags&1:
            c=p[pos]; pos+=1; out.append(c); ring[r]=c; r=(r+1)&(N-1)
        else:
            b1,b2=p[pos],p[pos+1]; pos+=2
            off=b1|((b2&0xF0)<<4); ln=(b2&0x0F)+TH+1
            for k in range(ln):
                c=ring[(off+k)&(N-1)]; out.append(c); ring[r]=c; r=(r+1)&(N-1)
                if len(out)>=usize: break
        flags>>=1; fc-=1
    return bytes(out)

p="/data/extra/font_data_j14x14.fnt"
fi=files[p]; raw=rd(GDAT_LBA,fi["off"],fi["size"])
comp = raw[:4]==b" 3;1"
if comp: raw=raic_decompress(raw)
print(f"font size={len(raw):,} compressed_in_dat={comp}  49B당 글리프={len(raw)/49:.3f}")
open(os.path.join(OUT,"font_j14x14.bin"),"wb").write(raw)

GB=49; W=H=14
nglyph=len(raw)//GB
PAL=np.array([255,170,85,0],dtype=np.uint8)  # 2bpp -> grayscale

def render(glyph_bytes, lsb=True):
    px=np.zeros(W*H,dtype=np.uint8)
    bitpos=0
    for i in range(W*H):
        byte=glyph_bytes[bitpos>>3]
        sh=(bitpos&7)
        if lsb: v=(byte>>sh)&3
        else:   v=(byte>>(6-sh))&3   # MSB-first within byte, 2-bit groups
        px[i]=v; bitpos+=2
    return px.reshape(H,W)

def atlas(start, cols=32, rows=32, lsb=True, scale=2):
    cell=W+2
    img=np.full((rows*cell*scale, cols*cell*scale),40,dtype=np.uint8)
    for gi in range(rows*cols):
        idx_=start+gi
        if idx_>=nglyph: break
        g=raw[idx_*GB:(idx_+1)*GB]
        m=render(g,lsb)
        gray=PAL[m]
        big=np.kron(gray,np.ones((scale,scale),dtype=np.uint8))
        r=(gi//cols); c=(gi%cols)
        y=r*cell*scale; x=c*cell*scale
        img[y:y+H*scale, x:x+W*scale]=big
    return Image.fromarray(img,'L')

for lsb in (True,False):
    tag="lsb" if lsb else "msb"
    atlas(0,lsb=lsb).save(os.path.join(OUT,f"atlas_{tag}_0.png"))
    atlas(1024,lsb=lsb).save(os.path.join(OUT,f"atlas_{tag}_1024.png"))
print("아틀라스 저장: atlas_lsb_0.png / atlas_msb_0.png / *_1024.png")
print(f"글리프 수={nglyph}")
f.close()
