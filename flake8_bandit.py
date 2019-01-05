"""Implementation of bandit security testing in Flake8."""
import ast

import pycodestyle
from bandit.core.config import BanditConfig
from bandit.core.meta_ast import BanditMetaAst
from bandit.core.metrics import Metrics
from bandit.core.node_visitor import BanditNodeVisitor
from bandit.core.test_set import BanditTestSet

__version__ = "2.0.0"


class BanditTester(object):
    """Flake8 class for checking code for bandit test errors.

    This class is necessary and used by flake8 to check the python
    file or files that are being tested.

    """

    name = "flake8-bandit"
    version = __version__

    def __init__(self, tree, filename, lines):
        self.filename = filename
        self.tree = tree
        self.lines = lines

    def _check_source(self):
        bnv = BanditNodeVisitor(
            self.filename,
            BanditMetaAst(),
            BanditTestSet(BanditConfig()),
            False,
            [],
            Metrics(),
        )
        bnv.generic_visit(self.tree)
        return [
            {
                # flake8-bugbear uses bandit default prefix 'B'
                # so this plugin replaces the 'B' with an 'S' for Security
                # See https://github.com/PyCQA/flake8-bugbear/issues/37
                "test_id": item.test_id.replace("B", "S"),
                "issue_text": item.text,
                "line_number": item.lineno,
            }
            for item in bnv.tester.results
        ]

    def run(self):
        """run will check file source through the bandit code linter."""

        if not self.tree or not self.lines:
            self._load_source()
        for warn in self._check_source():
            message = "%s %s" % (warn["test_id"], warn["issue_text"])
            yield (warn["line_number"], 0, message, type(self))

    def _load_source(self):
        """Loads the file in a way that auto-detects source encoding and deals
        with broken terminal encodings for stdin.

        Stolen from flake8_import_order because it's good.
        """

        if self.filename in ("stdin", "-", None):
            self.filename = "stdin"
            self.lines = pycodestyle.stdin_get_value().splitlines(True)
        else:
            self.lines = pycodestyle.readlines(self.filename)
        if not self.tree:
            self.tree = ast.parse("".join(self.lines))
