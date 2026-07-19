# -*- coding: utf-8 -*-
"""고정 폭 일본어 줄바꿈을 제거해 장문을 다시 번역하고 원래 줄 수로 복원."""
from __future__ import annotations

import csv
import glob
import io
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import translate_gas_worksheets as core
import polish_translations as polish


BASE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.join(BASE, "translate")
TARGETS = {
    "charamake_data.csv",
    "event.csv",
    "inst_mission.csv",
    "inst_ms.csv",
    "inst_operator.csv",
    "inst_parts.csv",
    "inst_pilot.csv",
    "inst_sfs.csv",
}


def translate_joined(source: str) -> str:
    # 코드가 있는 행은 기존 보수 번역을 유지한다.
    if core.CODE_RE.search(source):
        return ""
    joined = source.replace("\\n", "")
    ko = core.google_translate(joined)
    for old, new in core.OUTPUT_FIXES.items():
        ko = ko.replace(old, new)
    for old, new in polish.REPLACEMENTS:
        ko = ko.replace(old, new)
    if "\\n" in source:
        ko = core.reflow_like_source(source, ko)
    return ko


def main() -> None:
    loaded = {}
    jobs = []
    for path in sorted(glob.glob(os.path.join(WS, "*.csv"))):
        if os.path.basename(path) not in TARGETS:
            continue
        with io.open(path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            fields = list(reader.fieldnames or [])
            rows = list(reader)
        loaded[path] = (fields, rows)
        for idx, row in enumerate(rows):
            # 이름/짧은 명칭은 앞 단계의 확정 매핑을 유지한다.
            if row["kind"] in {"名前", "ミッション名", "パーツ名", "スキル名"}:
                continue
            if core.CODE_RE.search(row["원문"]):
                continue
            jobs.append((path, idx, row["원문"]))

    print(f"장문 재번역 대상: {len(jobs)}셀")
    done = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {
            pool.submit(translate_joined, source): (path, idx)
            for path, idx, source in jobs
        }
        for future in as_completed(futures):
            path, idx = futures[future]
            ko = future.result()
            if ko:
                loaded[path][1][idx]["번역"] = ko
            done += 1
            if done % 100 == 0:
                print(f"  {done}/{len(jobs)}")
                core.save_cache()

    for path, (fields, rows) in loaded.items():
        tmp = path + ".tmp"
        with io.open(tmp, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(tmp, path)
    core.save_cache()
    print(f"완료: {done}셀")


if __name__ == "__main__":
    main()
