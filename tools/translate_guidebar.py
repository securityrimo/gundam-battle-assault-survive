# -*- coding: utf-8 -*-
"""guide_bar msg.csv/btn.csv 잔여 일본어 → 한글. 패턴+용어사전, 조사 자동(을/를,이/가,은/는).
--write 시 csv_ko_utf8 갱신. 미커버는 _guidebar_left.txt 로."""
import csv, io, sys, os, re, json
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
BASE=os.path.dirname(os.path.abspath(__file__))

T={ # 용어(긴 것 우선 매칭)
 '地球連邦宇宙軍':'지구연방우주군','ジオン公国軍':'지온공국군','デラーズ・フリート':'델라즈 플릿',
 'エゥーゴ':'에우고','ティターンズ':'티탄즈','アクシズ':'액시즈','ネオ・ジオン':'네오지온',
 'クロスボーン・バンガード':'크로스본 뱅가드','ガンダムＳＥＥＤ':'건담SEED','ガンダム００':'건담00',
 '地球連邦軍':'지구연방군','ゲスト機体':'게스트 기체','カスタムパイロット':'커스텀 파일럿',
 '主兵装１':'주무장1','主兵装２':'주무장2','主兵装３':'주무장3','主兵装':'주무장','副兵装':'부무장',
 '格闘武器':'격투무기','シールド':'실드','カスタムパーツ':'커스텀 파츠','カスタムサウンド':'커스텀 사운드',
 '実弾兵器':'실탄병기','ビーム兵器':'빔병기','スラスター':'스러스터','ロックオン':'록온',
 '耐久力':'내구력','旋回速度':'선회속도','命中精度':'명중 정밀도','連射回数':'연사 횟수','リロード':'재장전',
 '機体':'기체','武器':'무기','弾':'탄','小隊':'소대','オペレーター':'오퍼레이터','パイロット':'파일럿',
 'シチュエーション':'시추에이션','ミッション':'미션','チューニング':'튜닝','チューン':'튜닝',
 '出撃':'출격','待機':'대기','隊長':'대장','編成':'편성','保存':'저장','称号':'칭호','スキル':'스킬',
 '性別':'성별','容姿':'외모','名前':'이름','出身地':'출신지','適性検査':'적성검사','初期パラメータ':'초기 파라미터',
 'パラメータ':'파라미터','ショップ':'상점','ＢＧＭ':'BGM','ボリューム':'볼륨','セーブ':'저장','ロード':'로드',
 'データインストール':'데이터 설치','シークレット':'시크릿','コントロール':'컨트롤','通信':'통신',
 '対戦':'대전','協力':'협력','購入':'구입','売却':'매각','雇用':'고용','開発計画':'개발계획',
 'エースパイロット':'에이스 파일럿','ゲージ':'게이지','メインメニュー':'메인메뉴','タイトル':'타이틀',
 'デモ':'데모','ランキング':'랭킹','リプレイ':'리플레이','クリア':'클리어','ハイスコア':'하이스코어',
 '声':'목소리','時代':'시대','軍属':'소속군','階級':'계급','報酬':'보수','資金':'자금','情報':'정보',
 '設定':'설정','変更':'변경','選択':'선택','決定':'결정','削除':'삭제','作成':'작성','管理':'관리',
 '確認':'확인','終了':'종료','移動':'이동','戻る':'뒤로',
 'ソレスタルビーイング':'솔레스타 빙','国連軍所属':'유엔군 소속','ザフト':'자프트',
 '地球連合軍、オーブ連合首長国軍':'지구연합군·오브 연합수장국군','地球連合軍':'지구연합군',
 'ガンダムマイスター':'건담 마이스터','エクストラ':'엑스트라','オートスキル':'오토 스킬','オートセーブ':'오토 세이브',
 'オンオフ切替':'온오프 전환','サイズ切替':'사이즈 전환','所持ボーナス！':'소지 보너스!','体験版ボーナス！':'체험판 보너스!',
 '新規作成':'신규 작성','装着制限':'장착 제한','解除':'해제','成長限界':'성장 한계','成長':'성장',
 'コンテナ数':'컨테이너 수','通信専用':'통신 전용','対戦モード':'대전 모드','コンピューター操作':'컴퓨터 조작',
 'コンピューター':'컴퓨터','キャラクター':'캐릭터','オーバーチューン':'오버 튜닝','制限':'제한',
 'ガンダムアサルトサヴァイブ':'건담 어설트 서바이브','ガンダムバトルクロニクル':'건담 배틀 크로니클',
 'ガンダムバトルタクティクス':'건담 배틀 택틱스','ガンダムバトルユニバース':'건담 배틀 유니버스',
 'ガンダムバトルロワイヤル':'건담 배틀 로와이얄','ＰＬＡＹＥＲ':'플레이어','PLAYER':'플레이어',
 '回以上出撃した':'회 이상 출격한 ','付け替えます':'교체합니다','切り替えます':'전환합니다',
 '競う':'겨루는 ','最大４人':'최대 4인','最大４人まで':'최대 4인까지',
}
TK=sorted(T,key=len,reverse=True)

def has_jp(s): return any('぀'<=c<='ヿ' or '一'<=c<='鿿' for c in s)
def term(s):
    out=s
    for k in TK: out=out.replace(k,T[k])
    return out
def particles(s):
    out=s
    for a,b in [('では','에서는 '),('の','의 '),('や','와 '),('もしくは','또는 ')]:
        out=out.replace(a,b)
    out=re.sub(r'([가-힣A-Za-z0-9%０-９Ｇ])を',lambda m:m.group(1)+('을 ' if jong(m.group(1)) else '를 '),out)
    out=re.sub(r'([가-힣A-Za-z0-9%０-９Ｇ])が',lambda m:m.group(1)+('이 ' if jong(m.group(1)) else '가 '),out)
    out=re.sub(r'([가-힣A-Za-z0-9%０-９Ｇ])は',lambda m:m.group(1)+('은 ' if jong(m.group(1)) else '는 '),out)
    out=re.sub(r'\s+',' ',out).replace(' 의 ','의 ').replace('의  ','의 ').strip()
    return out
def jong(w):  # 마지막 한글의 받침 유무
    for c in reversed(w):
        if '가'<=c<='힣': return (ord(c)-0xAC00)%28!=0
        if c.isascii() and c.isalnum(): return c.lower() in 'lmnr139607'  # 근사
    return False
def josa(w,a,b): return a if jong(w) else b  # a=받침있음(을/이/은), b=없음

RULES=[
 (r'^(.+)の機体です。$',        lambda x:f'{x}의 기체입니다.'),
 (r'^(.+)をチューニングします。$',lambda x:f'{x}{josa(x,"을","를")} 튜닝합니다.'),
 (r'^(.+)を選択してください。$', lambda x:f'{x}{josa(x,"을","를")} 선택해주세요.'),
 (r'^(.+)を選択します。$',       lambda x:f'{x}{josa(x,"을","를")} 선택합니다.'),
 (r'^(.+)を入力してください。$', lambda x:f'{x}{josa(x,"을","를")} 입력해주세요.'),
 (r'^(.+)が上昇します。$',       lambda x:f'{x}{josa(x,"이","가")} 상승합니다.'),
 (r'^(.+)が増加します。$',       lambda x:f'{x}{josa(x,"이","가")} 증가합니다.'),
 (r'^(.+)が増えます。$',         lambda x:f'{x}{josa(x,"이","가")} 늘어납니다.'),
 (r'^(.+)が短縮されます。$',     lambda x:f'{x}{josa(x,"이","가")} 단축됩니다.'),
 (r'^(.+)が決定しました。$',     lambda x:f'{x}{josa(x,"이","가")} 결정되었습니다.'),
 (r'^(.+)を行います。$',         lambda x:f'{x}{josa(x,"을","를")} 합니다.'),
 (r'^(.+)を変更します。$',       lambda x:f'{x}{josa(x,"을","를")} 변경합니다.'),
 (r'^(.+)を確認します。$',       lambda x:f'{x}{josa(x,"을","를")} 확인합니다.'),
 (r'^(.+)を購入します。$',       lambda x:f'{x}{josa(x,"을","를")} 구입합니다.'),
 (r'^(.+)を設定します。$',       lambda x:f'{x}{josa(x,"을","를")} 설정합니다.'),
 (r'^(.+)を保存します。$',       lambda x:f'{x}{josa(x,"을","를")} 저장합니다.'),
 (r'^(.+)を呼び出します。$',     lambda x:f'{x}{josa(x,"을","를")} 불러옵니다.'),
 (r'^(.+)を破棄します。$',       lambda x:f'{x}{josa(x,"을","를")} 버립니다.'),
 (r'^(.+)を完了します。$',       lambda x:f'{x}{josa(x,"을","를")} 완료합니다.'),
 (r'^(.+)を取り付けます。$',     lambda x:f'{x}{josa(x,"을","를")} 장착합니다.'),
 (r'^(.+)を開始します。$',       lambda x:f'{x}{josa(x,"을","를")} 시작합니다.'),
 (r'^(.+)はできません。$',       lambda x:f'{x}{josa(x,"은","는")} 불가능합니다.'),
 (r'^(.+)できません。$',         lambda x:f'{x}할 수 없습니다.'),
 (r'^(.+)されます。$',           lambda x:f'{x}됩니다.'),
 (r'^(.+)になります。$',         lambda x:f'{x}{josa(x,"이","가")} 됩니다.'),
 (r'^(.+)しました。$',           lambda x:f'{x}했습니다.'),
 (r'^(.+)します。$',             lambda x:f'{x}합니다.'),
 (r'^(.+)できます。$',           lambda x:f'{x}할 수 있습니다.'),
 (r'^(.+)です。$',               lambda x:f'{x}입니다.'),
 (r'^(.+)です$',                 lambda x:f'{x}입니다'),
]

def translate(s):
    for pat,fn in RULES:          # 규칙은 원문 접미에 매칭
        m=re.match(pat,s)
        if m:
            x=particles(term(m.group(1))).strip().rstrip('의').strip()
            if not has_jp(x): return fn(x)
    s2=particles(term(s))
    if not has_jp(s2): return s2
    return None

MANUAL=json.load(open(os.path.join(BASE,'_guidebar_manual.json'),encoding='utf-8')) if os.path.exists(os.path.join(BASE,'_guidebar_manual.json')) else {}

def run(write=False):
    left=[]; done=0
    for f in ['data/menu/guide_bar/msg.csv','data/menu/guide_bar/btn.csv']:
        p=os.path.join(BASE,'csv_ko_utf8',*f.split('/'))
        rows=list(csv.reader(open(p,encoding='utf-8')))
        for ri,row in enumerate(rows):
            for ci,c in enumerate(row):
                cs=c.strip()
                if not cs or cs.startswith('//') or not has_jp(cs): continue
                ko=MANUAL.get(cs) or translate(cs)
                if ko: rows[ri][ci]=ko; done+=1
                else: left.append(cs)
        if write:
            with open(p,'w',encoding='utf-8',newline='') as fp: csv.writer(fp).writerows(rows)
    print(f'번역 {done} / 잔여 {len(left)}')
    io.open(os.path.join(BASE,'_guidebar_left.txt'),'w',encoding='utf-8').write('\n'.join(sorted(set(left))))
    return left

if __name__=='__main__':
    run('--write' in sys.argv)
