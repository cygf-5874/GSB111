#!/usr/bin/env bash
# 固定验收入口：校验 REVIEW.md 的交付格式、6 行结论各自命中的保证编号与文件:函数，
# 以及三个源码文件的 SHA-256 未变。**别改这个文件。**
# 用法：bash scripts/check.sh [-list] [--only <组名>]
set -euo pipefail

cd "$(dirname "$0")/.."

exec python3 check/check.py "$@"
