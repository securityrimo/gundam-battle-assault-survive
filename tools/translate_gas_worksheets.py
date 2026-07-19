# -*- coding: utf-8 -*-
"""GAS 번역 워크시트의 '번역' 열만 채운다.

Google 일본어→한국어 초벌 번역을 사용하되 게임 제어코드와 명시적 줄바꿈을
자리표시자로 보호한다. 이미 채워진 번역은 기본적으로 건드리지 않는다.
"""
from __future__ import annotations

import csv
import glob
import html
import io
import json
import os
import re
import threading
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed


BASE = os.path.dirname(os.path.abspath(__file__))
WS_DIR = os.path.join(BASE, "translate")
CACHE_PATH = os.path.join(BASE, "translation_google_cache.json")
CODE_RE = re.compile(r"\{[^}]*\}|%[sd]")
JA_RE = re.compile(r"[\u3040-\u309f\u30a1-\u30fa\u3400-\u9fff]")
TOKEN_ARTIFACT_RE = re.compile(r"Z\s*Z\s*(?:TERM|BREAK|CODE)", re.I)
LOCK = threading.Lock()

# 공식/통용 건담 표기를 우선한다. 긴 항목부터 보호 토큰으로 치환한다.
TERMS = {
    "モビルスーツ": "모빌슈트",
    "モビルアーマー": "모빌아머",
    "地球連邦軍": "지구연방군",
    "ジオン公国軍": "지온 공국군",
    "ネオ・ジオン": "네오지온",
    "デラーズ・フリート": "데라즈 플리트",
    "デラーズフリート": "데라즈 플리트",
    "ロンド・ベル": "론도 벨",
    "ティターンズ": "티탄즈",
    "エゥーゴ": "에우고",
    "アクシズ": "액시즈",
    "ホワイトベース": "화이트 베이스",
    "ガンダム": "건담",
    "ジオン": "지온",
    "ザク": "자쿠",
    "ゲルググ": "겔구그",
    "ドム": "돔",
    "グフ": "구프",
    "ジム": "짐",
    "アムロ・レイ": "아무로 레이",
    "シャア・アズナブル": "샤아 아즈나블",
    "ブライト・ノア": "브라이트 노아",
    "カミーユ・ビダン": "카미유 비단",
    "ジュドー・アーシタ": "쥬도 아시타",
    "ハマーン・カーン": "하만 칸",
    "νガンダム": "뉴 건담",
    "ＭＳ": "MS",
    "ＭＡ": "MA",
}


def load_cache() -> dict[str, str]:
    if not os.path.exists(CACHE_PATH):
        return {}
    with io.open(CACHE_PATH, encoding="utf-8") as f:
        return json.load(f)


CACHE = load_cache()


def save_cache() -> None:
    tmp = CACHE_PATH + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as f:
        json.dump(CACHE, f, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, CACHE_PATH)


def protect(text: str) -> tuple[str, dict[str, str]]:
    replacements: dict[str, str] = {}
    counter = 0

    def put(value: str, prefix: str) -> str:
        nonlocal counter
        token = f"ZZ{prefix}{counter:04d}ZZ"
        counter += 1
        replacements[token] = value
        return token

    text = CODE_RE.sub(lambda m: put(m.group(0), "CODE"), text)
    text = text.replace("\\n", put("\\n", "BREAK"))
    for ja, ko in sorted(TERMS.items(), key=lambda x: len(x[0]), reverse=True):
        if ja in text:
            text = text.replace(ja, put(ko, "TERM"))
    return text, replacements


def restore(text: str, replacements: dict[str, str]) -> str:
    # 번역기가 토큰 주변에 넣는 공백도 함께 정리한다.
    for token, value in replacements.items():
        text = re.sub(rf"\s*{re.escape(token)}\s*", value, text, flags=re.I)
    # 번역기가 보호 토큰을 문장 경계로 보고 실제 개행을 넣는 경우가 있다.
    # 워크시트 규약은 두 글자짜리 ``\n``이므로 반드시 문자형으로 되돌린다.
    text = text.replace("\r\n", "\\n").replace("\r", "\\n").replace("\n", "\\n")
    text = text.replace(" \\\\n ", "\\n").replace(" \\\\n", "\\n").replace("\\n ", "\\n")
    return text.strip()


def google_translate(text: str) -> str:
    if not JA_RE.search(text):
        return text
    with LOCK:
        cached = CACHE.get(text)
    if cached is not None:
        return cached

    url = (
        "https://translate.googleapis.com/translate_a/single"
        "?client=gtx&sl=ja&tl=ko&dt=t&q=" + urllib.parse.quote(text)
    )
    last_error: Exception | None = None
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
            result = "".join(part[0] for part in payload[0] if part and part[0])
            result = html.unescape(result)
            with LOCK:
                CACHE[text] = result
            return result
        except Exception as exc:
            last_error = exc
            time.sleep(min(2 ** attempt, 20))
    raise RuntimeError(f"번역 실패: {text[:80]!r}: {last_error}")


def translate_cell(source: str) -> str:
    protected, replacements = protect(source)
    translated = google_translate(protected)
    return restore(translated, replacements)


def read_rows(path: str) -> tuple[list[str], list[dict[str, str]]]:
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def write_rows(path: str, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(tmp, path)


def validate(source: str, translated: str) -> list[str]:
    issues = []
    if sorted(CODE_RE.findall(source)) != sorted(CODE_RE.findall(translated)):
        issues.append("제어코드")
    if source.count("\\n") != translated.count("\\n"):
        issues.append("줄수")
    if not translated.strip():
        issues.append("공란")
    return issues


def reflow_like_source(source: str, translated: str) -> str:
    """번역문의 의미는 유지하면서 원문의 명시적 줄 수/빈 줄 위치를 복원한다."""
    src_lines = source.split("\\n")
    wanted = len(src_lines)
    if wanted <= 1:
        return translated.replace("\\n", " ").strip()

    # 번역기가 남긴 줄바꿈은 공백으로 합치고, 원문의 빈 줄은 아래에서 복원한다.
    flat = re.sub(r"\s+", " ", translated.replace("\\n", " ")).strip()
    nonempty = [i for i, line in enumerate(src_lines) if line]
    if not nonempty:
        return "\\n" * (wanted - 1)

    weights = [max(1, len(src_lines[i])) for i in nonempty]
    total_weight = sum(weights)
    chunks: list[str] = []
    start = 0
    used_weight = 0
    for pos, weight in enumerate(weights):
        if pos == len(weights) - 1:
            chunks.append(flat[start:].strip())
            break
        used_weight += weight
        ideal = round(len(flat) * used_weight / total_weight)
        lo = max(start + 1, ideal - 6)
        hi = min(len(flat) - 1, ideal + 6)
        spaces = [j for j in range(lo, hi + 1) if flat[j:j + 1] == " "]
        cut = min(spaces, key=lambda j: abs(j - ideal)) if spaces else ideal
        chunks.append(flat[start:cut].strip())
        start = cut + (1 if flat[cut:cut + 1] == " " else 0)

    out = [""] * wanted
    for idx, chunk in zip(nonempty, chunks):
        out[idx] = chunk
    return "\\n".join(out)


def translate_strict(source: str) -> str:
    """코드와 줄바꿈을 절대로 번역기에 보내지 않는 보수적 재번역."""
    out: list[str] = []
    for part in re.split(f"({CODE_RE.pattern})", source):
        if not part:
            continue
        if CODE_RE.fullmatch(part):
            out.append(part)
            continue
        lines = part.split("\\n")
        translated_lines = []
        for line in lines:
            if not line:
                translated_lines.append("")
                continue
            protected, replacements = protect(line)
            translated_lines.append(restore(google_translate(protected), replacements))
        out.append("\\n".join(translated_lines))
    return "".join(out)


OUTPUT_FIXES = {
    "鹵獲": "노획",
    "鹵捕": "노획",
    "髑髏": "해골",
    "匍匐": "포복",
    "ヅ다": "즈다",
    " ンダム": " 건담",
    "노획作작전": "노획 작전",
    "노획作 작전": "노획 작전",
    "노획作": "노획",
}


def translate_strict_plain(source: str) -> str:
    """자리표시자 없이 코드/줄 단위로 번역하여 ZZ 토큰 잔존을 원천 차단."""
    out: list[str] = []
    for part in re.split(f"({CODE_RE.pattern})", source):
        if not part:
            continue
        if CODE_RE.fullmatch(part):
            out.append(part)
            continue
        translated_lines = [google_translate(line) if line else "" for line in part.split("\\n")]
        out.append("\\n".join(translated_lines))
    result = "".join(out)
    for old, new in OUTPUT_FIXES.items():
        result = result.replace(old, new)
    return result


def main() -> None:
    paths = sorted(glob.glob(os.path.join(WS_DIR, "*.csv")))
    jobs: list[tuple[str, int, str]] = []
    loaded: dict[str, tuple[list[str], list[dict[str, str]]]] = {}
    for path in paths:
        fieldnames, rows = read_rows(path)
        loaded[path] = fieldnames, rows
        for idx, row in enumerate(rows):
            if not row["번역"].strip():
                jobs.append((path, idx, row["원문"]))

    print(f"번역 대상: {len(jobs)}셀 / 파일 {len(paths)}개")
    completed = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {
            pool.submit(translate_cell, source): (path, idx, source)
            for path, idx, source in jobs
        }
        for future in as_completed(futures):
            path, idx, source = futures[future]
            translated = future.result()
            loaded[path][1][idx]["번역"] = translated
            completed += 1
            if completed % 100 == 0:
                print(f"  {completed}/{len(jobs)}")
                with LOCK:
                    save_cache()

    # 로컬 정규화 후 오염/잔존 일본어 행은 병렬로 보수 재번역한다.
    repairs: list[tuple[str, int, str]] = []
    for path, (_, rows) in loaded.items():
        for idx, row in enumerate(rows):
            row["번역"] = (
                row["번역"]
                .replace("\r\n", "\\n")
                .replace("\r", "\\n")
                .replace("\n", "\\n")
            )
            if row["원문"].count("\\n") != row["번역"].count("\\n"):
                row["번역"] = reflow_like_source(row["원문"], row["번역"])
            for old, new in OUTPUT_FIXES.items():
                row["번역"] = row["번역"].replace(old, new)
            code_bad = sorted(CODE_RE.findall(row["원문"])) != sorted(CODE_RE.findall(row["번역"]))
            if code_bad or TOKEN_ARTIFACT_RE.search(row["번역"]) or JA_RE.search(row["번역"]):
                repairs.append((path, idx, row["원문"]))

    if repairs:
        print(f"보수 재번역: {len(repairs)}셀")
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = {
                pool.submit(translate_strict_plain, source): (path, idx)
                for path, idx, source in repairs
            }
            for future in as_completed(futures):
                path, idx = futures[future]
                loaded[path][1][idx]["번역"] = future.result()

    all_issues: list[str] = []
    for path, (fieldnames, rows) in loaded.items():
        for row in rows:
            issues = validate(row["원문"], row["번역"])
            if issues:
                all_issues.append(f"{os.path.basename(path)} {row['key']}: {','.join(issues)}")
        write_rows(path, fieldnames, rows)
    with LOCK:
        save_cache()

    print(f"완료: {completed}셀")
    if all_issues:
        print(f"검증 문제: {len(all_issues)}건")
        for issue in all_issues[:50]:
            print("  " + issue)
        raise SystemExit(2)
    print("제어코드/줄수/공란 검증 통과")


if __name__ == "__main__":
    main()
