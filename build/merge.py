#!/usr/bin/env python3
"""
sc-codex-strings — наложение оверлея на игровой global.ini.

Берёт ЧИСТЫЙ global.ini из вашей копии Star Citizen и заменяет значения
для ключей, перечисленных в overlay/*.ini. Всё, чего в оверлее нет,
остаётся ровно как в оригинале игры — файл не ломается.

Использование:
    python build/merge.py --base <путь к чистому global.ini> \
                          --out  <куда положить результат>

По умолчанию накладываются все overlay/*.ini рядом со скриптом.
"""

from __future__ import annotations

import argparse
import glob
import os
import sys


def read_ini(path: str) -> tuple[list[str], bool]:
    """Читает ini построчно. Возвращает (строки_без_переводов, был_ли_BOM)."""
    with open(path, "rb") as fh:
        raw = fh.read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    if bom:
        raw = raw[3:]
    text = raw.decode("utf-8", errors="replace")
    return text.splitlines(), bom


def load_overlay(paths: list[str]) -> dict[str, str]:
    """Собирает карту ключ→строка из всех оверлеев. Последний побеждает."""
    overlay: dict[str, str] = {}
    for p in paths:
        lines, _ = read_ini(p)
        for line in lines:
            eq = line.find("=")
            if eq <= 0:
                continue
            overlay[line[:eq]] = line
    return overlay


def main() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)

    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="чистый global.ini из игры")
    ap.add_argument("--out", required=True, help="куда записать результат")
    ap.add_argument(
        "--overlay",
        nargs="*",
        default=sorted(glob.glob(os.path.join(root, "overlay", "*.ini"))),
        help="файлы оверлея (по умолчанию overlay/*.ini)",
    )
    args = ap.parse_args()

    if not args.overlay:
        print("Нет ни одного оверлея — нечего накладывать.", file=sys.stderr)
        return 2

    overlay = load_overlay(args.overlay)
    base_lines, bom = read_ini(args.base)

    replaced = 0
    out_lines: list[str] = []
    for line in base_lines:
        eq = line.find("=")
        if eq > 0:
            key = line[:eq]
            if key in overlay:
                out_lines.append(overlay[key])
                replaced += 1
                continue
        out_lines.append(line)

    prefix = "\ufeff" if bom else ""
    with open(args.out, "w", encoding="utf-8", newline="\r\n") as fh:
        fh.write(prefix + "\n".join(out_lines) + "\n")

    total = len(overlay)
    print(f"Оверлеев-ключей: {total}")
    print(f"Заменено в базе: {replaced}")
    missing = total - replaced
    if missing:
        print(f"Не нашлось в базе: {missing} "
              f"(нормально, если ваш билд отличается от билда генерации)")
    print(f"Готово: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
