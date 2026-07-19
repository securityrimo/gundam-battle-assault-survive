# -*- coding: utf-8 -*-
"""EBOOT_dec.elf 의 번역대상 UI 문자열 전수 추출(NUL종료 SJIS, 가나/한자 포함).
얼럿(이미 처리) 외 미션명·소속군·메뉴·버튼·메시지 등. 워크시트로 저장(Codex 번역용)."""
import sys, io, os, json, re
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
BASE=os.path.dirname(os.path.abspath(__file__))
elf=open(os.path.join(BASE,"EBOOT_dec.elf"),"rb").read()

def is_lead(b): return 0x81<=b<=0x9f or 0xe0<=b<=0xfc
def is_trail(b): return 0x40<=b<=0x7e or 0x80<=b<=0xfc
jp=re.compile(r"[぀-ゟ゠-ヿ一-鿿]")   # 히라가나/가타카나/한자

def scan():
    out=[]; i=0; n=len(elf)
    while i<n:
        if elf[i]==0: i+=1; continue
        j=i; ok=True; has_jp=False
        while j<n and elf[j]!=0:
            b=elf[j]
            if 0x20<=b<0x7f: j+=1
            elif is_lead(b) and j+1<n and is_trail(elf[j+1]): j+=2
            elif b in (0x0a,0x0d): j+=1
            else: ok=False; break
        if ok and j>i:
            raw=elf[i:j]
            try: t=raw.decode("cp932")
            except: t=None
            if t and jp.search(t): out.append((i,j-i,t))
        i=j+1
    return out

strs=scan()
# 코드/포맷 잡음 완화: 최소 슬롯 4, 최대 220
strs=[(o,l,t) for o,l,t in strs if 4<=l<=220]
# 텍스트별 최소슬롯·오프셋들
from collections import defaultdict
by=defaultdict(list)
for o,l,t in strs: by[t].append((o,l))
uniq=sorted(by.items(), key=lambda kv:-min(l for _,l in kv[1]))
print(f"EBOOT 번역대상 UI 문자열: 총출현 {len(strs)}, 고유 {len(by)}")

# 워크시트 저장 (key=첫오프셋, slot, note(코드), 원문, 번역)
CODE=re.compile(r"\{[^}]*\}|%[sd]")
import csv as _csv
outp=os.path.join(BASE,"translate","eboot_ui.csv")
with io.open(outp,"w",encoding="utf-8-sig",newline="") as f:
    w=_csv.writer(f); w.writerow(["key","slot","note","원문","번역"])
    for t,offs in uniq:
        o0=offs[0][0]; slot=min(l for _,l in offs)
        note=" ".join(sorted(set(CODE.findall(t)))) + (" NL" if "\n" in t else "")
        w.writerow([f"eboot|{o0}", slot, note.strip(), t, ""])
print(f"워크시트 저장: {outp}")
# eboot 오프셋 매핑도 json으로(패치용)
json.dump([{"text":t,"slot":min(l for _,l in offs),"offs":offs} for t,offs in uniq],
          io.open(os.path.join(BASE,"eboot_ui.json"),"w",encoding="utf-8"), ensure_ascii=False)
# 길이 분포
import statistics
lens=[min(l for _,l in offs) for t,offs in uniq]
print(f"슬롯 길이: 합 {sum(lens)}, 평균 {statistics.mean(lens):.0f}, 최대 {max(lens)}")
