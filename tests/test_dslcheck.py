"""dslcheck 的既有用例。

覆盖范围有意保持很小：只走正常路径 —— 能解析、合法文档校验通过、
显式 ``strict=True`` 时能报到未声明字段。边界与组合情形没有被覆盖。
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dslcheck import DslError, load, validate  # noqa: E402

SCHEMA = {
    "server": {
        "kind": "block",
        "required": True,
        "fields": {
            "host": {"kind": "str", "required": True},
            "port": {"kind": "int", "required": True},
            "debug": {"kind": "bool"},
        },
    },
    "retries": {"kind": "int"},
}

GOOD = "\n".join([
    "server:",
    "  host: localhost",
    "  port: 8080",
    "  debug: false",
    "retries: 3",
    "",
])


class LoadTest(unittest.TestCase):

    def test_root_keys(self):
        doc = load(GOOD)
        self.assertEqual([node.key for node in doc.roots], ["server", "retries"])

    def test_nested_children(self):
        doc = load(GOOD)
        server = doc.find("server")
        self.assertEqual([node.key for node in server.children], ["host", "port", "debug"])
        self.assertEqual(doc.find("port").value, "8080")

    def test_skips_blank_and_comment_lines(self):
        doc = load("# 注释\n\nhost: a\n\n# 又一条注释\nport: 1\n")
        self.assertEqual([node.key for node in doc.roots], ["host", "port"])

    def test_rejects_bad_syntax(self):
        with self.assertRaises(DslError):
            load("server:\n  这行没有冒号\n")

    def test_rejects_inconsistent_indent_with_line_number(self):
        text = "a:\n  b: 1\n    c: 2\n   d: 3\n"
        with self.assertRaises(DslError) as caught:
            load(text)
        self.assertIn("4", str(caught.exception))


class ValidateTest(unittest.TestCase):

    def test_good_document_returns_empty(self):
        self.assertEqual(validate(load(GOOD), SCHEMA), [])

    def test_int_forms_are_accepted(self):
        text = "server:\n  host: h\n  port: 0x1f\nretries: +12\n"
        self.assertEqual(validate(load(text), SCHEMA), [])

    def test_bool_forms_are_accepted(self):
        text = "server:\n  host: h\n  port: 1\n  debug: true\n"
        self.assertEqual(validate(load(text), SCHEMA), [])

    def test_non_int_value_is_reported(self):
        text = "server:\n  host: h\n  port: abc\n  debug: true\n"
        errors = validate(load(text), SCHEMA)
        self.assertTrue(any("port" in message for message in errors))

    def test_missing_required_is_reported(self):
        text = "server:\n  host: h\n  debug: true\n"
        errors = validate(load(text), SCHEMA)
        self.assertTrue(any("port" in message for message in errors))

    def test_unknown_key_reported_when_strict(self):
        text = "server:\n  host: h\n  port: 1\n  debug: true\n  extra: 1\n"
        errors = validate(load(text), SCHEMA, strict=True)
        self.assertTrue(any("unknown key" in message for message in errors))

    def test_comments_inside_document_are_ignored(self):
        text = "# 顶部注释\nserver:\n  # 内层注释\n  host: h\n  port: 1\nretries: 0\n"
        self.assertEqual(validate(load(text), SCHEMA), [])


if __name__ == "__main__":
    unittest.main()
