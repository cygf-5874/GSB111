上线之前想请人从头看一遍。dslcheck 是 Python 3 的配置 DSL 校验器，
只用标准库，构建不需要额外步骤，
自检走 `scripts/check.sh`（`check/` 是固定验收程序，别改），既有用例走
`python3 -m unittest discover -s tests`。

README 里的「对外保证」8 条是这份实现的契约，三个源码文件里有若干处没有守住。

任务：通读源码，把 `REVIEW.md` 里那张表填满 —— 每个问题一行，
写清它违反哪一条保证、出在哪个文件的哪个函数、以及一句可判定的证据
（要能复现：别人照你说的输入能看出区别，或者能说出抛的异常类型）。

验收：
- python3 check/check.py 退出码 0，8 个场景全过（unmodified 1 + format 1 + finding 6）；
- 源码文件一个字节都不许改，`check/` 会校验哈希。

约束：
1. 只改 `REVIEW.md`；`dslcheck/` 下的源码与 `tests/` 一律不动。
2. 不改 `check/`。
3. 只用标准库，不许引入任何第三方包。
4. 证据一列不要写「看起来不对」「可能有风险」这类话。
