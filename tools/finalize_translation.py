# -*- coding: utf-8 -*-
"""번역 교정·사전 적용·재조립·최종 QA를 올바른 순서로 실행한다."""
from __future__ import annotations

import os
import subprocess
import sys


BASE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = [
    "polish_translations.py",
    "final_polish_all.py",
    "build_term_glossary.py",
    "build_character_glossary.py",
    "polish_event.py",
    "polish_missions.py",
    "polish_pilots.py",
    "apply_worksheets.py",
    "_validate_ws.py",
    "final_translation_qa.py",
]


def main() -> None:
    for script in SCRIPTS:
        print(f"\n== {script} ==")
        subprocess.run([sys.executable, os.path.join(BASE, script)], cwd=BASE, check=True)
    print("\n번역 최종화 및 검증 완료.")


if __name__ == "__main__":
    main()
