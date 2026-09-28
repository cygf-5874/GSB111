"""dslcheck：一个极简的配置 DSL 校验器。

对外出口::

    from dslcheck import load, validate, DslError

``load`` 把缩进式 ``key: value`` 文本解析成 :class:`Doc`，
``validate`` 按 schema 校验并返回错误消息列表。
"""

from .parser import Doc, DslError, Node, load
from .rules import STRICT, validate

__all__ = ["load", "validate", "DslError", "Doc", "Node", "STRICT"]
