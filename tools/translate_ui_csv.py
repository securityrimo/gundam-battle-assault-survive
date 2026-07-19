# -*- coding: utf-8 -*-
"""btn.csv / msg.csv / tips_data.csv 번역 → csv_ko_utf8/ 에 저장(build_kr이 소비).
컬럼 규칙 준수: 필드명 행(0,1)·아이콘/id 컬럼·주석행 보존. 용어사전+UI사전+부분치환."""
import sys, io, os, csv, glob, re
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gaslib as G
jp=re.compile(r"[぀-ゟ゠-ヿ一-鿿]")

# MASTER: 용어/캐릭터 사전 + csv 셀쌍
MASTER={}
def add(j,k):
    j=(j or "").strip(); k=(k or "").strip()
    if j and k and j!=k and (j not in MASTER or len(k)<len(MASTER[j])): MASTER[j]=k
for row in csv.DictReader(io.open(os.path.join(G.BASE,"TERM_GLOSSARY.csv"),encoding="utf-8-sig")): add(row["original_jp"],row["standard_ko"])
for row in csv.DictReader(io.open(os.path.join(G.BASE,"CHARACTER_GLOSSARY.csv"),encoding="utf-8-sig")): add(row["original_jp"],row["standard_ko"])
for kp in glob.glob(os.path.join(G.BASE,"csv_ko_utf8","**","*.csv"),recursive=True):
    sp=os.path.join(G.BASE,"csv_src",os.path.relpath(kp,os.path.join(G.BASE,"csv_ko_utf8")))
    if not os.path.exists(sp): continue
    for si,kr in zip(csv.reader(io.open(sp,encoding="utf-8-sig",newline="")),csv.reader(io.open(kp,encoding="utf-8-sig",newline=""))):
        for a,b in zip(si,kr):
            if jp.search(a) and not jp.search(b): add(a,b)

# UI/버튼/메시지 사전 (수동)
UI={
"決定":"결정","戻る":"뒤로","編成完了":"편성 완료","選択画面":"선택 화면","タイトル画面に戻る":"타이틀 화면으로",
"メインメニューに戻る":"메인 메뉴로","時代／作品切替":"시대/작품 전환","時代切替":"시대 전환","作品切替":"작품 전환",
"機体情報":"기체 정보","チューニング":"튜닝","購入":"구입","売却":"매각","装備":"장비","解除":"해제","変更":"변경",
"次へ":"다음","前へ":"이전","確認":"확인","中止":"중지","開始":"시작","終了":"종료","一覧":"목록","詳細":"상세",
"出撃":"출격","待機":"대기","出撃準備":"출격 준비","小隊編成":"소대 편성","保存":"저장","呼び出し":"불러오기",
"搭乗する機体を選択します。":"탑승할 기체를 선택합니다.","パイロットを選択します。":"파일럿을 선택합니다.",
"ＳＦＳを選択します。":"ＳＦＳを 선택합니다.".replace("ＳＦＳを","ＳＦＳ를"),
"小隊のオペレーターを選択します。":"소대의 오퍼레이터를 선택합니다.","編成を完了し、出撃します。":"편성을 완료하고 출격합니다.",
"編成した小隊の保存や呼び出しを行います。":"편성한 소대의 저장·불러오기를 합니다.",
"パイロットについての説明を表示します。":"파일럿에 대한 설명을 표시합니다.",
"出撃準備についての説明を表示します。":"출격 준비에 대한 설명을 표시합니다.",
"シチュエーションについての説明を表示します。":"시츄에이션에 대한 설명을 표시합니다.",
"を選択します。":"를 선택합니다.","を表示します。":"를 표시합니다.","についての説明":"에 대한 설명",
"を行います。":"를 실행합니다.","します。":"합니다.","します":"합니다","です。":"입니다.","ます。":"습니다.",
}
for j,k in UI.items(): add(j,k)
keys=sorted(MASTER,key=len,reverse=True)
def tr(t):
    t=t.strip()
    if not jp.search(t): return t          # 일본어 없으면 그대로(아이콘ID/숫자/영문)
    if t in MASTER: return MASTER[t]
    s=t
    for j in keys:
        if j in s: s=s.replace(j,MASTER[j])
    return s if not jp.search(s) else t     # 못 풀면 원문 유지(추후)

def fileset_read(name):
    for s in G.fsets():
        if s["nfiles"]==0: continue
        try: ents=G.fset_entries(s)
        except: continue
        for e in ents:
            if e["name"].endswith(name): return G.fset_read(s,e).decode("cp932"), e["name"]
    return None,None

# (파일, 번역할 컬럼들, 헤더행수)
JOBS=[("guide_bar/btn.csv",[2,4,6,8],2),("guide_bar/msg.csv",[1],2),("option/tips_data.csv",[1],2)]
for name,cols,hdr in JOBS:
    text,full=fileset_read(name)
    if not text: print(f"{name}: 없음"); continue
    sep="\r\n" if "\r\n" in text else "\n"
    rows=[ln.split(",") for ln in text.split(sep)]
    changed=0
    for ri,r in enumerate(rows):
        if ri<hdr: continue
        for ci in cols:
            if ci<len(r) and jp.search(r[ci]):
                nt=tr(r[ci])
                if nt!=r[ci]: r[ci]=nt; changed+=1
    outp=os.path.join(G.BASE,"csv_ko_utf8",full.replace("/",os.sep))
    os.makedirs(os.path.dirname(outp),exist_ok=True)
    io.open(outp,"w",encoding="utf-8-sig",newline="").write(sep.join(",".join(r) for r in rows))
    # 남은 일본어 셀 수
    rem=sum(1 for ri,r in enumerate(rows) if ri>=hdr for ci in cols if ci<len(r) and jp.search(r[ci]))
    print(f"{name}: {changed}셀 번역, 남은 일본어 {rem} → {outp}")
