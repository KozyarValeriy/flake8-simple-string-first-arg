import ast
from typing import Dict, List, Set

import pytest

from flake8_simple_string_first_arg import (
    FSTRING_VIOLATION,
    PERCENT_FORMAT_VIOLATION,
    STRING_CONCAT_VIOLATION,
    STRING_FORMAT_VIOLATION,
    Plugin,
)

OBSERVED_CALL = 'SomeClassName'
SFA100 = FSTRING_VIOLATION.format(OBSERVED_CALL)
SFA200 = STRING_FORMAT_VIOLATION.format(OBSERVED_CALL)
SFA300 = STRING_CONCAT_VIOLATION.format(OBSERVED_CALL)
SFA400 = PERCENT_FORMAT_VIOLATION.format(OBSERVED_CALL)


def lint_code(loc: str, callable_for_check: Dict[str, Set[str]]) -> List[str]:
    tree = ast.parse(loc)
    plugin = Plugin(tree)
    plugin._callable_for_check = callable_for_check  # pylint: disable=protected-access
    return [f'{line}:{col} {message}' for line, col, message, _ in plugin.run()]


@pytest.mark.parametrize(
    ('code', 'error'),
    [
        ('SomeClassName(f"{abc}")', SFA100),
        ('SomeClassName(url=f"{abc}")', SFA100),
        ('SomeClassName(test=f"{abc}")', SFA100),
        ('SomeClassName(a=1, url=f"{abc}")', SFA100),
        ('SomeClassName("{}".format("some"))', SFA200),
        ('SomeClassName(url="{}".format("some"))', SFA200),
        ('SomeClassName(test="{}".format("some"))', SFA200),
        ('SomeClassName(a=1, url="{}".format("some"))', SFA200),
        ('SomeClassName("a" + "b")', SFA300),
        ('SomeClassName(url="a" + "b")', SFA300),
        ('SomeClassName(test="a" + "b")', SFA300),
        ('SomeClassName(a=1, url="a" + "b")', SFA300),
        ('SomeClassName("%s" % "b")', SFA400),
        ('SomeClassName(url="%s" % "b")', SFA400),
        ('SomeClassName(test="%s" % "b")', SFA400),
        ('SomeClassName(a=1, url="%s" % "b")', SFA400),
    ],
)
def test_bad_args(code, error):
    errors = lint_code(code, {OBSERVED_CALL: {'url', 'test'}})
    assert len(errors) == 1, errors
    assert error in errors[0], errors


@pytest.mark.parametrize(
    ('code', 'observed_call_dict'),
    [
        ('OtherClassName(f"{abc}")', {OBSERVED_CALL: {'url', 'test'}}),
        ('SomeClassName(url="some")', {OBSERVED_CALL: {'url', 'test'}}),
        ('SomeClassName(url="some".lower())', {OBSERVED_CALL: {'url', 'test'}}),
        ('SomeClassName(a="some_param", url=f"some {abc}")', {OBSERVED_CALL: set()}),
        ('SomeClassName(url="other", test="test")', {OBSERVED_CALL: {'url', 'test'}}),
        ('SomeClassName(url="other", test=f"test {abc}")', {OBSERVED_CALL: {'url'}}),
        ('SomeClassName(a=1, url="other", test="test")', {OBSERVED_CALL: {'url', 'test'}}),
        ('SomeClassName("other", test="test")', {OBSERVED_CALL: {'url', 'test'}}),
        ('SomeClassName(f"some {abc}")', {}),
    ],
)
def test_not_errors(code, observed_call_dict):
    errors = lint_code(code, observed_call_dict)
    assert len(errors) == 0, errors
