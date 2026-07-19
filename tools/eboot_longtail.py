# -*- coding: utf-8 -*-
"""EBOOT 문자열영역 롱테일 일괄 번역 → eboot_ui_short.json 병합.
FES tl_line 재사용. CSV 헤더/제어값 식별자는 제외(テキスト1 교훈)."""
import json, io, csv, os, sys, glob
BASE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,BASE)
import fes_worksheet as FW

# 엔진 식별자 제외집합: 모든 csv_src 헤더행(0,1) + locate 헤더 + event 제어값
EXCL=set()
for f in glob.glob(os.path.join(BASE,'csv_src','data','**','*.csv'),recursive=True):
    rows=list(csv.reader(open(f,encoding='utf-8')))
    for ri in (0,1):
        if ri<len(rows):
            for c in rows[ri]: EXCL.add(c.strip().lstrip('﻿'))
EXCL|={'なし','下','左','上','右','スクロール方向','スクロールスピード','リーダーモード','フォーメーション',
      '初期排出フラグ','所属オブジェクト','初期配置','出現方法','汎用値1','汎用値2','チーム番号','隊番号',
      '搭乗者能力','搭乗者','表示名','主兵装','陣営','原点','得点','制限','種類','必要G','状況','説明','テキスト',
      '耐久力','HP表示','優先度','出現方法','点数','汎用値'}

ui=json.load(open(os.path.join(BASE,'eboot_ui.json'),encoding='utf-8'))
sh=json.load(open(os.path.join(BASE,'eboot_ui_short.json'),encoding='utf-8'))
tr=set()
for r in csv.DictReader(io.open(os.path.join(BASE,'translate','eboot_ui.csv'),encoding='utf-8-sig',newline='')):
    if r.get('번역','').strip(): tr.add(int(r['key'].split('|')[1]))
def hasjp(s): return any('぀'<=c<='ヿ' or '一'<=c<='鿿' for c in s)
def frac(s):
    j=sum(1 for c in s if 'ぁ'<=c<='ヿ' or '一'<=c<='鿿' or c in '、。・ー')
    return j/max(1,len(s))
def kb(s):
    n=0
    for c in s:
        if c=='\n': n+=1
        elif '가'<=c<='힣': n+=2
        else:
            try: n+=len(c.encode('cp932'))
            except: n+=2
    return n
un=[e for e in ui if e['offs'][0][0] not in tr and e['text'] not in sh
    and hasjp(e['text']) and frac(e['text'])>=0.5 and 3400000<=e['offs'][0][0]<=3800000
    and e['text'].strip() not in EXCL]
okd={}; fail=[]
for e in un:
    ko,ok=FW.tl_line(e['text'])
    if ok and ko.strip() and kb(ko.replace(' ','').replace('　',''))<=e['slot']: okd[e['text']]=ko
    else: fail.append(e['text'])
print('cover %d / fail %d (excl %d)'%(len(okd),len(fail),len(EXCL)))
io.open(os.path.join(BASE,'_eboot_lt_fail.txt'),'w',encoding='utf-8').write('\n'.join(fail))
if '--write' in sys.argv:
    sh.update(okd)
    json.dump(sh,open(os.path.join(BASE,'eboot_ui_short.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=0)
    print('merged -> total %d'%len(sh))
