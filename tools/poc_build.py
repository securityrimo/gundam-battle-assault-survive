# -*- coding: utf-8 -*-
"""GAS 한글 PoC 빌더.
- 폰트: fileset gameinit 사본(RAIC) + gundam.dat 사본(flat) 양쪽에 한글 글리프 주입
- 텍스트: main_menu_text.csv 몇 줄을 한글로 → fileset 전 사본 RAIC 재압축 in-place
원본 ISO 불변, 사본(PoC ISO)에만 기록. GBU 검증 방식(75/97) 그대로.
"""
import sys, io, os, struct, json, shutil
import numpy as np
from PIL import Image, ImageFont, ImageDraw
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gaslib as G

SRC_ISO = G.ISO
DST_ISO = os.path.join(os.path.dirname(SRC_ISO), "Gundam Assault Survive (Korean_PoC).iso")
KRFONT  = r"C:\Windows\Fonts\malgunbd.ttf"

# main_menu_text.csv 의 (행,열) -> 한글. 색상코드 {C=..}{CE}·리터럴 \n 유지. 전각 사용.
# 셀 내 줄바꿈은 리터럴 백슬래시+n("\\n"), 실제 개행 아님(행 구분과 구별)
KO = {
 (1,2): "{C=3ca0a0}시츄에이션{CE}　미션　시작。",
 (2,2): "{C=3ca0a0}커스텀　파일럿{CE}　관리。",
 (5,2): "{C=3ca0a0}대전　모드{CE}　시작。",
 (6,2): "{C=3ca0a0}각종　설정{CE}　변경。",
 (8,2): "대장님、　무운을。",
}

def need_syllables():
    s=set()
    for t in KO.values():
        for ch in t:
            if "가"<=ch<="힣": s.add(ch)
    return sorted(s)

def build_kr_map(need):
    cs=G.charset()
    def dec(c):
        try: return struct.pack(">H",c).decode("cp932")
        except: return None
    # 사용 문자 집합: 추출된 csv_src 전부 + eboot 문자열 일부(간단히 csv만으로도 PoC 충분)
    used=set()
    srcdir=os.path.join(G.BASE,"csv_src")
    for root,_,fs in os.walk(srcdir):
        for fn in fs:
            if fn.endswith(".csv"):
                try: used.update(io.open(os.path.join(root,fn),encoding="utf-8-sig").read())
                except: pass
    donors=[]
    for ti in range(len(cs)):
        ch=dec(cs[ti])
        if ch and ch not in used and "一"<=ch<="鿿":
            donors.append((ti,cs[ti]))
    donors=donors[len(donors)//3:]   # 앞쪽 흔한 한자 회피(GBU와 동일)
    if len(need)>len(donors):
        raise RuntimeError(f"donor 부족 {len(need)}>{len(donors)}")
    kr={ch:(ti,code) for ch,(ti,code) in zip(need,donors)}
    return kr

def make_encoder(kr):
    def enc(s):
        out=bytearray()
        for ch in s:
            if ch=="\n": out+=b"\\n"           # CSV는 리터럴 백슬래시+n
            elif "가"<=ch<="힣": out+=struct.pack(">H",kr[ch][1])
            else: out+=ch.encode("cp932")
        return bytes(out)
    return enc

def render2bpp(ch, font):
    img=Image.new("L",(24,24),0)
    ImageDraw.Draw(img).text((2,3),ch,fill=255,font=font)
    a=np.asarray(img); ys,xs=np.nonzero(a>40)
    if len(xs)==0: return np.zeros((14,14),np.uint8)
    crop=a[ys.min():ys.max()+1, xs.min():xs.max()+1]; h,w=crop.shape
    if h>14 or w>14:
        crop=np.asarray(Image.fromarray(crop).resize((min(w,14),min(h,14)),Image.LANCZOS)); h,w=crop.shape
    cv=np.zeros((14,14),np.uint8); oy,ox=(14-h)//2,(14-w)//2; cv[oy:oy+h,ox:ox+w]=crop
    q=np.zeros((14,14),np.uint8); q[cv>=64]=1; q[cv>=128]=2; q[cv>=192]=3
    return q

def patch_font_bytes(fnt_bytearray, kr, font):
    for ch,(ti,code) in kr.items():
        G.glyph_write(fnt_bytearray, ti, render2bpp(ch,font))

def translate_csv_bytes(data, enc):
    text=data.decode("cp932")
    sep="\r\n" if "\r\n" in text else "\n"
    rows=[ln.split(",") for ln in text.split(sep)]
    changed=0
    for (ri,ci),ko in KO.items():
        if ri<len(rows) and ci<len(rows[ri]):
            rows[ri][ci]=ko; changed+=1
    joined=sep.join(",".join(r) for r in rows)
    # 인코딩: 한글→donor, \n 리터럴 유지, 그 외 cp932
    out=bytearray()
    for ch in joined:
        if "가"<=ch<="힣": out+=struct.pack(">H", KRMAP[ch][1])
        else: out+=ch.encode("cp932")
    return bytes(out), changed

need=need_syllables()
print(f"필요 음절 {len(need)}개: {''.join(need)}")
KRMAP=build_kr_map(need)
print(f"donor 할당 완료: {len(KRMAP)}개")
json.dump({c:[t,code] for c,(t,code) in KRMAP.items()}, io.open(os.path.join(G.BASE,"kr_map_poc.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=0)

krfont=ImageFont.truetype(KRFONT,13)

# ---- ISO 복사 ----
if not os.path.exists(DST_ISO):
    print("ISO 복사 중(854MB)..."); shutil.copyfile(SRC_ISO, DST_ISO)
else:
    print("기존 PoC ISO에 재기록")
out=open(DST_ISO,"r+b")

# ---- 폰트 패치 ----
# (a) fileset gameinit 사본 (RAIC)
gi=[s for s in G.fsets() if s["name"]=="gameinit"][0]
gents=G.fset_entries(gi)
fe=[e for e in gents if e["name"].endswith("font_data_j14x14.fnt")][0]
font_plain=bytearray(G.fset_read(gi,fe))
patch_font_bytes(font_plain, KRMAP, krfont)
fcomp=G.raic_compress(bytes(font_plain))
assert len(fcomp)<=fe["csize"], f"폰트 재압축 초과 {len(fcomp)}>{fe['csize']}"
bhead=G.rd(G.FSET_LBA,gi["off"],0x14); _m,_nf,tbl,_nt,_ds=struct.unpack_from("<4s4I",bhead,0)
abs_off=G.FSET_LBA*G.SECTOR+gi["off"]+fe["off"]
out.seek(abs_off); out.write(fcomp+b"\x00"*(fe["csize"]-len(fcomp)))
out.seek(G.FSET_LBA*G.SECTOR+gi["off"]+tbl+16*fe["idx"]+12); out.write(struct.pack("<I",len(fcomp)))
print(f"폰트 fileset(gameinit) 패치: {len(fcomp)}/{fe['csize']}B")
# (b) gundam.dat 사본 (flat, 동일 크기 직접 기록)
gfi=G.gtree()[G.FONT_PATH]
gfont=bytearray(G.rd(G.GDAT_LBA,gfi["off"],gfi["size"]))
patch_font_bytes(gfont, KRMAP, krfont)
out.seek(G.GDAT_LBA*G.SECTOR+gfi["off"]); out.write(gfont)
print(f"폰트 gundam.dat 패치: {gfi['size']}B (flat)")

# ---- CSV 패치: fileset 전 사본 ----
enc=make_encoder(KRMAP)
csv_patched=0
for s in G.fsets():
    if s["nfiles"]==0: continue
    try: ents=G.fset_entries(s)
    except: continue
    for e in ents:
        if not e["name"].endswith("main_menu_text.csv"): continue
        data=G.fset_read(s,e)
        newdata,changed=translate_csv_bytes(data,enc)
        comp=G.raic_compress(newdata)
        so=sorted(ents,key=lambda x:x["off"])
        i=next(i for i,x in enumerate(so) if x["off"]==e["off"])
        room=(so[i+1]["off"] if i+1<len(so) else s["size"])-e["off"]
        if len(comp)>room:
            print(f"  [스킵] {e['name']}@{s['name']} 재압축 {len(comp)}>{room}"); continue
        bh=G.rd(G.FSET_LBA,s["off"],0x14); _m,_nf,tb,_nt,_ds=struct.unpack_from("<4s4I",bh,0)
        base=G.FSET_LBA*G.SECTOR+s["off"]
        out.seek(base+e["off"]); out.write(comp)
        out.seek(base+tb+16*e["idx"]+8);  out.write(struct.pack("<I",len(newdata)))
        out.seek(base+tb+16*e["idx"]+12); out.write(struct.pack("<I",len(comp)))
        csv_patched+=1
        print(f"  CSV {e['name']}@{s['name']}: cells={changed} usize {len(data)}->{len(newdata)} comp={len(comp)}/{room}")
out.close()
print(f"\nCSV 사본 {csv_patched}개 패치 완료")
print("DONE:", DST_ISO)
