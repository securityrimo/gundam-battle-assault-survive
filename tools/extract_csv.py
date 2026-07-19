# -*- coding: utf-8 -*-
"""gundam.dat(PIDX0/FSTS/RAIC)에서 모든 .csv 텍스트를 추출.
원본 ISO는 읽기 전용. 결과는 work_gas/csv_src/<원본경로> 로 저장(cp932→utf-8-sig).
GBU와 동일 엔진 로직(probe_text_font.py 검증본) 재사용."""
import struct, os, io

ISO = r"C:\Emul\Switch\패치유틸.xdeltaUI\Gundam Assault Survive (Japan).iso"
OUTDIR = r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gas\csv_src"
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

def read_file(path):
    fi=files[path]; d=rd(GDAT_LBA,fi["off"],fi["size"])
    raic = d[:4]==b" 3;1"
    if raic: d=raic_decompress(d)
    return d, raic

csvs = sorted(p for p in files if p.lower().endswith(".csv"))
print(f"총 파일 {len(files):,}개 중 .csv {len(csvs)}개 발견\n")

manifest = []
for p in csvs:
    d, raic = read_file(p)
    # cp932 디코드 시도
    try:
        txt = d.decode("cp932")
        enc_ok = True
    except Exception as e:
        txt = None; enc_ok = False
    rel = p.lstrip("/")
    outp = os.path.join(OUTDIR, rel)
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    if enc_ok:
        # utf-8-sig 로 저장(엑셀/지피티 친화). 원본 라인수 보존.
        with io.open(outp, "w", encoding="utf-8-sig", newline="") as w:
            w.write(txt)
        nlines = txt.count("\n")+1
    else:
        with open(outp, "wb") as w:
            w.write(d)
        nlines = -1
    manifest.append((p, len(d), raic, enc_ok, nlines))
    flag = "RAIC" if raic else "flat"
    dec = "cp932" if enc_ok else "!! BINARY(디코드실패)"
    print(f"  {p:50s} {len(d):8,}B {flag:5s} {dec} lines={nlines}")

# 매니페스트 저장
mf = os.path.join(OUTDIR, "_manifest.tsv")
with io.open(mf, "w", encoding="utf-8-sig", newline="") as w:
    w.write("path\tsize\tcompressed\tcp932_ok\tlines\n")
    for row in manifest:
        w.write("\t".join(str(x) for x in row)+"\n")
print(f"\n추출 완료 → {OUTDIR}")
print(f"매니페스트 → {mf}")
f.close()
