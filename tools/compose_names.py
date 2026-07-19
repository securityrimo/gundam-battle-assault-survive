# -*- coding: utf-8 -*-
"""tl_dict.json 최장일치 조합으로 _names_todo.json 번역. 커버리지 측정 + 슬롯검증.
완전조합된 것만 eboot_ui_short.json 에 병합(원문→한글)."""
import json, io, sys, re, os
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
BASE=os.path.dirname(os.path.abspath(__file__))
D={k:v for k,v in json.load(open(os.path.join(BASE,'tl_dict.json'),encoding='utf-8')).items() if not k.startswith('_')}
KEYS=sorted(D,key=len,reverse=True)
un=json.load(open(os.path.join(BASE,'_names_todo.json'),encoding='utf-8'))

def is_pass(c):  # 그대로 통과(숫자/영문/기호/구두점)
    return c.isascii() or c in '・ー（）()［］[]「」　 0123456789ⅠⅡⅢⅣⅤ％＆' or '０'<=c<='９' or 'Ａ'<=c<='ｚ'
PASS_MAP={'（':'(','）':')','・':'','ー':'','　':'','「':'','」':''}

def compose(jp):
    i=0; out=[]; ok=True
    while i<len(jp):
        for k in KEYS:
            if jp.startswith(k,i):
                out.append(D[k]); i+=len(k); break
        else:
            c=jp[i]
            if is_pass(c): out.append(PASS_MAP.get(c,c)); i+=1
            else: ok=False; i+=1
    return ''.join(out), ok

def est(ko):
    ko=ko.replace(' ','').replace('　','')
    return sum(1 if (c==' ' or ord(c)<128) else 2 for c in ko)

covered={}; uncov=[]; overflow=[]
for e in un:
    ko,ok=compose(e['jp'])
    if ok and ko.strip():
        if est(ko)<=e['slot']: covered[e['jp']]=ko
        else: overflow.append((e['slot'],est(ko),e['jp'],ko))
    else:
        uncov.append(e['jp'])
print(f'타깃 {len(un)} → 완전조합&슬롯적합 {len(covered)}, 슬롯초과 {len(overflow)}, 미커버 {len(uncov)}')
# 미커버 토큰 빈도(사전 보강용)
from collections import Counter
tok=Counter()
for jp in uncov:
    for m in re.findall(r'[ァ-ヿ]{2,}|[一-鿿]+', jp):
        if m not in D: tok[m]+=1
print('\n미커버 상위 토큰(사전 추가 후보):')
for t,c in tok.most_common(40): print(f'  {t}: {c}')
print('\n슬롯초과 샘플:')
for o in sorted(overflow,reverse=True)[:10]: print(f'  slot{o[0]} {o[1]}B | {o[2]} -> {o[3]}')

if '--write' in sys.argv:
    sp=os.path.join(BASE,'eboot_ui_short.json')
    d=json.load(open(sp,encoding='utf-8'))
    d.update(covered)
    json.dump(d,open(sp,'w',encoding='utf-8'),ensure_ascii=False,indent=0)
    print(f'\neboot_ui_short.json 병합: +{len(covered)} → 총 {len(d)}')
