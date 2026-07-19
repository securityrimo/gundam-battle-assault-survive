# -*- coding: utf-8 -*-
import io,csv,glob
import fes_worksheet as FW
EXCL=set()
for f in glob.glob('csv_src/data/**/*.csv',recursive=True):
    rows=list(csv.reader(open(f,encoding='utf-8')))
    for ri in (0,1):
        if ri<len(rows):
            for c in rows[ri]: EXCL.add(c.strip().lstrip('﻿'))
EXCL|={'なし','下','左','上','右','スクロール方向','スクロールスピード','リーダーモード','フォーメーション','初期排出フラグ','所属オブジェクト','初期配置','出現方法','汎用値1','汎用値2','チーム番号','隊番号','搭乗者能力','搭乗者','表示名','主兵装','陣営','原点','得点','制限','種類','必要G','状況','説明','テキスト','耐久力','HP表示','優先度','点数','汎用値'}
out=[]
for t in ['陽炎','狩人','小粋','子犬','時代','出身','修正','宙域挙動','ボイス','殺し屋','向日葵','A以下','Dのみ','風の','舞う']:
    ko,ok=FW.tl_line(t)
    out.append('%s: %s tl=%s|%r'%(t,'EXCL' if t in EXCL else '',ok,ko))
io.open('_dbg.txt','w',encoding='utf-8').write('\n'.join(out))
