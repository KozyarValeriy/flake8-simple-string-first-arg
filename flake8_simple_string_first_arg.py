import ast
import sys
from _ast import FormattedValue
from typing import Any, Dict, Generator, List, Optional, Set, Type

if sys.version_info < (3, 8):  # pragma: no cover
    import importlib_metadata
else:
    import importlib.metadata as importlib_metadata

FSTRING_VIOLATION = 'SFA100: In calling {} f-string is used'
STRING_FORMAT_VIOLATION = 'SFA200: In calling {} string.format() is used'
STRING_CONCAT_VIOLATION = 'SFA300: In calling {} string concatenation ("+") is used'
PERCENT_FORMAT_VIOLATION = 'SFA400: In calling {} "%" is used'


class Visitor(ast.NodeVisitor):
    def __init__(self, callable_for_check: Dict[str, Set[str]]) -> None:
        self.current_call: Optional[ast.Call] = None
        self.in_current_call_argument: bool = False

        self.callable_for_check = callable_for_check

        self.errors: list[tuple[int, int, str]] = []

    @property
    def is_observed_call_argument(self) -> bool:
        return self.current_call is not None and self.in_current_call_argument

    @property
    def current_observed_keyword(self) -> Set[str]:
        return self.callable_for_check.get(self.current_call_name, set())

    @property
    def current_call_name(self) -> str:
        if self.current_call is not None:
            return self.current_call.func.id  # type: ignore
        return ''

    def format_error(self, error_template: str) -> str:
        return error_template.format(self.current_call_name)

    def visit_Call(self, node: ast.Call) -> None:
        # in checked class call statement
        if self.is_observed_call_argument and self.is_format_call(node):
            self.errors.append((node.lineno, node.col_offset, self.format_error(STRING_FORMAT_VIOLATION)))
            self.generic_visit(node)
            return

        # in some other call statement
        if not isinstance(node.func, ast.Name) or node.func.id not in self.callable_for_check:
            self.generic_visit(node)
            return

        # in new checked class call statement
        self.current_call = node

        for index, child in enumerate(ast.iter_child_nodes(node)):
            if index == 1:
                self.in_current_call_argument = True
            if index > 1 and isinstance(child, ast.keyword) and child.arg in self.current_observed_keyword:
                self.in_current_call_argument = True

            self.visit(child)
            self.in_current_call_argument = False

        self.current_call = None

    def visit_JoinedStr(self, node: ast.JoinedStr) -> None:
        if self.is_observed_call_argument:
            if any(isinstance(i, FormattedValue) for i in node.values):
                self.errors.append((node.lineno, node.col_offset, self.format_error(FSTRING_VIOLATION)))
        self.generic_visit(node)

    def visit_BinOp(self, node) -> None:
        if self.is_observed_call_argument:
            # handle percent format ('%s' % 'some')
            if isinstance(node.op, ast.Mod):
                self.errors.append((node.lineno, node.col_offset, self.format_error(PERCENT_FORMAT_VIOLATION)))
            # handle string concat ('some' + '123')
            if isinstance(node.op, ast.Add):
                self.errors.append((node.lineno, node.col_offset, self.format_error(STRING_CONCAT_VIOLATION)))
        self.generic_visit(node)

    def is_format_call(self, node: ast.Call) -> bool:
        try:
            return node.func.attr == 'format'  # type: ignore
        except AttributeError:  # pragma: no cover
            return False


class Plugin:
    name = __name__
    check_callable_names_option_shortname_for_cli = 'sfa'
    check_callable_names_option_fullname_for_cli = 'simple-string-first-arg'
    check_callable_names_option_name_for_conf = 'simple_string_first_arg'

    default_check_callable_names: List[str] = []
    _callable_for_check: Dict[str, Set[str]] = {}

    version = importlib_metadata.version(__name__)

    def __init__(self, tree: ast.AST) -> None:
        self._tree = tree

    @classmethod
    def add_options(cls, parser):  # pragma: no cover
        """Required by flake8
        add the possible options, called first
        Args:
            parser (OptionsManager):
        """
        kwargs = {'action': 'store', 'parse_from_config': True, 'comma_separated_list': True}
        parser.add_option(
            f'-{cls.check_callable_names_option_shortname_for_cli}',
            f'--{cls.check_callable_names_option_fullname_for_cli}',
            default=', '.join(cls.default_check_callable_names),
            **kwargs,
        )

    @classmethod
    def parse_options(cls, options):  # pragma: no cover
        """Required by flake8
        parse the options, called after add_options
        Args:
            options (dict): options to be parsed
        """
        callable_for_check = getattr(
            options, cls.check_callable_names_option_name_for_conf, cls.default_check_callable_names
        )
        cls._callable_for_check = {k: set(v) for k, *v in (arg.split(':') for arg in callable_for_check)}

    def run(self) -> Generator[tuple[int, int, str, Type[Any]], None, None]:
        """
        Any module from specified package could not be import in another package
        """
        if not self._callable_for_check:
            return
        visitor = Visitor(callable_for_check=self._callable_for_check)
        visitor.visit(self._tree)
        for line, col, msg in visitor.errors:
            yield line, col, msg, type(self)
