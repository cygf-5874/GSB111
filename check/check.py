#!/usr/bin/env python3
"""dslcheck 审查题的固定验收入口。**别改这个文件。**

只校验 ``REVIEW.md`` 的交付格式、6 行结论各自命中的「违反保证」编号与「文件:函数」，
以及三个源码文件的 SHA-256 未变；结论是否正确由人按 README 逐条复核。

用法::

    python3 check/check.py                  # 跑全部 8 个场景
    python3 check/check.py -list            # 列出全部场景
    python3 check/check.py --only format    # 只跑一组（可逗号分隔多组）
"""

import hashlib
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REVIEW_REL = "REVIEW.md"

COLUMNS = ("编号", "违反保证", "文件:函数", "可判定证据")
ROW_IDS = ("D1", "D2", "D3", "D4", "D5", "D6")

#: 三个源码文件的 SHA-256 基线（先把行尾统一成 LF 再算）。建仓时生成。
BASELINE = {
    "dslcheck/__init__.py": "de59daa9a9be2d3bb33242a14ca957a29c051cfa8ec66310ac933a77e071ba85",
    "dslcheck/parser.py": "27b247a25e84ad3689b7ce783b2c19283519291f62e50538381279118361b521",
    "dslcheck/rules.py": "aa9e30e2521b6db200d107b5f4553d6c13feac2813dfb657203d9c6920bd0453",
}

#: 6 处缺陷各自允许的「违反保证」编号与「文件:函数」。
DEFECTS = (
    {"id": "D1", "guarantees": (3,),
     "locations": ("rules.py:_is_int", "rules.py:_check_type")},
    {"id": "D2", "guarantees": (4,),
     "locations": ("rules.py:_validate_level", "rules.py:_check_required",
                   "rules.py:validate")},
    {"id": "D3", "guarantees": (5,),
     "locations": ("rules.py:validate", "rules.py:_validate_level",
                   "rules.py:STRICT")},
    {"id": "D4", "guarantees": (6,),
     "locations": ("rules.py:_validate_level", "rules.py:validate")},
    {"id": "D5", "guarantees": (7,),
     "locations": ("rules.py:_resolve", "rules.py:_check_cycles", "rules.py:validate")},
    {"id": "D6", "guarantees": (2, 8),
     "locations": ("rules.py:validate", "rules.py:_validate_level")},
)

PLACEHOLDERS = ("TODO", "todo", "FIXME", "待填", "待补", "待定",
                "看起来", "可能有风险", "或许", "大概")

SCENARIOS = []


def fail(expected, actual):
    return "期望=%s 实际=%s" % (expected, actual)


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError:
        return None


def file_sha256(path):
    with open(path, "rb") as handle:
        raw = handle.read()
    return hashlib.sha256(raw.replace(b"\r", b"")).hexdigest()


def scenario(name):
    def decorate(function):
        SCENARIOS.append((name, function))
        return function

    return decorate


# ---------------------------------------------------------------------------
# REVIEW.md 表格解析
# ---------------------------------------------------------------------------


def _split_row(line):
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return cells


def _is_separator(cells):
    return bool(cells) and set("".join(cells)) <= set("-: ")


def parse_table(text):
    """返回 (表头, 数据行列表)；表头与分隔行之外的行都算数据行。"""
    if text is None:
        return None, []
    header = None
    rows = []
    for raw in text.split("\n"):
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = _split_row(line)
        if len(cells) != 4 or _is_separator(cells):
            continue
        if header is None:
            header = cells
        else:
            rows.append(cells)
    return header, rows


REVIEW_TEXT = read_text(os.path.join(ROOT, REVIEW_REL))
HEADER, ROWS = parse_table(REVIEW_TEXT)


def _norm(text):
    out = text.strip().lower()
    out = out.replace("\\", "/").replace("：", ":")
    for token in ("(", ")", "（", "）"):
        out = out.replace(token, "")
    out = re.sub(r"\s+", "", out)
    if out.startswith("./"):
        out = out[2:]
    return out


def _guarantee_numbers(cell):
    return set(int(token) for token in re.findall(r"\d+", cell))


def _row_covers(row, defect):
    if not (_guarantee_numbers(row[1]) & set(defect["guarantees"])):
        return False
    location = _norm(row[2])
    if not location:
        return False
    return any(_norm(allowed) in location for allowed in defect["locations"])


def _matching(rows):
    """把数据行匹配到 6 处缺陷上，返回 {缺陷下标: 行下标}。"""
    adjacency = [[index for index, row in enumerate(rows) if _row_covers(row, defect)]
                 for defect in DEFECTS]
    taken = [-1] * len(rows)

    def augment(defect_index, visited):
        for row_index in adjacency[defect_index]:
            if visited[row_index]:
                continue
            visited[row_index] = True
            holder = taken[row_index]
            if holder == -1 or augment(holder, visited):
                taken[row_index] = defect_index
                return True
        return False

    for defect_index in range(len(DEFECTS)):
        augment(defect_index, [False] * len(rows))

    result = {}
    for row_index, defect_index in enumerate(taken):
        if defect_index != -1:
            result[defect_index] = row_index
    return result


MATCHING = _matching(ROWS) if ROWS else {}


# ---------------------------------------------------------------------------
# unmodified 1
# ---------------------------------------------------------------------------


@scenario("unmodified/sources")
def check_unmodified_sources():
    for rel in sorted(BASELINE):
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            return fail("%s 存在" % rel, "缺失")
        if file_sha256(path) != BASELINE[rel]:
            return fail("%s 保持原样（SHA-256 与基线一致）" % rel, "内容已被改动")
    return None


# ---------------------------------------------------------------------------
# format 1
# ---------------------------------------------------------------------------


@scenario("format/table")
def check_format_table():
    if REVIEW_TEXT is None:
        return fail("REVIEW.md 存在且含一张结论表", "文件不存在")
    if HEADER is None:
        return fail("REVIEW.md 里有 4 列的 markdown 表格", "没有找到表格")
    normalized = tuple(_norm(cell) for cell in HEADER)
    expected = tuple(_norm(cell) for cell in COLUMNS)
    if normalized != expected:
        return fail("表头 = %s" % (list(COLUMNS),), "= %s" % (HEADER,))
    if len(ROWS) != len(ROW_IDS):
        return fail("表格有 %d 行" % len(ROW_IDS), "有 %d 行" % len(ROWS))
    labels = [_norm(row[0]) for row in ROWS]
    if sorted(labels) != sorted(_norm(name) for name in ROW_IDS):
        return fail("行号是 D1~D6", "= %s" % (labels,))
    return None


# ---------------------------------------------------------------------------
# finding 6
# ---------------------------------------------------------------------------


def _finding_scenario(defect_index):
    defect = DEFECTS[defect_index]

    def check():
        if not ROWS:
            return fail("表格里已填出 %s 这一行" % defect["id"], "没有数据行")
        row_index = MATCHING.get(defect_index)
        if row_index is None:
            return fail(
                "%s 命中「违反保证 ∈ %s、文件:函数 ∈ %s」"
                % (defect["id"], list(defect["guarantees"]), list(defect["locations"])),
                "没有一行同时满足这两列",
            )
        row = ROWS[row_index]
        evidence = re.sub(r"\s+", "", row[3])
        if len(evidence) < 8:
            return fail("%s 的「可判定证据」给出具体现象" % defect["id"],
                        "去空白后过短")
        for word in PLACEHOLDERS:
            if word in row[3]:
                return fail("%s 的「可判定证据」不含占位词" % defect["id"],
                            "出现「%s」" % word)
        return None

    check.__name__ = "check_finding_%s" % defect["id"].lower()
    return check


for _index, _defect in enumerate(DEFECTS):
    SCENARIOS.append(("finding/%s" % _defect["id"], _finding_scenario(_index)))


# ---------------------------------------------------------------------------
# 运行器
# ---------------------------------------------------------------------------


def main(argv):
    only = []
    do_list = False
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "-list":
            do_list = True
        elif arg == "--only":
            index += 1
            if index >= len(argv):
                print("--only 需要一个组名", file=sys.stderr)
                return 2
            only.extend(part for part in argv[index].split(",") if part)
        else:
            print("未知参数：%s" % arg, file=sys.stderr)
            return 2
        index += 1

    if do_list:
        for name, _function in SCENARIOS:
            print(name)
        return 0

    total = 0
    passed = 0
    for name, function in SCENARIOS:
        group = name.split("/", 1)[0]
        if only and group not in only:
            continue
        total += 1
        try:
            problem = function()
        except Exception as exc:  # noqa: BLE001
            problem = fail("检查正常完成", "检查过程抛异常：%s: %s" % (type(exc).__name__, exc))
        if problem is None:
            passed += 1
            print("PASS " + name)
        else:
            print("FAIL " + name + "  " + problem)

    if total == 0:
        print("没有匹配的场景（--only %s）" % ",".join(only))
        return 2

    print("结果：通过 %d/%d" % (passed, total))
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
