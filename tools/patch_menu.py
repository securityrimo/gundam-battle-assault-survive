# -*- coding: utf-8 -*-
"""main_menu_text.csv 전체 한글화 → fileset 사본 RAIC 재압축 in-place.
번역은 직접 정제(MT 오역 교정). 폰트는 필요한 한글 글리프를 fileset+gundam.dat 양쪽 주입.
in-place 슬롯(≈1472B) 초과 시, 우선순위 낮은 셀(높은 행=프라이즈 메시지)부터 원문 유지하고 보고."""
import sys, io, os, struct, json, shutil, csv
import numpy as np
from PIL import Image, ImageFont, ImageDraw
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gaslib as G

DST_ISO = os.path.join(os.path.dirname(G.ISO), "Gundam Assault Survive (Korean_PoC).iso")
KRFONT  = r"C:\Windows\Fonts\malgunbd.ttf"
CSVNAME = "main_menu_text.csv"

# col2 정제 번역. 코드 {C=..}{CE}·%s·「」·리터럴 \n 보존. 우선순위=행 오름차순(메뉴 먼저).
KO = {
 1:  "{C=3ca0a0}시츄에이션{CE}　미션　시작。\\n３인　협력　가능。",
 2:  "{C=3ca0a0}커스텀　파일럿{CE}　관리。",
 3:  "{C=3ca0a0}통신　매칭{CE}。\\n대전・협력　전　선택。",
 4:  "{C=3ca0a0}숍{CE}으로　이동。\\n기체・파일럿　구입　가능。",
 5:  "{C=3ca0a0}대전　모드{CE}　시작。\\n４인　협력　가능。",
 6:  "{C=3ca0a0}각종　설정{CE}　변경。\\nＨＯＷＴＯ　확인　가능。",
 8:  "대장님、　무운을。",
 9:  "{C=3ca0a0}통신　차단{CE}。",
 11: "{C=284880}타이틀{CE}로　복귀？",
 12: "통신　차단？",
 13: "{C=284880}미션{CE}　선택됨。\\n{C=284880}ＳＩＴＵＡＴＩＯＮ{CE}에서　출격　준비。",
 14: "{C=284880}ＶＳ　ＢＡＴＴＬＥ{CE}　선택됨。\\n출격　준비。",
 16: "{C=3ca0a0}「%s」{CE}\\n노획。　숍에서　구입　가능。",
 17: "{C=3ca0a0}「%s」{CE}\\n노획、　{C=3ca0a0}%sＧ{CE}에　매각。",
 18: "{C=3ca0a0}「%s」{CE}\\n획득。",
 19: "{C=3ca0a0}「%s」{CE}\\n획득、　{C=3ca0a0}%sＧ{CE}에　매각。",
 21: "새　{C=3ca0a0}파일럿{CE}　숍　등록。",
 22: "새　{C=3ca0a0}ＭＳ{CE}　숍　등록。",
 23: "새　{C=3ca0a0}ＳＦＳ{CE}　숍　등록。",
 24: "새　{C=3ca0a0}오퍼레이터{CE}　숍　등록。",
 25: "새　{C=3ca0a0}스킬{CE}　숍　등록。",
 26: "새　{C=3ca0a0}칭호{CE}　숍　등록。",
 27: "새　{C=3ca0a0}커스텀　파츠{CE}　숍　등록。",
 28: "새　{C=3ca0a0}개발　계획{CE}　숍　등록。",
 30: "시츄에이션　{C=3ca0a0}「%s」{CE}\\n추가됨。",
 31: "{C=3ca0a0}「%s」{CE}\\n→　{C=3ca0a0}「%s」{CE}　승진。",
 32: "새　{C=3ca0a0}시크릿{CE}　숍　등록。",
 34: "{C=3ca0a0}「%s」{CE}\\n튜닝　한계　개방。",
 35: "{C=3ca0a0}「%s」{CE}\\n튜닝　한계　개방。",
 36: "{C=3ca0a0}「%s」{CE}\\n성장　한계　개방。",
 38: "미션、　수고。",
 40: "신임　대장님이시군요。\\n오퍼레이터　{C=3ca0a0}엘렌{CE}입니다。",
 41: "{C=3ca0a0}ＨＯＷＴＯ{CE}를　먼저　읽으세요。",
 42: "조작・전술　정보　DB입니다。",
 43: "{C=3ca0a0}ＯＰＴＩＯＮ{CE}→{C=3ca0a0}ＨＯＷＴＯ{CE}에서　열람。",
 44: "대장님의　활약을　기원합니다。",
}

def need_syllables(ko_map):
    s=set()
    for t in ko_map.values():
        for ch in t:
            if "가"<=ch<="힣": s.add(ch)
    return sorted(s)

def build_kr_map(need, stable_path=None):
    """stable_path 지정 시 char→donor 배정을 파일에 고정(append-only).
    번역이 늘어도 기존 글자의 donor 코드가 안 바뀜 → 기존 파일 압축크기 불변(회귀 방지)."""
    import json as _json
    cs=G.charset()
    def dec(c):
        try: return struct.pack(">H",c).decode("cp932")
        except: return None
    used=set()
    for root,_,fs in os.walk(os.path.join(G.BASE,"csv_src")):
        for fn in fs:
            if fn.endswith(".csv"):
                try: used.update(io.open(os.path.join(root,fn),encoding="utf-8-sig").read())
                except: pass
    donors=[(ti,cs[ti]) for ti in range(len(cs)) if (lambda ch: ch and ch not in used and "一"<=ch<="鿿")(dec(cs[ti]))]
    donors=donors[len(donors)//3:]
    m={}
    if stable_path and os.path.exists(stable_path):
        m={k:tuple(v) for k,v in _json.load(io.open(stable_path,encoding="utf-8")).items()}
    taken={code for _,code in m.values()}
    free=[d for d in donors if d[1] not in taken]
    for ch in need:
        if ch not in m:
            if not free: raise RuntimeError("donor 부족")
            m[ch]=free.pop(0)
    if stable_path:
        _json.dump({k:list(v) for k,v in m.items()}, io.open(stable_path,"w",encoding="utf-8"), ensure_ascii=False)
    return {ch:m[ch] for ch in need}

def encode_text(s, kr):
    out=bytearray()
    for ch in s:
        if "가"<=ch<="힣": out+=struct.pack(">H",kr[ch][1])
        else: out+=ch.encode("cp932")
    return bytes(out)

def build_csv(orig_bytes, ko_map, kr):
    text=orig_bytes.decode("cp932"); sep="\r\n" if "\r\n" in text else "\n"
    rows=[ln.split(",") for ln in text.split(sep)]
    for ri,ko in ko_map.items():
        if ri<len(rows) and len(rows[ri])>2: rows[ri][2]=ko
    joined=sep.join(",".join(r) for r in rows)
    return encode_text(joined, kr)

def render2bpp(ch, font):
    img=Image.new("L",(24,24),0); ImageDraw.Draw(img).text((2,3),ch,fill=255,font=font)
    a=np.asarray(img); ys,xs=np.nonzero(a>40)
    if len(xs)==0: return np.zeros((14,14),np.uint8)
    crop=a[ys.min():ys.max()+1,xs.min():xs.max()+1]; h,w=crop.shape
    if h>14 or w>14:
        crop=np.asarray(Image.fromarray(crop).resize((min(w,14),min(h,14)),Image.LANCZOS)); h,w=crop.shape
    cv=np.zeros((14,14),np.uint8); oy,ox=(14-h)//2,(14-w)//2; cv[oy:oy+h,ox:ox+w]=crop
    q=np.zeros((14,14),np.uint8); q[cv>=64]=1; q[cv>=128]=2; q[cv>=192]=3
    return q

def main():
    apply = "--apply" in sys.argv
    # 원본 CSV(fileset 사본 하나 기준)
    src_bundle=src_ent=None
    for s in G.fsets():
        if s["nfiles"]==0: continue
        try: ents=G.fset_entries(s)
        except: continue
        for e in ents:
            if e["name"].endswith(CSVNAME): src_bundle,src_ent=s,e; break
        if src_ent: break
    orig=G.fset_read(src_bundle,src_ent)

    # 슬롯 맞을 때까지 우선순위 낮은 셀부터 제거
    ko=dict(KO)
    order=sorted(ko.keys())  # 낮은 행=우선(메뉴). 제거는 높은 행부터.
    dropped=[]
    while True:
        need=need_syllables(ko); kr=build_kr_map(need)
        newdata=build_csv(orig, ko, kr)
        comp=G.raic_compress(newdata)
        # room: 모든 사본 중 최소
        rooms=[]
        for s in G.fsets():
            if s["nfiles"]==0: continue
            try: ents=G.fset_entries(s)
            except: continue
            for e in ents:
                if not e["name"].endswith(CSVNAME): continue
                so=sorted(ents,key=lambda x:x["off"]); i=next(i for i,x in enumerate(so) if x["off"]==e["off"])
                rooms.append((so[i+1]["off"] if i+1<len(so) else s["size"])-e["off"])
        room=min(rooms)
        if len(comp)<=room or not ko: break
        drop=max(ko.keys()); dropped.append(drop); del ko[drop]
    print(f"번역 셀 {len(ko)}/{len(KO)}  usize={len(newdata)} comp={len(comp)}/{room} fit={len(comp)<=room}")
    if dropped: print(f"슬롯초과로 원문유지(행): {sorted(dropped)}")
    print(f"필요 음절 {len(need)}자, 왕복검증 {G.raic_decompress(comp)==newdata}")
    if not apply:
        print("[측정 전용] 적용하려면 --apply"); return

    # 폰트 준비(필요 글리프 주입본)
    krfont=ImageFont.truetype(KRFONT,13)
    if not os.path.exists(DST_ISO):
        print("ISO 복사..."); shutil.copyfile(G.ISO,DST_ISO)
    out=open(DST_ISO,"r+b")
    # 폰트 fileset
    gi=[s for s in G.fsets() if s["name"]=="gameinit"][0]; ge=G.fset_entries(gi)
    fe=[e for e in ge if e["name"].endswith("font_data_j14x14.fnt")][0]
    fp=bytearray(G.fset_read(gi,fe))
    for ch,(ti,code) in kr.items(): G.glyph_write(fp,ti,render2bpp(ch,krfont))
    fc=G.raic_compress(bytes(fp)); assert len(fc)<=fe["csize"], f"폰트초과 {len(fc)}>{fe['csize']}"
    bh=G.rd(G.FSET_LBA,gi["off"],0x14); _m,_n,tbl,_nt,_d=struct.unpack_from("<4s4I",bh,0)
    base=G.FSET_LBA*G.SECTOR+gi["off"]
    out.seek(base+fe["off"]); out.write(fc)
    out.seek(base+tbl+16*fe["idx"]+12); out.write(struct.pack("<I",len(fc)))
    print(f"폰트 fileset 패치 {len(fc)}/{fe['csize']}")
    # 폰트 gundam.dat
    gfi=G.gtree()[G.FONT_PATH]; gf=bytearray(G.rd(G.GDAT_LBA,gfi["off"],gfi["size"]))
    for ch,(ti,code) in kr.items(): G.glyph_write(gf,ti,render2bpp(ch,krfont))
    out.seek(G.GDAT_LBA*G.SECTOR+gfi["off"]); out.write(gf)
    # CSV 전 사본
    n=0
    for s in G.fsets():
        if s["nfiles"]==0: continue
        try: ents=G.fset_entries(s)
        except: continue
        for e in ents:
            if not e["name"].endswith(CSVNAME): continue
            nd=build_csv(G.fset_read(s,e), ko, kr); cp=G.raic_compress(nd)
            so=sorted(ents,key=lambda x:x["off"]); i=next(i for i,x in enumerate(so) if x["off"]==e["off"])
            room=(so[i+1]["off"] if i+1<len(so) else s["size"])-e["off"]
            if len(cp)>room: print(f"  [스킵]{s['name']} {len(cp)}>{room}"); continue
            bh=G.rd(G.FSET_LBA,s["off"],0x14); _m,_n2,tb,_nt,_d=struct.unpack_from("<4s4I",bh,0)
            b=G.FSET_LBA*G.SECTOR+s["off"]
            out.seek(b+e["off"]); out.write(cp)
            out.seek(b+tb+16*e["idx"]+8); out.write(struct.pack("<I",len(nd)))
            out.seek(b+tb+16*e["idx"]+12); out.write(struct.pack("<I",len(cp)))
            n+=1
    out.close()
    json.dump({c:[t,code] for c,(t,code) in kr.items()}, io.open(os.path.join(G.BASE,"kr_map_menu.json"),"w",encoding="utf-8"), ensure_ascii=False)
    print(f"CSV 사본 {n}개 패치, DONE: {DST_ISO}")

if __name__=="__main__": main()
