"""Basic lints for lark grammars."""

import re
import typing as t

import attr
import astroid
import pyglint

# Setup
###############

group = pyglint.CheckerGroup("pylint-lark")


@attr.s(auto_attribs=True, order=False)
class GrammarCheckerRegistry:
    """Registry for collecting grammar checkers.."""

    functions: t.List[t.Callable] = attr.ib(factory=list)

    def checker(self, function):
        self.functions.append(function)
        return function


@group.check(astroid.node_classes.Call)
def check_grammar(checker, node) -> t.Iterator[pyglint.Message]:
    """Generate messages for Lark grammars."""

    if isinstance(node, astroid.node_classes.Attribute):
        if node.func.expr.name != "lark":
            return
        if node.func.attrname != "Lark":
            return

    if isinstance(node, astroid.node_classes.Call):
        if node.func.name != "Lark":
            return

    first_argument = node.args[0]
    # Take the first inferred guess about the value of the grammar.
    node = next(first_argument.infer())

    # Assumes the grammar is provided as a string literal. If the grammar is loaded from a
    # file or with importlib.resources, code can be added here to handle that case.
    grammar = node.value

    for function in registry.functions:  # pylint: disable=not-an-iterable
        for msg in function(grammar, node):
            msg = attr.evolve(msg, line=msg.line + node.lineno - grammar.count("\n"))
            yield msg


def register(linter):
    """Register checkers."""
    checker = pyglint.make_pylint_checker(group)
    linter.register_checker(checker(linter))


registry = GrammarCheckerRegistry()

# Define problems
##########################


BAD_NAME = group.problem(
    name="bad-name",
    text="The name '{identifier}' is against the guidelines.",
    explanation="It's a good idea to have a useful and descriptive name. For example, Counter instead of ctr.",
)


# Define checkers
############################


@registry.checker
def metasyntactic_names(grammar: str, node) -> t.Iterator[pyglint.Message]:
    """Identify some metasyntactic names literally."""
    for lineno, line in enumerate(grammar.splitlines()):
        for match in re.finditer("(foo|bar|baz|quux)", line):
            yield pyglint.message(
                problem=BAD_NAME,
                node=node,
                line=lineno,
                col_offset=match.start(),
                identifier=match.group(1),
            )


@registry.checker
def short_names(grammar: str, node) -> t.Iterator[pyglint.Message]:
    """Identify short names."""

    for lineno, line in enumerate(grammar.splitlines()):
        for match in re.finditer(r"\b([A-Za-z])\b", line):
            yield pyglint.message(
                problem=BAD_NAME,
                node=node,
                line=lineno,
                col_offset=match.start(),
                identifier=match.group(1),
            )
