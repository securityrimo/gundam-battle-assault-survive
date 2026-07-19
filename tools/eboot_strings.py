# -*- coding: utf-8 -*-
"""EBOOT_dec.elf 의 NUL 종료 SJIS 문자열 인벤토리(오프셋+슬롯길이).
in-place 교체용: 각 문자열은 다음 NUL까지가 슬롯. Korean 인코딩 ≤ 슬롯이어야 함."""
import sys, io, os, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE=os.path.dirname(os.path.abspath(__file__))
elf=open(os.path.join(BASE,"EBOOT_dec.elf"),"rb").read()

def is_sjis_lead(b): return 0x81<=b<=0x9f or 0xe0<=b<=0xfc
def is_sjis_trail(b): return 0x40<=b<=0x7e or 0x80<=b<=0xfc

# NUL 경계 문자열: [start..NUL). 유효 cp932 + ASCII 인쇄가능 + 제어({},%s,\n)
def scan():
    out=[]; i=0; n=len(elf)
    while i<n:
        if elf[i]==0: i+=1; continue
        j=i; ok=True; has_dbcs=False
        while j<n and elf[j]!=0:
            b=elf[j]
            if 0x20<=b<0x7f: j+=1
            elif is_sjis_lead(b) and j+1<n and is_sjis_trail(elf[j+1]): has_dbcs=True; j+=2
            elif b in (0x0a,0x0d): j+=1
            else: ok=False; break
        if ok and has_dbcs and j>i:
            raw=elf[i:j]
            try: t=raw.decode("cp932")
            except: t=None
            if t: out.append((i, j-i, t))   # (offset, slot_len(바이트, NUL 제외), text)
        i=j+1
    return out

strs=scan()
# 얼럿/시스템 다이얼로그 키워드
KEYS=["よろしいですか","しますか","ますか？","失敗","セーブ","ロード","データ","破損","中断",
      "削除","戻り","いいですか","メモリー","完了","登録","購入","雇用","取得","上書き","呼び出",
      "破棄","出撃","開始","受けなお","調整","インストール","接続","キャラクターメイキング","承認"]
alerts=[(o,l,t) for o,l,t in strs if any(k in t for k in KEYS)]
# 중복 텍스트 제거(첫 등장만) 하되 모든 오프셋 기록
from collections import defaultdict
by_text=defaultdict(list)
for o,l,t in alerts: by_text[t].append((o,l))
print(f"NUL종료 SJIS 문자열 {len(strs)}개, 얼럿후보 고유 {len(by_text)}개\n")
inv=[]
for t,ol in sorted(by_text.items(), key=lambda x:-len(x[0])):
    minlen=min(l for o,l in ol)
    inv.append({"text":t,"minlen":minlen,"offs":ol})
    print(f"[slot={minlen:3d} x{len(ol)}] {t.replace(chr(10),'/')[:56]}")
json.dump(inv, io.open(os.path.join(BASE,"eboot_alerts.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\n저장: eboot_alerts.json ({len(inv)}개)")
