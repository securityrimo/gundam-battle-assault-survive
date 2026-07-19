# -*- coding: utf-8 -*-
"""GAS(건담 어설트 서바이브 PSP) 공용 라이브러리 — GBU와 동일 엔진(gpsp3).
gbulib 구조를 GAS ISO 오프셋에 맞춰 이식. 폰트/charset 모델은 GBU와 100% 동일 검증됨.
- charset 테이블: EBOOT_dec.elf 0x3aad24, 6953개 (GBU BOOT.BIN 0x2e71e0과 바이트 동일)
- 폰트: /data/extra/font_data_j14x14.fnt, 448px 4bpp 선형, cell=idx//2 plane=idx%2
"""
import struct, os, json

BASE = os.path.dirname(os.path.abspath(__file__))
ISO = os.path.join(os.path.dirname(BASE), "Gundam Assault Survive (Japan).iso")
SECTOR = 2048
GDAT_LBA = 133792   # gundam.dat
FSET_LBA = 325328   # fileset.dat
IDX_LBA  = 416848   # gundam.idx
IDX_SIZE = 479873

_iso=None
def iso():
    global _iso
    if _iso is None: _iso=open(ISO,"rb")
    return _iso
def rd(lba,off,size):
    f=iso(); f.seek(lba*SECTOR+off); return f.read(size)

# ---------- charset ----------
_charset=None
def charset():
    """glyph_index -> SJIS code (u16 BE). 6953개."""
    global _charset
    if _charset is None:
        elf=open(os.path.join(BASE,"EBOOT_dec.elf"),"rb").read()
        _charset=struct.unpack_from(">6953H", elf, 0x3aad24)
    return _charset

# ---------- PIDX0 (gundam.idx / gundam.dat) ----------
_tree=None
def gtree():
    global _tree
    if _tree is None:
        idx=rd(IDX_LBA,0,IDX_SIZE)
        u32=lambda b,o: struct.unpack_from("<I",b,o)[0]
        hdr,n_ent,sec2=u32(idx,0xc),u32(idx,0x10),u32(idx,0x20)
        def name_at(o):
            e=idx.index(b"\x00",sec2+o); return idx[sec2+o:e].decode("ascii","replace")
        ents=[struct.unpack_from("<6I",idx,hdr+i*24) for i in range(n_ent)]
        files={}
        def walk(i,path,d=0):
            if d>12: return
            t,no,a,b,c,dd=ents[i]; nm=name_at(no)
            if t==1:
                for j in range(b,b+a): walk(j,path+"/"+nm,d+1)
            else: files[path+"/"+nm]={"off":b,"size":c}
        walk(0,"")
        _tree=files
    return _tree
def gfile(path):
    fi=gtree()[path]; d=rd(GDAT_LBA,fi["off"],fi["size"])
    return raic_decompress(d) if d[:4]==b" 3;1" else d

# ---------- RAIC (gbulib과 동일) ----------
def raic_decompress(data):
    assert data[:4]==b" 3;1", data[:4]
    usize=struct.unpack_from("<I",data,4)[0]
    p=bytes(b^0x72 for b in data[8:]); N,TH=4096,2
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

def raic_compress(data, lazy=True):
    N,F,TH=4096,18,2; n=len(data)
    from collections import defaultdict
    heads=defaultdict(list)
    def ring_of(i): return (N-F+i)&(N-1)
    def find_match(pos):
        best_len,best_off=0,0
        if pos+TH>=n: return 0,0
        key=data[pos:pos+3]; cand=heads.get(key)
        if not cand: return 0,0
        maxl=min(F,n-pos)
        for j in reversed(cand[-64:]):
            if pos-j>N-F: continue
            l=0
            while l<maxl and data[pos+l]==data[j+(l%(pos-j))]: l+=1
            if l>best_len:
                best_len,best_off=l,j
                if l>=maxl: break
        return best_len,best_off
    def add_head(pos):
        if pos+3<=n: heads[data[pos:pos+3]].append(pos)
    items=[]; pos=0
    while pos<n:
        blen,boff=find_match(pos)
        if blen>=TH+1:
            if lazy and pos+1<n:
                add_head(pos); nlen,noff=find_match(pos+1)
                if nlen>blen:
                    items.append((True,data[pos:pos+1])); pos+=1; continue
                for k in range(1,blen): add_head(pos+k)
            else:
                for k in range(blen): add_head(pos+k)
            ri=ring_of(boff)
            b2=((ri>>4)&0xF0)|(blen-TH-1); b1=ri&0xFF
            items.append((False,bytes((b1,b2)))); pos+=blen
        else:
            items.append((True,data[pos:pos+1])); add_head(pos); pos+=1
    stream=bytearray()
    for i in range(0,len(items),8):
        chunk=items[i:i+8]; flags=0
        for bi,(is_lit,_) in enumerate(chunk):
            if is_lit: flags|=(1<<bi)
        stream.append(flags)
        for _,pl in chunk: stream+=pl
    return b" 3;1"+struct.pack("<I",n)+bytes(b^0x72 for b in stream)

# ---------- FSTS (fileset.dat) ----------
_sets=None
def fsets():
    global _sets
    if _sets is None:
        head=rd(FSET_LBA,0,0x50)
        s1_off,s1_size,s2_off,s2_size=struct.unpack_from("<4I",head,0x18)
        sec1=rd(FSET_LBA,s1_off,s1_size); sec2=rd(FSET_LBA,s2_off,s2_size)
        cnt=struct.unpack_from("<I",sec1,0)[0]
        offs=struct.unpack_from(f"<{cnt}I",sec1,4)
        _sets=[]
        for i in range(cnt):
            nameoff,flags,doff,dsize,nf=struct.unpack_from("<5I",sec1,offs[i])
            e=sec2.index(b"\x00",nameoff)
            _sets.append({"name":sec2[nameoff:e].decode("ascii"),"off":doff,"size":dsize,"nfiles":nf})
    return _sets
def fset_entries(s):
    if s["nfiles"]==0: return []
    b=rd(FSET_LBA,s["off"],s["size"])
    magic,nf,tbl,ntbl,dstart=struct.unpack_from("<4s4I",b,0)
    assert magic==b"FSTS",(s["name"],magic)
    ents=[]
    for i in range(nf):
        nameoff,off,usize,csize=struct.unpack_from("<4I",b,tbl+16*i)
        e=b.index(b"\x00",ntbl+nameoff)
        ents.append({"name":b[ntbl+nameoff:e].decode("ascii"),"off":off,"usize":usize,"csize":csize,"tbl":tbl,"idx":i})
    return ents
def fset_read(s,ent,decompress=True):
    d=rd(FSET_LBA,s["off"]+ent["off"],ent["csize"])
    return raic_decompress(d) if (decompress and d[:4]==b" 3;1") else d

# ---------- 폰트 렌더/패치 (GBU 확정 모델) ----------
FONT_PATH="/data/extra/font_data_j14x14.fnt"
ROWB,CW,CH,COLS=224,14,14,32
def glyph_read(fnt,ti):
    import numpy as np
    cell,plane=ti//2,ti%2; r,c=divmod(cell,COLS)
    m=np.zeros((CH,CW),np.uint8)
    for y in range(CH):
        for x in range(CW):
            off=(r*CH+y)*ROWB+c*7+x//2
            nsh=(4 if x%2 else 0)+(2 if plane else 0)
            m[y,x]=(fnt[off]>>nsh)&3
    return m
def glyph_write(fnt,ti,q):
    """q: 14x14 (0..3). fnt: bytearray."""
    cell,plane=ti//2,ti%2; r,c=divmod(cell,COLS)
    sh=0 if plane==0 else 2
    for y in range(CH):
        base=(r*CH+y)*ROWB+c*7
        for x in range(CW):
            off=base+x//2
            nsh=(0 if x%2==0 else 4)+sh
            b=fnt[off]; b&=~(3<<nsh)&0xFF; b|=(int(q[y,x])&3)<<nsh
            fnt[off]=b

if __name__=="__main__":
    cs=charset(); print("charset:",len(cs),"first:",hex(cs[0]),hex(cs[1]))
    t=gtree(); print("gundam.dat files:",len(t))
    print("font in dat:", FONT_PATH in t, t.get(FONT_PATH))
    print("fsets:",len(fsets()))
