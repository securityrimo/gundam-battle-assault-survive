# -*- coding: utf-8 -*-
"""파일럿 이름 표준화 및 캐릭터별 키 사전 생성."""
from __future__ import annotations

import csv
import io
import os
from collections import defaultdict


BASE = os.path.dirname(os.path.abspath(__file__))
PILOT_PATH = os.path.join(BASE, "translate", "inst_pilot.csv")
OUT_PATH = os.path.join(BASE, "CHARACTER_GLOSSARY.csv")


STANDARD = {
    "アムロ・レイ": "아무로 레이",
    "カイ・シデン": "카이 시덴",
    "ハヤト・コバヤシ": "하야토 코바야시",
    "シロー・アマダ": "시로 아마다",
    "クリスチーナ・マッケンジー": "크리스티나 맥켄지",
    "シャア・アズナブル": "샤아 아즈나블",
    "ランバ・ラル": "람바 랄",
    "アイナ・サハリン": "아이나 사할린",
    "バーナード・ワイズマン": "버나드 와이즈먼",
    "ララァ・スン": "라라아 슨",
    "ドズル・ザビ": "도즐 자비",
    "コウ・ウラキ": "코우 우라키",
    "アナベル・ガトー": "애너벨 가토",
    "シーマ・ガラハウ": "시마 가라하우",
    "カミーユ・ビダン": "카미유 비단",
    "クワトロ・バジーナ": "크와트로 바지나",
    "エマ・シーン": "에마 신",
    "ファ・ユイリィ": "화 유이리",
    "レコア・ロンド": "레코아 론드",
    "ジェリド・メサ": "제리드 메사",
    "フォウ・ムラサメ": "포우 무라사메",
    "パプテマス・シロッコ": "팝티머스 시로코",
    "ヤザン・ゲーブル": "야잔 게이블",
    "ロザミア・バダム": "로자미아 바담",
    "ジュドー・アーシタ": "쥬도 아시타",
    "ルー・ルカ": "루 루카",
    "エルピー・プル": "엘피 플",
    "ハマーン・カーン": "하만 칸",
    "ハマーン・カーン(スーツ)": "하만 칸(파일럿 슈트)",
    "プルツー": "플 투",
    "グレミー・トト": "그레미 토토",
    "マシュマー・セロ": "마슈마 세로",
    "マシュマー・セロ(強化)": "마슈마 세로(강화)",
    "キャラ・スーン": "캐라 슨",
    "キャラ・スーン(強化)": "캐라 슨(강화)",
    "ハサウェイ・ノア": "하사웨이 노아",
    "クェス・パラヤ": "퀘스 파라야",
    "シーブック・アノー": "시북 아노",
    "ビルギット・ピリヨ": "빌기트 피리요",
    "アンナマリー・ブルージュ(連邦）": "안나마리 부르지(연방)",
    "セシリー・フェアチャイルド": "세실리 페어차일드",
    "カロッゾ・ロナ": "카롯조 로나",
    "ザビーネ・シャル": "자비네 샤르",
    "アンナマリー・ブルージュ": "안나마리 부르지",
    "キラ・ヤマト（私服）": "키라 야마토(사복)",
    "キラ・ヤマト（連合）": "키라 야마토(연합)",
    "キラ・ヤマト（ザフト）": "키라 야마토(자프트)",
    "ムウ・ラ・フラガ": "무우 라 플라가",
    "オーブ軍一般兵Ａ": "오브군 일반병 A",
    "オーブ軍一般兵Ｂ": "오브군 일반병 B",
    "アスラン・ザラ": "아스란 자라",
    "イザーク・ジュール（傷無し）": "이자크 쥴(흉터 없음)",
    "イザーク・ジュール": "이자크 쥴",
    "ラウ・ル・クルーゼ": "라우 르 크루제",
    "アンドリュー・バルトフェルド": "앤드류 발트펠트",
    "ザフト軍一般兵Ａ": "자프트군 일반병 A",
    "ザフト軍一般兵Ｂ": "자프트군 일반병 B",
    "クロト・ブエル": "크로토 부엘",
    "オルガ・サブナック": "오르가 사브나크",
    "シャニ・アンドラス": "샤니 안드라스",
    "連合軍一般兵Ａ": "연합군 일반병 A",
    "刹那・F・セイエイ": "세츠나 F. 세이에이",
    "ロックオン・ストラトス": "록온 스트라토스",
    "アレルヤ・ハプティズム": "알렐루야 합티즘",
    "ハレルヤ": "할렐루야",
    "覚醒アレルヤ": "각성 알렐루야",
    "ティエリア・アーデ": "티에리아 아데",
    "ヨハン・トリニティ": "요한 트리니티",
    "ミハエル・トリニティ": "미하엘 트리니티",
    "ネーナ・トリニティ": "네나 트리니티",
    "グラハム・エーカー": "그라함 에이커",
    "パトリック・コーラサワー": "패트릭 콜라사워",
    "セルゲイ・スミルノフ": "세르게이 스밀노프",
    "ソーマ・ピーリス": "소마 필리스",
    "アリー・アル・サーシェス": "알리 알 서셰스",
    "アレハンドロ・コーナー": "알레한드로 코너",
    "人革連軍一般兵Ａ": "인혁련군 일반병 A",
    "ユニオン軍一般兵Ａ": "유니온군 일반병 A",
    "ユニオン軍一般兵Ｂ": "유니온군 일반병 B",
    "国連軍一般兵Ａ": "유엔군 일반병 A",
    "国連軍一般兵Ｂ": "유엔군 일반병 B",
    "ウッソ・エヴィン": "웃소 에빈",
    "カテジナ・ルース": "카테지나 루스",
    "カテジナ・ルース（狂）": "카테지나 루스(광기)",
}


def main() -> None:
    with io.open(PILOT_PATH, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))

    entries: dict[str, dict[str, object]] = {}
    changed = 0
    for row in rows[1:]:
        if not row or not row[0].endswith("|1"):
            continue
        original = row[3].strip()
        if original not in STANDARD:
            raise RuntimeError(f"표준 이름이 없는 인물: {original!r}")
        standard = STANDARD[original]
        old = row[4]
        row[4] = standard
        changed += old != standard
        entry = entries.setdefault(
            original,
            {"original_jp": original, "standard_ko": standard, "keys": []},
        )
        entry["keys"].append(row[0])

    # 이름 셀에서 실제로 사용하던 기존 표기도 같은 파일의 설명에서 교정한다.
    old_to_new: dict[str, str] = {}
    for row in rows[1:]:
        if row and row[0].endswith("|1"):
            original = row[3].strip()
            old_to_new.setdefault(row[4], STANDARD[original])
    # 기존 이름은 위에서 이미 바뀌었으므로 알려진 혼용 표기를 별도로 보완한다.
    old_to_new.update({
        "아무로・레이": "아무로 레이",
        "하야토・고바야시": "하야토 코바야시",
        "하만・칸": "하만 칸",
        "아나벨 가토": "애너벨 가토",
        "시마 갈라하우": "시마 가라하우",
        "파푸테마스 시로코": "팝티머스 시로코",
        "쥬도 아시타": "쥬도 아시타",
        "알리 알 사셰스": "알리 알 서셰스",
        "우소 에빈": "웃소 에빈",
    })
    for row in rows[1:]:
        if not row or row[0].endswith("|1"):
            continue
        for old, new in old_to_new.items():
            if old and old != new:
                row[4] = row[4].replace(old, new)

    tmp = PILOT_PATH + ".tmp"
    with io.open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerows(rows)
    os.replace(tmp, PILOT_PATH)

    with io.open(OUT_PATH, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["original_jp", "standard_ko", "keys", "status", "note"]
        )
        writer.writeheader()
        for original, entry in entries.items():
            writer.writerow({
                "original_jp": original,
                "standard_ko": entry["standard_ko"],
                "keys": ";".join(entry["keys"]),
                "status": "표준화 완료",
                "note": "중복 키 통합" if len(entry["keys"]) > 1 else "",
            })

    print(f"파일럿 이름 교정: {changed}셀")
    print(f"캐릭터 사전: {len(entries)}명 -> {OUT_PATH}")


if __name__ == "__main__":
    main()
