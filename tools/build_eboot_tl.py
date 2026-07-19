# -*- coding: utf-8 -*-
"""EBOOT UI 문자열(eboot_ui.csv) 자동+수동 번역.
소스: Codex 용어/캐릭터 사전 + csv_src↔csv_ko_utf8 셀쌍(이름류) + 수동 UI사전.
방식: (1)정확일치 (2)긴것우선 부분치환 후 일본어 잔존 없으면 채택. 잔존시 공란(추후)."""
import sys, io, os, csv, glob, re
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
BASE=os.path.dirname(os.path.abspath(__file__))
jp=re.compile(r"[぀-ゟ゠-ヿ一-鿿]")

MASTER={}
def add(j,k):
    j=(j or "").strip(); k=(k or "").strip()
    if j and k and j!=k and (j not in MASTER or len(k)<len(MASTER[j])): MASTER[j]=k

# 1) 용어/캐릭터 사전
for row in csv.DictReader(io.open(os.path.join(BASE,"TERM_GLOSSARY.csv"),encoding="utf-8-sig")):
    add(row["original_jp"], row["standard_ko"])
for row in csv.DictReader(io.open(os.path.join(BASE,"CHARACTER_GLOSSARY.csv"),encoding="utf-8-sig")):
    add(row["original_jp"], row["standard_ko"])
# 2) csv_src ↔ csv_ko_utf8 셀쌍
for kp in glob.glob(os.path.join(BASE,"csv_ko_utf8","**","*.csv"),recursive=True):
    rel=os.path.relpath(kp,os.path.join(BASE,"csv_ko_utf8"))
    sp=os.path.join(BASE,"csv_src",rel)
    if not os.path.exists(sp): continue
    srows=list(csv.reader(io.open(sp,encoding="utf-8-sig",newline="")))
    krows=list(csv.reader(io.open(kp,encoding="utf-8-sig",newline="")))
    for si,kr in zip(srows,krows):
        for a,b in zip(si,kr):
            if jp.search(a) and not jp.search(b): add(a,b)

# 3) 수동 UI 사전(능력치·메뉴·버튼·공통). 필요시 계속 확장.
UI={
 "出撃":"출격","出撃回数":"출격 횟수","出撃準備":"출격 준비","編成完了":"편성 완료","編成":"편성",
 "カスタム小隊":"커스텀 소대","カスタムパイロット":"커스텀 파일럿","小隊":"소대",
 "残ポイント":"잔여 포인트","選択画面":"선택 화면","機体情報":"기체 정보","時代切替":"시대 전환",
 "決定":"결정","戻る":"뒤로","チューニング":"튜닝","選択":"선택","確認":"확인","購入":"구입",
 "実弾防御":"실탄 방어","ビーム防御":"빔 방어","機動性":"기동성","スラスター出力":"스러스터 출력",
 "スラスター速度":"스러스터 속도","レーダー性能":"레이더 성능","バランサー":"밸런서","旋回速度":"선회 속도",
 "体力":"체력","射撃":"사격","格闘":"격투","命中":"명중","防御":"방어","反応":"반응","敏捷":"민첩",
 "技量":"기량","感知":"감지","搭乗する機体を選択します":"탑승할 기체를 선택합니다",
 "の機体です":"의 기체입니다","のシチュエーションです":"의 시츄에이션입니다","です":"입니다",
 "メインメニューに戻る":"메인 메뉴로","クリア情報":"클리어 정보","名前":"이름","性別":"성별",
 "容姿":"용모","声":"음성","出身地":"출신지","適性検査":"적성 검사","質問":"질문","回答":"답변",
 "男":"남","女":"여","地球連邦宇宙軍":"지구연방 우주군","地球連邦軍":"지구연방군",
 "ジオン公国軍":"지온 공국군","ジオン軍":"지온군","エゥーゴ":"에우고","ティターンズ":"티탄즈",
 "ネオ・ジオン":"네오지온","購入ポイント":"구입 포인트","装備":"장비","武器":"무기","機体":"기체",
}
for j,k in UI.items(): add(j,k)

keys=sorted(MASTER.keys(), key=len, reverse=True)  # 긴 것 우선 치환
def translate(t):
    if t in MASTER: return MASTER[t], "exact"
    s=t
    for j in keys:
        if j in s: s=s.replace(j,MASTER[j])
    return (s,"sub") if not jp.search(s) else (None,"fail")

# eboot_ui.csv 채우기
p=os.path.join(BASE,"translate","eboot_ui.csv")
rows=list(csv.reader(io.open(p,encoding="utf-8-sig",newline="")))
ex=sub=fail=0
for r in rows[1:]:
    if len(r)<4: continue
    while len(r)<5: r.append("")
    if r[4].strip(): continue
    ko,how=translate(r[3])
    if ko: r[4]=ko; ex+=(how=="exact"); sub+=(how=="sub")
    else: fail+=1
with io.open(p,"w",encoding="utf-8-sig",newline="") as f: csv.writer(f).writerows(rows)
print(f"MASTER {len(MASTER)}개. eboot_ui: 정확일치 {ex}, 부분치환 {sub}, 실패(공란) {fail}, 커버 {ex+sub}/{len(rows)-1}")
