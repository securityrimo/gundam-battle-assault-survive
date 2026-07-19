# -*- coding: utf-8 -*-
"""얼럿 문자열 위치 탐색 + charamake_data.csv in-place 여유 조사."""
import sys, io, os, struct, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gaslib as G

# ---- 1) 얼럿 키워드를 EBOOT_dec.elf 하드코딩 SJIS에서 탐색 ----
elf=open(os.path.join(G.BASE,"EBOOT_dec.elf"),"rb").read()
KEYS=["よろしいですか","しますか","ますか？","失敗","セーブ","ロード","データ",
      "破損","中断","削除","開始します","戻り","いいですか","メモリー"]
# SJIS 문자열 추출: 연속된 유효 cp932 구간
def sjis_strings(buf, minlen=6):
    out=[]; i=0; n=len(buf)
    while i<n:
        j=i; s=bytearray()
        while j<n:
            b=buf[j]
            if 0x20<=b<0x7f: s.append(b); j+=1
            elif (0x81<=b<=0x9f or 0xe0<=b<=0xfc) and j+1<n and (0x40<=buf[j+1]<=0x7e or 0x80<=buf[j+1]<=0xfc):
                s+=buf[j:j+2]; j+=2
            else: break
        if len(s)>=minlen:
            try: t=s.decode("cp932")
            except: t=None
            if t: out.append((i,t))
        i=max(j+1,i+1)
    return out
strs=sjis_strings(elf)
hits=[(o,t) for o,t in strs if any(k in t for k in KEYS)]
print(f"EBOOT SJIS 문자열 {len(strs)}개 중 얼럿후보 {len(hits)}개 (상위 30):")
seen=set()
for o,t in hits[:60]:
    if t in seen: continue
    seen.add(t)
    print(f"  0x{o:06x}  {t[:50]}")

# ---- 2) 얼럿 관련 CSV/파일이 gundam.dat 트리에 있나 ----
print("\n트리에서 alert/warning/dialog/message/common 관련 파일:")
for p in sorted(G.gtree()):
    low=p.lower()
    if any(k in low for k in ["alert","warn","dialog","caution","common/","/msg","message","notice"]):
        if p.endswith((".csv",".txt",".dat",".bin")): print("  ",p, G.gtree()[p]["size"])

# ---- 3) charamake_data.csv in-place 여유 ----
print("\ncharamake_data.csv fileset 사본:")
for s in G.fsets():
    if s["nfiles"]==0: continue
    try: ents=G.fset_entries(s)
    except: continue
    for e in ents:
        if e["name"].endswith("charamake_data.csv"):
            so=sorted(ents,key=lambda x:x["off"]); i=next(i for i,x in enumerate(so) if x["off"]==e["off"])
            room=(so[i+1]["off"] if i+1<len(so) else s["size"])-e["off"]
            print(f"  {s['name']}: usize={e['usize']} csize={e['csize']} room={room}")
