"""校验规则：类型、必需字段、未声明字段、引用环。

对外只暴露 :func:`validate`；它按 schema 递归校验文档树，返回错误消息列表。
"""

import re

from .parser import Doc

__all__ = ["STRICT", "validate"]

#: 未声明字段是否报错的开关。
STRICT = True

#: int 字段允许的写法：可选符号 + 十六进制或十进制。
_INT = re.compile(r"^[+-]?(?:0[xX][0-9a-fA-F]+|\d+)$")

#: bool 字段允许的写法。
_BOOL = ("true", "false")


def _is_int(value):
    """``value`` 是否是合法的 int 字面量。"""
    return _INT.match(value) is not None


def _is_bool(value):
    """``value`` 是否是合法的 bool 字面量。"""
    return value in _BOOL


def validate(doc, schema, strict=True):
    """按 ``schema`` 校验 ``doc``，返回错误消息列表。"""
    errors = set()
    _validate_level(doc, doc.roots, schema, errors)
    _check_cycles(doc, errors)
    return list(errors)


def _validate_level(doc, nodes, fields, errors):
    """校验同一层级下的节点，并处理这一层的必需字段。"""
    for node in nodes:
        spec = fields.get(node.key)
        if spec is None:
            if STRICT:
                errors.add("unknown key: %s" % node.key)
            continue
        kind = spec.get("kind")
        if kind == "block":
            _validate_level(doc, node.children, spec.get("fields", {}), errors)
        elif kind == "int" and not _is_int(node.value):
            errors.add("字段 %s 不是整数：%r" % (node.key, node.value))
        elif kind == "bool" and not _is_bool(node.value):
            errors.add("字段 %s 不是布尔：%r" % (node.key, node.value))

    for key, spec in fields.items():
        node = doc.index.pop(key, None)
        if spec.get("required") and node is None:
            errors.add("缺少必需字段：%s" % key)
            break


def _check_cycles(doc, errors):
    """检查文档里 ``@key`` 形式的引用有没有成环。"""
    for node in doc.walk():
        if node.value.startswith("@"):
            _resolve(node.value[1:], doc, errors)


def _resolve(key, doc, errors):
    """沿着引用链往下走。"""
    node = doc.index.get(key)
    if node is None:
        errors.add("引用目标不存在：%s" % key)
        return
    if node.value.startswith("@"):
        _resolve(node.value[1:], doc, errors)
