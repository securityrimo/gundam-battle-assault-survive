# -*- coding: utf-8 -*-
"""슬롯 초과 칭호 26개를 슬롯 이내 한글로 개별 지정 → eboot_ui_short.json 병합."""
import json, io, os, sys
BASE=os.path.dirname(os.path.abspath(__file__))
M={
 'だが':'허나','使い':'술사','呼ぶ':'부름','子息':'자제','子犬':'강견','宵闇':'야음','小粋':'세련',
 '撫子':'패랭','狩人':'엽사','猟犬':'엽견','舞う':'무희','風の':'바람','常闇':'암흑','濃霧':'농무',
 '陽炎':'양염','子猫':'자묘',
 '向日葵':'해님꽃','殺し屋':'암살자','焼け跡':'폐허',
 '宙域挙動':'우주거동','架空の空':'가상하늘',
 '壊れないコンテナ':'안부서지는상자',
 '北宋の壺(背低/本物)':'북송단지(저/진품)','北宋の壺(背低/贋作)':'북송단지(저/위작)',
 'エリア表示用（矩形）':'에리어표시용(사각)',
 '壊れない格納庫(対戦空中戦専用)':'안부서지는격납고(대전공중전)',
}
def kb(s):
    n=0
    for c in s:
        if c=='\n': n+=1
        elif '가'<=c<='힣': n+=2
        else:
            try: n+=len(c.encode('cp932'))
            except: n+=2
    return n
ui={e['text']:e for e in json.load(open(os.path.join(BASE,'eboot_ui.json'),encoding='utf-8'))}
bad=0; add={}
for jp,ko in M.items():
    e=ui.get(jp)
    if not e: io.open(os.path.join(BASE,'_titlefit_log.txt'),'a',encoding='utf-8').write('MISS %s\n'%jp); bad+=1; continue
    if kb(ko)>e['slot']: io.open(os.path.join(BASE,'_titlefit_log.txt'),'a',encoding='utf-8').write('OVER %d %d %s\n'%(e['slot'],kb(ko),jp)); bad+=1; continue
    add[jp]=ko
res='fit %d bad %d'%(len(add),bad)
io.open(os.path.join(BASE,'_titlefit_res.txt'),'w',encoding='utf-8').write(res)
if '--write' in sys.argv and bad==0:
    sp=os.path.join(BASE,'eboot_ui_short.json'); d=json.load(open(sp,encoding='utf-8')); d.update(add)
    json.dump(d,open(sp,'w',encoding='utf-8'),ensure_ascii=False,indent=0)
    io.open(os.path.join(BASE,'_titlefit_res.txt'),'a',encoding='utf-8').write(' | merged %d'%len(d))
