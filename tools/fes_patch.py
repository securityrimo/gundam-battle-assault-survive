# -*- coding: utf-8 -*-
"""FES 풀 문자열 in-place 한글 치환 도우미.
translate/fes_tl.csv(번역 열) + fes_strings.json 기반. 각 문자열 encoded<=len, NUL 패딩."""
import io, os, json, csv, struct
BASE=os.path.dirname(os.path.abspath(__file__))

def load_tl():
    p=os.path.join(BASE,'translate','fes_tl.csv')
    tl={}
    if os.path.exists(p):
        for r in csv.DictReader(io.open(p,encoding='utf-8-sig',newline='')):
            ko=(r.get('번역') or '').strip()
            if ko: tl[r['원문']]=ko
    # 이분탐색용: GAS_FES_HALF=1|2 (절반) 또는 GAS_FES_N=<개수> (정렬 앞 N개)
    h=os.environ.get('GAS_FES_HALF')
    if h in ('1','2'):
        ks=sorted(tl); mid=len(ks)//2
        sel=ks[:mid] if h=='1' else ks[mid:]
        tl={k:tl[k] for k in sel}
        print(f'FES 이분: half{h} → {len(tl)}개')
    n=os.environ.get('GAS_FES_N')
    if n:
        ks=sorted(tl)[:int(n)]
        tl={k:tl[k] for k in ks}
        print(f'FES 이분: 앞 {len(tl)}개')
    return tl

def load_entries():
    by_file={}
    for e in json.load(open(os.path.join(BASE,'fes_strings.json'),encoding='utf-8')):
        by_file.setdefault(e['file'],[]).append(e)
    return by_file

def hangul_of(tl):
    s=set()
    for ko in tl.values():
        for c in ko:
            if '가'<=c<='힣': s.add(c)
    return s

def patch_fes(data, entries, tl, enc, strip_all=False):
    """enc(str)->bytes (도너 인코딩). strip_all=True면 모든 한글 번역의 공백 제거(파일 용량 절약).
    반환 (new_bytes, applied, skipped)"""
    out=bytearray(data); ap=sk=0
    for e in entries:
        ko=tl.get(e['text'])
        if not ko: continue
        if strip_all: ko=ko.replace(' ','').replace('　','')
        b=enc(ko)
        if len(b)>e['len']:
            b=enc(ko.replace(' ','').replace('　',''))
        if len(b)>e['len']: sk+=1; continue
        off=e['off']
        out[off:off+len(b)]=b
        for k in range(off+len(b), off+e['len']): out[k]=0
        ap+=1
    return bytes(out), ap, sk
