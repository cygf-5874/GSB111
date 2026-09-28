"""DSL 解析：``key: value`` 的行式语法，用缩进表示层级。

- 每一行形如 ``key: value``；``#`` 开头是注释，空行忽略。
- 子节点的缩进必须大于父节点；同一父节点下的兄弟节点缩进必须一致。
- 解析失败抛 :class:`DslError`，消息里带行号。
"""

import re

__all__ = ["DslError", "Node", "Doc", "load"]

#: 一行的形状：key 后面跟冒号，冒号后面是值（值可以为空）。
_LINE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$")


class DslError(Exception):
    """DSL 解析错误；消息以「第 N 行：」开头。"""


class Node(object):
    """文档树里的一个节点。"""

    def __init__(self, key, value, line, indent):
        self.key = key
        self.value = value
        self.line = line
        self.indent = indent
        self.children = []

    def walk(self):
        """按文档顺序（前序）产出自己与全部后代。"""
        yield self
        for child in self.children:
            for node in child.walk():
                yield node

    def __repr__(self):
        return "Node(%r, %r, line=%d)" % (self.key, self.value, self.line)


class Doc(object):
    """解析出来的文档：根节点列表 + 按 key 建好的索引。

    ``index`` 是 ``key -> Node`` 的映射，同名 key 以后出现的为准。
    """

    def __init__(self, roots, lines):
        self.roots = roots
        self.lines = lines
        self.index = {}
        for node in self.walk():
            self.index[node.key] = node

    def walk(self):
        """按文档顺序产出全部节点。"""
        for root in self.roots:
            for node in root.walk():
                yield node

    def find(self, key):
        """按 key 找节点；找不到返回 ``None``。"""
        return self.index.get(key)


def load(text):
    """把 DSL 文本解析成 :class:`Doc`。"""
    if not isinstance(text, str):
        raise DslError("第 1 行：输入必须是字符串")

    roots = []
    stack = []

    for number, raw in enumerate(text.split("\n"), 1):
        if not raw.strip() or raw.strip().startswith("#"):
            continue

        indent = len(raw) - len(raw.lstrip(" "))
        if "\t" in raw[:indent + 1]:
            raise DslError("第 %d 行：缩进不允许用制表符" % (number,))

        match = _LINE.match(raw.strip())
        if match is None:
            raise DslError("第 %d 行：不是 key: value 形式" % (number,))

        key = match.group(1)
        value = match.group(2).strip()
        node = Node(key, value, number, indent)

        while stack and stack[-1].indent >= indent:
            stack.pop()

        if stack:
            parent = stack[-1]
            if parent.children and parent.children[-1].indent != indent:
                raise DslError("第 %d 行：缩进不一致" % (number,))
            parent.children.append(node)
        else:
            if indent != 0:
                raise DslError("第 %d 行：顶层节点不能缩进" % (number,))
            roots.append(node)

        stack.append(node)

    return Doc(roots, text.split("\n"))
