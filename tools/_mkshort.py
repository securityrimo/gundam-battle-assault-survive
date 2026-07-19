# -*- coding: utf-8 -*-
import csv, io, sys, json
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
def est(ko):
    n=0
    for c in ko:
        if c==' ' or ord(c)<128: n+=1
        else: n+=2
    return n
OVR={
 # slot4
 '刹那':'찰나','悟り':'깨침','岩場':'바위',
 # slot6
 'ジム改':'짐카이','光の翼':'빛날개','黙示録':'묵시록',
 # slot7
 '刹那 EX':'찰나EX',
 # slot8
 '二つの心':'두마음','悪意の刃':'악의의칼','折れた翼':'꺾인날개','暁の宇宙':'새벽우주',
 '絶望の鎖':'절망사슬','閃光の刻':'섬광순간','ザクⅡ改':'자쿠2改','宇宙の虹':'무지개',
 '揺らぐ心':'흔들림','ザクⅢ改':'자쿠3改','宇宙の渦':'소용돌이',
 # slot10
 'ドワッジ改':'드왓지改','宿命の二人':'숙명의두명','欧風市街地':'유럽시가지','砂塵の果て':'모래먼지끝',
 '宇宙の蜻蛉':'우주잠자리','星の屑作戦':'별먼지작전','死に誘う花':'죽음의꽃','父と子と…':'아버지와…',
 # slot11
 '二つの心 EX':'두마음EX','折れた翼 EX':'꺾인날개EX','絶望の鎖 EX':'절망사슬EX','閃光の刻 EX':'섬광순간EX',
 'SFSドダイ改':'SFS도다이改','TEST1(田中)':'TEST1(田中)','TEST2(田中)':'TEST2(田中)','揺らぐ心 EX':'흔들림EX',
 # slot12
 'イフリート改':'이프리트改','宇宙に降る星':'우주에지는별','戦場での再会':'전장에서재회','紅に染まる海':'붉게물든바다',
 'やらせはせん':'가만안둔다',
 # slot13
 '砂塵の果て EX':'모래먼지끝EX',
 # slot14
 'ネモ＋ドダイ改':'네모+도다이改','小惑星での死闘':'소행성사투','嵐の中で輝いて':'폭풍속빛나다','雷鳴に魂は還る':'천둥에혼귀환',
 # slot15
 '宇宙に降る星 EX':'우주에지는별EX',
 # slot16
 '光とどかぬ海底で':'빛닿지않는해저','謎のモビルスーツ':'수수께끼의MS','宇宙を乱す物の怪':'우주교란요괴',
 # slot22
 '遠吠えは落日に染まった':'석양에물든포효','狙い撃つ者と断ち斬る者':'겨눠쏘는자와베는자',
}
# slot 조회
rows=list(csv.DictReader(io.open('translate/eboot_ui.csv',encoding='utf-8-sig',newline='')))
slotmap={}
for r in rows:
    slotmap.setdefault(r['원문'],int(r['slot']))
bad=[]
for jp,ko in OVR.items():
    sl=slotmap.get(jp)
    b=est(ko.replace(' ',''))
    tag='OK' if (sl is not None and b<=sl) else '⚠'
    if tag=='⚠': bad.append((jp,ko,sl,b))
    print(f'{tag} slot{sl} {b}B | {jp} -> {ko}')
print('\n초과/미발견:',len(bad))
if not bad:
    json.dump(OVR,open('eboot_ui_short.json','w',encoding='utf-8'),ensure_ascii=False,indent=0)
    print('eboot_ui_short.json 저장',len(OVR))
