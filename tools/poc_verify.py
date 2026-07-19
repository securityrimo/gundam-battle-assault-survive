# -*- coding: utf-8 -*-
"""PoC ISO 오프라인 검증: 패치된 fileset 폰트/CSV를 되읽어 한글 주입 확인 + 미리보기."""
import sys, io, os, struct, json
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gaslib as G

DST=os.path.join(os.path.dirname(G.ISO),"Gundam Assault Survive (Korean_PoC).iso")
f=open(DST,"rb")
def rd(lba,off,size): f.seek(lba*G.SECTOR+off); return f.read(size)

kr=json.load(io.open(os.path.join(G.BASE,"kr_map_poc.json"),encoding="utf-8"))  # {글자:[ti,code]}

# fileset 오프셋 재계산(gaslib는 원본 ISO를 읽으니 구조는 동일)
gi=[s for s in G.fsets() if s["name"]=="gameinit"][0]
gents=G.fset_entries(gi)
fe=[e for e in gents if e["name"].endswith("font_data_j14x14.fnt")][0]
# 패치된 csize를 PoC ISO의 FSTS 테이블에서 다시 읽음
bh=rd(G.FSET_LBA,gi["off"],0x14); _m,_nf,tbl,_nt,_ds=struct.unpack_from("<4s4I",bh,0)
csz=struct.unpack_from("<I", rd(G.FSET_LBA, gi["off"]+tbl+16*fe["idx"]+12,4),0)[0]
comp=rd(G.FSET_LBA, gi["off"]+fe["off"], csz)
font_plain=G.raic_decompress(comp)
print(f"패치폰트 fileset: csize={csz} usize={len(font_plain)}")

# 주입 글리프 렌더
ROWB,CW,CH,COLS=224,14,14,32
PAL=np.array([255,170,85,0],np.uint8)
def render(fnt,ti):
    cell,plane=ti//2,ti%2; r,c=divmod(cell,COLS)
    m=np.zeros((CH,CW),np.uint8)
    for y in range(CH):
        for x in range(CW):
            off=(r*CH+y)*ROWB+c*7+x//2
            nsh=(4 if x%2 else 0)+(2 if plane else 0)
            m[y,x]=(fnt[off]>>nsh)&3
    return m
chars=list(kr.keys()); scale=6; cp=CW+2
img=np.full((cp*scale, len(chars)*cp*scale),40,np.uint8)
for k,ch in enumerate(chars):
    ti=kr[ch][0]; gray=PAL[render(font_plain,ti)]
    big=np.kron(gray,np.ones((scale,scale),np.uint8))
    img[0:CH*scale, k*cp*scale:k*cp*scale+CW*scale]=big
Image.fromarray(img,'L').save(os.path.join(G.BASE,"poc_injected_glyphs.png"))
print(f"주입 글리프 {len(chars)}자 렌더 -> poc_injected_glyphs.png:", "".join(chars))

# CSV 되읽기
for s in G.fsets():
    if s["nfiles"]==0: continue
    try: ents=G.fset_entries(s)
    except: continue
    for e in ents:
        if not e["name"].endswith("main_menu_text.csv"): continue
        bh=rd(G.FSET_LBA,s["off"],0x14); _m,_nf,tb,_nt,_ds=struct.unpack_from("<4s4I",bh,0)
        csz=struct.unpack_from("<I", rd(G.FSET_LBA,s["off"]+tb+16*e["idx"]+12,4),0)[0]
        comp=rd(G.FSET_LBA,s["off"]+e["off"],csz)
        plain=G.raic_decompress(comp)
        # donor 코드→한글 역치환해서 사람이 읽게
        rev={code:ch for ch,(ti,code) in kr.items()}
        txt=plain.decode("cp932")
        # 2글자 SJIS 중 donor 코드를 한글로 역변환
        recon=[]
        i=0
        while i<len(txt):
            ch=txt[i]
            try: code=struct.unpack(">H",ch.encode("cp932"))[0] if len(ch.encode("cp932"))==2 else None
            except: code=None
            recon.append(rev.get(code,ch)); i+=1
        out="".join(recon)
        io.open(os.path.join(G.BASE,"poc_csv_readback.txt"),"w",encoding="utf-8").write(out)
        # 한글 몇 개 포함됐는지
        nk=sum(1 for c in out if "가"<=c<="힣")
        print(f"CSV {s['name']}: csize={csz} 한글역변환 {nk}자 -> poc_csv_readback.txt")
        break
    else: continue
    break
f.close()
print("검증 완료")
