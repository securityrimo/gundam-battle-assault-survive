# -*- coding: utf-8 -*-
"""GAS 한글 통합 빌더 v3 (재패커 기반, task #9).
fileset.dat를 0x800 정렬 유지 재패킹(패딩 회수) → 폰트/CSV를 슬롯 제약 없이 교체.
폰트 압축본이 원본보다 작아 CSV 증가분 상쇄 → 총 크기 ≤ 원본이면 ISO 재빌드 불필요.
EBOOT 얼럿 in-place, gundam.dat 폰트 in-place(비로드본이나 일관성).
"""
import sys, io, os, struct, json, shutil, csv
import numpy as np
from PIL import ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gaslib as G
import patch_menu as PM
import fileset_repack as R

DST_ISO = os.path.join(os.path.dirname(G.ISO), "Gundam Assault Survive (Korean_PoC).iso")
KRFONT  = r"C:\Windows\Fonts\malgunbd.ttf"
EBOOT_LBA, ENC_SIZE = 560, 5142592
R.BUNDLE_ALIGN = 0x800   # 섹터 정렬 필수(0x40은 크래시 확인)

import glob
# cp932 불가 문자 → 안전 대체
_NONCP={"·":"・","–":"-","—":"-","―":"ー","“":"\"","”":"\"","‘":"'","’":"'","…":"...","∼":"～","•":"・","※":"※"}
def sanitize(ko):
    ko=ko.replace("​","").replace(",", "、")
    out=[]
    for ch in ko:
        if "가"<=ch<="힣": out.append(ch); continue
        ch=_NONCP.get(ch,ch)
        try:
            ch.encode("cp932"); out.append(ch)
        except Exception:
            pass  # 남은 비cp932 문자는 제거(구조 안전)
    return "".join(out)
def hangul(s): return {c for c in s if "가"<=c<="힣"}

def load_all_worksheets():
    """translate/*.csv 전부 → {basename: {(row,col):ko}}. fileset 사본 있는 것만 대상은 main()에서 필터."""
    tgt={}
    for wp in glob.glob(os.path.join(G.BASE,"translate","*.csv")):
        rows=list(csv.reader(io.open(wp,encoding="utf-8-sig",newline="")))
        if not rows or rows[0][:1]!=["key"]: continue
        base=rows[1][0].split("|")[0].split("/")[-1]
        d={}
        for r in rows[1:]:
            if len(r)<5 or not r[4].strip(): continue
            _p,ri,ci=r[0].rsplit("|",2); d[(int(ri),int(ci))]=sanitize(r[4])
        tgt[base]=d
    return tgt

# Codex 최종 한국어 CSV(재조립본). 헤더/필드명 원문 보존 확인됨. 이걸 직접 인코딩.
KO_DIR=os.path.join(G.BASE,"csv_ko_utf8")
KO_PATHS={os.path.basename(p):p for p in glob.glob(os.path.join(KO_DIR,"**","*.csv"),recursive=True)}
_SKIP=set(x for x in os.environ.get("GAS_SKIP","").split(",") if x)  # 원문(일본어) 유지할 CSV

def main():
    alerts=json.load(io.open(os.path.join(G.BASE,"eboot_alerts.json"),encoding="utf-8"))
    alert_ko=json.load(io.open(os.path.join(G.BASE,"tl_alerts.json"),encoding="utf-8"))
    # EBOOT UI 워크시트(eboot_ui.csv 번역) + 오프셋(eboot_ui.json). {first_off: ko}
    ui_by_off={}
    uip=os.path.join(G.BASE,"translate","eboot_ui.csv")
    if os.path.exists(uip):
        for row in csv.DictReader(io.open(uip,encoding="utf-8-sig",newline="")):
            ko=row.get("번역","").strip()
            if ko: ui_by_off[int(row["key"].split("|")[1])]=sanitize(ko)
    ui_json={e["offs"][0][0]:e for e in json.load(io.open(os.path.join(G.BASE,"eboot_ui.json"),encoding="utf-8"))} if os.path.exists(os.path.join(G.BASE,"eboot_ui.json")) else {}
    # 슬롯초과 이름 축약 오버라이드(원문→짧은 한글)
    ui_short={}
    _sp=os.path.join(G.BASE,"eboot_ui_short.json")
    if os.path.exists(_sp): ui_short={k:sanitize(v) for k,v in json.load(io.open(_sp,encoding="utf-8")).items()}
    if os.environ.get("GAS_NO_SHORT"): print("ui_short: 비활성(이분테스트)"); ui_short={}
    _h=os.environ.get("GAS_SHORT_HALF")
    if _h in ("1","2"):
        _ks=sorted(ui_short); _mid=len(_ks)//2
        ui_short={k:ui_short[k] for k in (_ks[:_mid] if _h=="1" else _ks[_mid:])}
        print(f"ui_short 이분: half{_h} → {len(ui_short)}개")
    _n=os.environ.get("GAS_SHORT_N")
    if _n:
        _ks=sorted(ui_short)[:int(_n)]
        ui_short={k:ui_short[k] for k in _ks}
        print(f"ui_short 이분: 앞 {len(ui_short)}개")
    _ex=os.environ.get("GAS_SHORT_EXCL")
    if _ex:
        _ks=sorted(ui_short)
        _drop={_ks[int(i)] for i in _ex.split(",")}
        ui_short={k:v for k,v in ui_short.items() if k not in _drop}
        print(f"ui_short 제외 {_ex} → {len(ui_short)}개")
    # ui_short는 (1)슬롯초과 축약 (2)번역CSV에 없는 미번역 문자열 추가 겸용. 원문→오프셋 주입.
    _t2o={e["text"]:e["offs"][0][0] for e in json.load(io.open(os.path.join(G.BASE,"eboot_ui.json"),encoding="utf-8"))} if os.path.exists(os.path.join(G.BASE,"eboot_ui.json")) else {}
    for _jp,_ko in ui_short.items():
        if _jp in _t2o and _t2o[_jp] not in ui_by_off: ui_by_off[_t2o[_jp]]=_ko

    need=set()
    for p in KO_PATHS.values():
        for r in csv.reader(io.open(p,encoding="utf-8-sig",newline="")):
            for c in r: need|=hangul(sanitize(c))
    for t in alert_ko:
        if t: need|=hangul(t)
    for t in ui_by_off.values(): need|=hangul(t)
    for t in ui_short.values(): need|=hangul(t)
    # FES 번역 음절
    import fes_patch as FP
    fes_tl=FP.load_tl()
    need|=FP.hangul_of(fes_tl)
    # locate 표시명 음절
    import locate_tl as LT
    need|=LT.need_syllables()
    # 단일 한자 칭호(추출 누락, 오프셋 직접패치) 음절
    import eboot_titles_extra as ETX
    for _o,_c in ETX.get_patches(): need|=hangul(_c)
    kr=PM.build_kr_map(sorted(need), os.path.join(G.BASE,"kr_map_stable.json"))
    print(f"글로벌 음절 {len(need)}자 (csv_ko_utf8 기준)")

    def enc_csv(s):
        out=bytearray()
        for ch in s:
            if "가"<=ch<="힣": out+=struct.pack(">H",kr[ch][1])
            else: out+=ch.encode("cp932")
        return bytes(out)
    def enc_eboot(s):
        out=bytearray()
        for ch in s:
            if ch=="\n": out.append(0x0a)
            elif "가"<=ch<="힣": out+=struct.pack(">H",kr[ch][1])
            else: out+=ch.encode("cp932")
        return bytes(out)
    def build_csv_uncomp(orig_bytes, ko_by_rc):
        text=orig_bytes.decode("cp932"); sep="\r\n" if "\r\n" in text else "\n"
        rows=[ln.split(",") for ln in text.split(sep)]
        for (ri,ci),ko in ko_by_rc.items():
            if ri<len(rows) and ci<len(rows[ri]): rows[ri][ci]=ko
        return enc_csv(sep.join(",".join(r) for r in rows))

    # ---- 폰트 패치본(압축) ----
    krfont=ImageFont.truetype(KRFONT,13)
    def inject(fnt):
        for ch,(ti,code) in kr.items(): G.glyph_write(fnt,ti,PM.render2bpp(ch,krfont))
    gi=[s for s in G.fsets() if s["name"]=="gameinit"][0]
    fe=[e for e in G.fset_entries(gi) if e["name"].endswith("font_data_j14x14.fnt")][0]
    fpl=bytearray(G.fset_read(gi,fe)); inject(fpl)
    font_comp=G.raic_compress(bytes(fpl))
    print(f"폰트 {len(kr)}글리프 압축 {len(font_comp)} (원본csize {fe['csize']})")

    # ---- 재패커 new_files 구성: {bundle_name:{file_basename:(stored,usize)}} ----
    fs=R.Fileset(G.ISO)
    # 파일명은 FSTS 전체경로(e['name']). 대상 basename → 각 번들 사본
    def full_names(basename):
        res=[]  # (bundle_name, file_full_name)
        for b in fs.bundles:
            info=fs.parse_bundle_files(b)
            if not info: continue
            for f in info["files"]:
                if f["name"].endswith(basename): res.append((b["name"], f["name"], f))
        return res

    def fit(stored, orig_csize):
        # 줄어든 파일은 0 패딩(RAIC는 usize까지만 읽음)해 원본 크기 유지 → 뒤 파일 안 밀림
        return stored + b"\x00"*(orig_csize-len(stored)) if len(stored)<orig_csize else stored

    new_files={}
    # 폰트
    for bn,fn,f in full_names("font_data_j14x14.fnt"):
        new_files.setdefault(bn,{})[fn]=(fit(font_comp,f["csize"]), len(fpl))
    # CSV들: Codex 최종본(csv_ko_utf8) 직접 인코딩. 성장(초과) 파일은 공백제거→끝셀 원문복원으로 원본 csize에 맞춤(성장 0).
    for basename,kp in sorted(KO_PATHS.items()):
        if basename in _SKIP:
            print(f"  {basename}: SKIP(원문 유지)"); continue
        copies=full_names(basename)
        if not copies:
            print(f"  {basename}: fileset 사본 없음(event=gundam.dat 별도)"); continue
        bn0,fn0,f0=copies[0]
        b0=next(b for b in fs.bundles if b["name"]==bn0)
        raw0=fs.data[b0["doff"]+f0["off"]:b0["doff"]+f0["off"]+f0["csize"]]
        orig=G.raic_decompress(bytes(raw0)) if raw0[:4]==b" 3;1" else bytes(raw0)
        sep="\r\n" if b"\r\n" in orig else "\n"
        # charamake/btn: CRLF면 초과 → LF로 맞춤(행당 1B 절약, charamake 인게임 검증됨).
        if basename in ("charamake_data.csv","btn.csv"): sep="\n"
        korows=list(csv.reader(io.open(kp,encoding="utf-8-sig",newline="")))
        try:
            orows=[ln.split(",") for ln in orig.decode("cp932").split(sep)]
        except UnicodeDecodeError:
            print(f"  {basename}: 원본 cp932 아님(다른 포맷) → SKIP"); continue
        n=len(korows)
        def encode(revert, strip):  # revert=원문복원할 행 집합
            rows=[]
            for ri in range(n):
                if ri in revert:
                    rows.append(orows[ri] if ri<len(orows) else [])
                else:
                    rows.append([(sanitize(c).replace(" ","").replace("　","") if strip else sanitize(c)) for c in korows[ri]])
            return enc_csv(sep.join(",".join(r) for r in rows))
        kcount=lambda ri: sum(1 for c in korows[ri] for ch in c if "가"<=ch<="힣")
        cand=sorted([ri for ri in range(n) if kcount(ri)>0], key=kcount)  # 한글 적은 행부터
        revert=set(); strip=False
        unc=encode(revert,strip); comp=G.raic_compress(unc)
        if len(comp)>f0["csize"]:
            strip=True; unc=encode(revert,strip); comp=G.raic_compress(unc)
        ci=0
        while len(comp)>f0["csize"] and ci<len(cand):   # 짧은 셀부터 원문복원(밀림 방지)
            for _ in range(3):
                if ci<len(cand): revert.add(cand[ci]); ci+=1
            unc=encode(revert,strip); comp=G.raic_compress(unc)
        note=("공백제거" if strip else "패딩")+(f"+{len(revert)}행원문" if revert else "")
        print(f"  {basename}: comp {f0['csize']}->{len(comp)} [{note}] {'OK' if len(comp)<=f0['csize'] else '⚠초과→원본유지'} x{len(copies)}")
        if len(comp)>f0["csize"]: continue  # 성장 금지: 초과 시 원본(일본어) 유지
        for bn,fn,f in copies:
            new_files.setdefault(bn,{})[fn]=(fit(comp,f["csize"]), len(unc))

    # ---- GIM: 다이얼로그 버튼(はい/いいえ/戻る/OK → 예/아니오/뒤로/OK) ----
    import patch_dialog_gim as PD
    GIM_TARGETS=["data/menu/dialog/2d_dialog_1.gim"]
    for gpath in GIM_TARGETS:
        cnt=0
        for b in fs.bundles:
            info=fs.parse_bundle_files(b)
            if not info: continue
            for f in info["files"]:
                if f["name"]==gpath:
                    raw=fs.data[b["doff"]+f["off"]:b["doff"]+f["off"]+f["csize"]]
                    orig=G.raic_decompress(bytes(raw)) if raw[:4]==b" 3;1" else bytes(raw)
                    patched,_,_,_=PD.patch(orig)
                    comp=G.raic_compress(patched)
                    new_files.setdefault(b["name"],{})[f["name"]]=(fit(comp,f["csize"]), len(patched))
                    cnt+=1
        print(f"  GIM {gpath}: {cnt}사본 재도색")

    # ---- GIM: 파일럿 생성/관리 라벨 + 스탯 아틀라스(sel_paramoji, 4번들 공용) ----
    import patch_cham_gim as PCH
    import patch_paramoji as PMJ
    import patch_cpsel as PCS
    import patch_hensei as PHS
    # 샵 GIM(shop_moji_*)은 patch_shop.py 결과를 기본 포함한다.
    # 이분 테스트가 필요할 때만 GAS_NO_SHOP=1로 비활성화한다.
    GIM_LABELS={ **{k:(PCH.patch,v) for k,v in PCH.TARGETS.items()},
                 "sel_paramoji.gim": (PCH.patch, PMJ.LABELS),
                 "cp_sel_1.gim": (PCS.patch, PCS.LABELS),
                 "2d_hensei_name.gim": (PHS.patch, PHS.LABELS_NAME),
                 "2d_hensei_03.gim": (PHS.patch, PHS.LABELS_03) }
    if not os.environ.get("GAS_NO_SHOP"):
        import patch_shop as PSH
        GIM_LABELS.update(PSH.TARGETS)
    # VS 배틀: 모드 버튼, REGULATION 항목, 결정/초기화 및 편성 선택 라벨.
    # 공용 GIM이 scene_vsbattle_rule/edit/plat에 중복되므로 basename 기준으로
    # 발견되는 모든 사본을 같은 결과로 재도색한다.
    if not os.environ.get("GAS_NO_VS"):
        import patch_vs as PVS
        GIM_LABELS.update(PVS.TARGETS)
    for b in fs.bundles:
        info=fs.parse_bundle_files(b)
        if not info: continue
        for f in info["files"]:
            base=f["name"].split("/")[-1]
            if base in GIM_LABELS:
                raw=fs.data[b["doff"]+f["off"]:b["doff"]+f["off"]+f["csize"]]
                orig=G.raic_decompress(bytes(raw)) if raw[:4]==b" 3;1" else bytes(raw)
                _fn,_labs=GIM_LABELS[base]
                patched,_,_,_=_fn(orig,_labs)
                comp=G.raic_compress(patched)
                ok="OK" if len(comp)<=f["csize"] else "⚠초과"
                print(f"  GIM {base}: comp {f['csize']}->{len(comp)} {ok}")
                if len(comp)<=f["csize"]:
                    new_files.setdefault(b["name"],{})[f["name"]]=(fit(comp,f["csize"]), len(patched))

    # ---- GIM: 메인메뉴 우측 대시보드(2d_myroom_01) 라벨 한글화 ----
    # myroom_00.ark TXOS의 실제 고정 crop 좌표를 사용한다.
    import patch_myroom_gim as PMR
    MY_TARGET="ui/main_menu/2d_myroom_01.gim"
    cnt=0
    if not os.environ.get("GAS_NO_MYROOM"):
      for b in fs.bundles:
        info=fs.parse_bundle_files(b)
        if not info: continue
        for f in info["files"]:
            if f["name"].endswith("2d_myroom_01.gim"):
                raw=fs.data[b["doff"]+f["off"]:b["doff"]+f["off"]+f["csize"]]
                orig=G.raic_decompress(bytes(raw)) if raw[:4]==b" 3;1" else bytes(raw)
                patched,_,_,_=PMR.patch(orig)
                comp=G.raic_compress(patched)
                ok="OK" if len(comp)<=f["csize"] else "⚠초과"
                print(f"  GIM {f['name']}: comp {f['csize']}->{len(comp)} {ok}")
                if len(comp)<=f["csize"]:
                    new_files.setdefault(b["name"],{})[f["name"]]=(fit(comp,f["csize"]), len(patched))
                    cnt+=1
    print(f"  GIM 대시보드: {cnt}장 재도색")

    # ---- GIM: 시추에이션 시작 연출 미션명 181종 ----
    # intro_<mission>.gim 자체에 일본어 붓글씨가 박혀 있으므로 EBOOT 제목
    # 문자열만 바꿔서는 시작 화면이 변하지 않는다.
    import patch_situation_titles as PST
    stap=stskip=stsmall=0
    if os.environ.get("GAS_NO_SITUATION_TITLE"):
        print("  GIM 시추에이션 제목: 비활성(GAS_NO_SITUATION_TITLE)")
    else:
      for b in fs.bundles:
        if not b["name"].endswith("_o"):
            continue
        mission=b["name"][:-2]
        title=PST.TITLES.get(mission)
        if not title:
            continue
        info=fs.parse_bundle_files(b)
        if not info:
            continue
        target="intro_"+mission+".gim"
        for f in info["files"]:
            if not f["name"].endswith(target):
                continue
            raw=fs.data[b["doff"]+f["off"]:b["doff"]+f["off"]+f["csize"]]
            orig=G.raic_decompress(bytes(raw)) if raw[:4]==b" 3;1" else bytes(raw)
            comp=None
            used_px=42
            for font_px in (42,40,38,36,34,32,30,28,26,24):
                patched,_,_,_=PST.patch(orig,title,font_px)
                trial=G.raic_compress(patched)
                if len(trial)<=f["csize"]:
                    comp=trial
                    used_px=font_px
                    break
            if comp is None:
                stskip+=1
                print(f"  ⚠ 시추에이션 제목 초과: {mission} {title}")
                continue
            new_files.setdefault(b["name"],{})[f["name"]]=(fit(comp,f["csize"]), len(patched))
            stap+=1
            if used_px<42:
                stsmall+=1
    print(f"  GIM 시추에이션 제목: {stap}/{len(PST.TITLES)}장 적용 "
          f"(축소 {stsmall}, 초과스킵 {stskip})")

    # ---- locate: HUD 표시명(col2) 번들별 in-place (동명이본 안전) ----
    lap=lcnt=lskip=0
    if os.environ.get("GAS_NO_LOCATE"): print("locate: 비활성(GAS_NO_LOCATE)")
    else:
     for b in fs.bundles:
        info=fs.parse_bundle_files(b)
        if not info: continue
        for f in info["files"]:
            if "/locate/" not in f["name"] or not f["name"].endswith(".csv"): continue
            raw=fs.data[b["doff"]+f["off"]:b["doff"]+f["off"]+f["csize"]]
            orig=G.raic_decompress(bytes(raw)) if raw[:4]==b" 3;1" else bytes(raw)
            try: txt=orig.decode("cp932")
            except UnicodeDecodeError: continue
            new,nn=LT.tl_locate_text(txt)
            if nn==0: continue
            unc=enc_csv(new)
            comp=G.raic_compress(unc)
            if len(comp)>f["csize"]:
                unc=enc_csv(new.replace("　","")); comp=G.raic_compress(unc)
            if len(comp)>f["csize"]: lskip+=1; continue
            new_files.setdefault(b["name"],{})[f["name"]]=(fit(comp,f["csize"]), len(unc))
            lap+=nn; lcnt+=1
    print(f"locate {lcnt}파일 {lap}셀 적용 (초과스킵 {lskip})")

    # ---- FES: 전투 브리핑/무전 풀 문자열 in-place ----
    if os.environ.get("GAS_NO_FES"): print("FES: 비활성(GAS_NO_FES)"); fes_tl={}
    if fes_tl:
        fes_entries=FP.load_entries()
        fap=fsk=fover=fcnt=fstrip=0
        def enc_fes(s):
            out=bytearray()
            for ch in s:
                if ch=="\n": out.append(0x0a)
                elif "가"<=ch<="힣": out+=struct.pack(">H",kr[ch][1])
                else:
                    try: out+=ch.encode("cp932")
                    except Exception: pass
            return bytes(out)
        for b in fs.bundles:
            info=fs.parse_bundle_files(b)
            if not info: continue
            for f in info["files"]:
                ents=fes_entries.get(f["name"])
                if not ents: continue
                if not any(e["text"] in fes_tl for e in ents): continue
                raw=fs.data[b["doff"]+f["off"]:b["doff"]+f["off"]+f["csize"]]
                orig=G.raic_decompress(bytes(raw)) if raw[:4]==b" 3;1" else bytes(raw)
                # 1차: 전량 적용. 초과 시 2차: 파일 전체 공백제거. 그래도 초과 시 그리디(긴 번역 제외).
                nd,ap,sk=FP.patch_fes(orig,ents,fes_tl,enc_fes)
                comp=G.raic_compress(nd)
                if len(comp)>f["csize"]:
                    nd2,ap2,sk2=FP.patch_fes(orig,ents,fes_tl,enc_fes,strip_all=True)
                    comp2=G.raic_compress(nd2)
                    if len(comp2)<=f["csize"]:
                        nd,ap,sk,comp=nd2,ap2,sk2,comp2
                        fstrip+=1
                if len(comp)<=f["csize"]:
                    new_files.setdefault(b["name"],{})[f["name"]]=(fit(comp,f["csize"]), len(nd))
                    fap+=ap; fsk+=sk; fcnt+=1
                    continue
                # 그리디: 여전히 초과 시 긴 번역부터 제외
                cand=sorted([e for e in ents if e["text"] in fes_tl], key=lambda e:-e["len"])
                drop=1
                while drop<len(cand):
                    use={e["text"] for e in cand[drop:]}
                    tl_sub={k:v for k,v in fes_tl.items() if k in use}
                    nd,ap,sk=FP.patch_fes(orig,ents,tl_sub,enc_fes,strip_all=True)
                    if ap==0: break
                    comp=G.raic_compress(nd)
                    if len(comp)<=f["csize"]:
                        new_files.setdefault(b["name"],{})[f["name"]]=(fit(comp,f["csize"]), len(nd))
                        fap+=ap; fsk+=sk; fcnt+=1; fover+=1
                        break
                    drop+=1
        print(f"FES {fcnt}파일 {fap}문자열 적용 (슬롯스킵 {fsk}, 공백제거파일 {fstrip}, 부분적용 파일 {fover})")

    # ---- 최소변경 재패킹(이동 0: 모든 번들 원위치, 줄어든 파일 패딩으로 밀림 0) ----
    try:
        out_fs, changed = fs.repack_minimal(new_files)
    except RuntimeError as ex:
        print(f"❌ {ex}"); return
    print(f"최소변경 재패킹: {changed}개 번들 제자리, 이동·밀림 0")
    if "--measure" in sys.argv:
        print("[측정 전용]"); return

    # ---- ISO 재생성 ----
    print("원본→PoC ISO 복사(854MB)..."); shutil.copyfile(G.ISO, DST_ISO)
    out=open(DST_ISO,"r+b")
    # fileset.dat 통째 기록(같은 크기)
    out.seek(R.FSET_LBA*R.SECTOR); out.write(out_fs[:R.TOTAL])
    print("fileset.dat 재패킹본 기록")
    # EBOOT 얼럿
    elf=bytearray(open(os.path.join(G.BASE,"EBOOT_dec.elf"),"rb").read())
    ap=sk=0
    for entry,ko in zip(alerts, alert_ko):
        if not ko: continue
        slot=min(l for o,l in entry["offs"]); b=enc_eboot(ko)
        if len(b)>slot: b=enc_eboot(ko.replace("　",""))
        if len(b)>slot: sk+=1; continue
        for off,ln in entry["offs"]:
            elf[off:off+len(b)]=b
            for k in range(off+len(b),off+ln): elf[k]=0
        ap+=1
    print(f"EBOOT 얼럿 {ap}적용/{sk}스킵")
    # EBOOT UI 문자열(eboot_ui.csv 번역) in-place
    # 엔진 내부식별자(CSV 컬럼명/제어값 비교용) — 번역 금지. テキスト1/2, なし(이벤트 스크롤값)
    UI_BLACKLIST={3712808,3712820,3658692}
    uap=usk=0
    for off0,ko in ui_by_off.items():
        if off0 in UI_BLACKLIST: continue
        e=ui_json.get(off0)
        if not e: continue
        if e["text"] in ui_short: ko=ui_short[e["text"]]  # 축약본 우선
        slot=e["slot"]; b=enc_eboot(ko)
        if len(b)>slot: b=enc_eboot(ko.replace("　","").replace(" ",""))  # 공백 제거 폴백
        if len(b)>slot:
            usk+=1
            if os.environ.get("GAS_DBG"): print(f"  [UIskip] slot{slot} {len(b)}B | {e['text'][:20]} -> {ko[:20]}")
            continue
        for off,ln in e["offs"]:
            elf[off:off+len(b)]=b
            for k in range(off+len(b),off+ln): elf[k]=0
        uap+=1
    print(f"EBOOT UI {uap}적용/{usk}스킵 (번역입력 {len(ui_by_off)})")
    # 단일 한자 칭호(추출 누락) 오프셋 직접 패치: 각 slot=2B, 한글 1음절
    tap=0
    for off,ch in ETX.get_patches():
        b=enc_eboot(ch)
        if len(b)<=2 and off+2<=len(elf):
            elf[off:off+len(b)]=b
            for k in range(off+len(b),off+2): elf[k]=0
            tap+=1
    print(f"EBOOT 단일한자 칭호 {tap}개 직접패치")
    out.seek(EBOOT_LBA*R.SECTOR); out.write(bytes(elf)+b"\x00"*(ENC_SIZE-len(elf)))
    # gundam.dat 폰트(in-place 동일크기; 비로드본이나 일관성)
    gfi=G.gtree()[G.FONT_PATH]
    if gfi["size"]==len(fpl):
        out.seek(G.GDAT_LBA*G.SECTOR+gfi["off"]); out.write(bytes(fpl))
    out.close()
    json.dump({c:[t,code] for c,(t,code) in kr.items()}, io.open(os.path.join(G.BASE,"kr_map_global.json"),"w",encoding="utf-8"), ensure_ascii=False)
    print("DONE:", DST_ISO)

if __name__=="__main__": main()
