# 代码审查结论 · dslcheck

> 每一行写**一处**没有守住「对外保证」的地方：填好「违反保证」「文件:函数」「可判定证据」三列。
> 只改本文件；`dslcheck/` 下的源码与 `tests/` 一个字节都不许动（`check/` 会校验源码哈希）。
> 「可判定证据」要能复现：给出输入形状，或直接说出抛出的异常类型；
> 不要写「看起来不对」「可能有风险」这类无法核对的话。

| 编号 | 违反保证 | 文件:函数 | 可判定证据 |
| --- | --- | --- | --- |
| D1 | 3 | rules.py:_is_int | `load("age: 01")` 后调用 `validate(doc, {"age": {"kind": "int"}})` 返回 `[]`：前导 0 的 `01`、`007` 都被 `_INT` 正则接受，未报类型错误。 |
| D2 | 4 | rules.py:_validate_level | schema 里 `a`、`b` 均为 required，文档只有 `c: 1` 时，`validate` 只返回 `缺少必需字段：a`；必需字段循环末尾的 `break` 使同层缺失的 `b` 不被报出。 |
| D3 | 5 | rules.py:validate | `validate(load("x: 1"), {}, strict=False)` 仍返回 `['unknown key: x']`：`strict` 形参未被使用，`_validate_level` 判断的是模块级常量 `STRICT`。 |
| D4 | 6 | rules.py:_validate_level | 检查必需字段时执行 `doc.index.pop(key, None)` 改写传入的 doc；同一 `doc`/`schema` 连调两次，第一次返回 `[]`，第二次返回 `['缺少必需字段：a']`。 |
| D5 | 7 | rules.py:_resolve | 文档为 `a: @a`（或 `a: @b` 与 `b: @a`）时调用 `validate` 抛 `RecursionError`：引用链无已访问集合，自引用/循环引用不被检出反而无限递归。 |
| D6 | 2、8 | rules.py:validate | `a`/`b`/`c` 三个 int 字段都非法时，返回的消息均不以 `行号:` 开头（如 `字段 c 不是整数：'z'`），且错误按 c、b、a 逆序给出，不按文档顺序；消息取自 set，顺序不稳定。 |
