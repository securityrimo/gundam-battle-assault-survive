# -*- coding: utf-8 -*-
import csv, io, os, sys
BASE=os.path.dirname(os.path.abspath(__file__))
R='{B=W}{C=C83C3C}'; B='{B=W}{C=334572}'; G='{B=W}{C=356E4D}'; E='{CE}{BE}'
M={
 f'{G}エリアＡ{E}、{R}デュエルガンダム・{E}\n{R}アサルトシュラウド{E}が共闘を開始':f'{G}에리어A{E}, {R}듀얼 건담{E}\n{R}어설트 슈라우드{E}가 공투 개시',
 f'{G}エリアＢ{E}、{G}エリアＣ{E}、{G}エリアＤ{E}への\n{B}バグ{E}の投入に成功！':f'{G}에리어B{E}, {G}에리어C{E}, {G}에리어D{E}에\n{B}버그{E} 투입에 성공!',
 f'{G}エリアＣ{E}、{R}エターナル{E}、{R}クサナギ{E}が\n{B}ジェネシス{E}へ向け前進を始めました':f'{G}에리어C{E}, {R}이터널{E}, {R}쿠사나기{E}가\n{B}제네시스{E}를 향해 전진을 시작했습니다',
 f'{G}エリアＤ{E}、{R}隔壁{E}を発見しました！\n{R}隔壁{E}を破壊し、{G}要塞内部{E}への進入路を\n確保してください。':f'{G}에리어D{E}, {R}격벽{E}을 발견했습니다!\n{R}격벽{E}을 파괴해 {G}요새 내부{E} 진입로를\n확보해주세요.',
 f'{G}エリアＥ{E}、{R}デュエルガンダム・{E}\n{R}アサルトシュラウド{E}が共闘を開始':f'{G}에리어E{E}, {R}듀얼 건담{E}\n{R}어설트 슈라우드{E}가 공투 개시',
 f'{G}エリアＥ{E}、{R}連邦軍第０８ＭＳ小隊{E}が\n{R}ガンタンク部隊{E}防衛のため出現！':f'{G}에리어E{E}, {R}연방군 제08MS소대{E}가\n{R}건탱크 부대{E} 방어를 위해 출현!',
 '敵ＭＡをなんとしても撃墜して\nください':'적 MA를 반드시 격추해\n주세요',
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
p=os.path.join(BASE,'translate','fes_tl.csv')
rows=list(csv.DictReader(io.open(p,encoding='utf-8-sig',newline='')))
slots={r['원문']:int(r['slot']) for r in rows}
ok=bad=0
for jp,ko in M.items():
    if jp not in slots: bad+=1; print('MISS'); continue
    if kb(ko.replace(' ',''))>slots[jp]: bad+=1; print('OVER',slots[jp],kb(ko.replace(' ',''))); continue
    ok+=1
print('fit',ok,'bad',bad)
if '--write' in sys.argv and bad==0:
    for r in rows:
        if r['원문'] in M: r['번역']=M[r['원문']]
    with io.open(p,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    print('done')
