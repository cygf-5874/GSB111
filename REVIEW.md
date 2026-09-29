# 代码审查结论 · dslcheck

> 每一行写**一处**没有守住「对外保证」的地方：填好「违反保证」「文件:函数」「可判定证据」三列。
> 只改本文件；`dslcheck/` 下的源码与 `tests/` 一个字节都不许动（`check/` 会校验源码哈希）。
> 「可判定证据」要能复现：给出输入形状，或直接说出抛出的异常类型；
> 不要写「看起来不对」「可能有风险」这类无法核对的话。

| 编号 | 违反保证 | 文件:函数 | 可判定证据 |
| --- | --- | --- | --- |
| D1 | 3 | rules.py:_is_int | `_is_int("01")` 返回 `True`；对 `load("port: 01")` 用 schema `{"port": {"kind": "int"}}` 调 validate 返回 `[]`，前导 0 被接受。 |
| D2 | 4 | rules.py:_validate_level | schema 里 a、b 都是必需键，对空文档 `load("")` 调 validate 只返回 `['缺少必需字段：a']`，缺失的 b 没被报出；必需字段循环末尾有 `break`。 |
| D3 | 5 | rules.py:validate | 对 `load("extra: 1")` 配空 schema 调 `validate(doc, {}, strict=False)` 仍返回 `['unknown key: extra']`；`strict` 形参从未被读取，判断只看模块级 `STRICT`。 |
| D4 | 6 | rules.py:_validate_level | 同一个 doc 连调两次 validate：第一次返回 `[]`，第二次返回 `['缺少必需字段：server']`；该函数用 `doc.index.pop(key, None)` 把传入文档的 index 清空，非纯函数。 |
| D5 | 7 | rules.py:_resolve | 对 `a: @a`（自引用）或 `a: @b` 与 `b: @a`（互引用，配空 schema）调 validate 抛 `RecursionError`；`_resolve` 沿引用链递归时不记录已访问节点。 |
| D6 | 2、8 | rules.py:validate | 错误收集进 `set` 后 `return list(errors)`：同一份输入在 `PYTHONHASHSEED` 取 0、1、2 时返回顺序互不相同，且消息形如 `字段 port 不是整数：'abc'`，没有任何一条以 `行号:` 开头。 |
