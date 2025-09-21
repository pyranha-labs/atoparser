"""Unit tests for Atop reader command."""

import os
import re
from typing import Any
from typing import Callable

import pytest

from atoparser import reader
from atoparser.parsers import atop_1_26 as atop_1_26_parsers

TEST_FILE_DIR = os.path.join(os.path.dirname(__file__), "files")
TEST_CASES = {
    "parse_file": {
        "default": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_12.log.gz"),
            ],
            "returns": {
                "stdout": [
                    '      "www": {',
                    '        "accesses": 0,',
                    '        "totkbytes": 0,',
                    '        "uptime": 0,',
                    '        "bworkers": 0,',
                    '        "iworkers": 0',
                    "      }",
                    "    }",
                    "  }",
                    "]",
                ],
                "stderr": [],
            },
        },
        "parseable valid": {
            "args": [os.path.join(TEST_FILE_DIR, "atop_1_26.log.gz"), ["CPU"]],
            "returns": {
                "stdout": [
                    '    "niced": 0,',
                    '    "idle": 600,',
                    '    "wait": 0,',
                    '    "irq": 0,',
                    '    "softirq": 0,',
                    '    "steal": 0,',
                    '    "guest": 0,',
                    '    "parseable": "CPU"',
                    "  }",
                    "]",
                ],
                "stderr": [],
            },
        },
        "parseable not supported": {
            "args": [os.path.join(TEST_FILE_DIR, "atop_2_12.log.gz"), ["CPU"]],
            "returns": {
                "stdout": [
                    "[",
                    "  {",
                    '    "error": "Atop version 2.12 does not support parseables, only full raw output.",',
                    '    "file": "replaced_by_test"',
                    "  }",
                    "]",
                ],
                "stderr": [],
            },
        },
    },
}


@pytest.mark.parametrize_test_case("test_case", TEST_CASES["parse_file"])
def test_parse_file(test_case: dict, function_tester: Callable, capsys: pytest.CaptureFixture) -> None:
    """Read a file and ensure the values in the records match expectations."""

    def _get_struct(*args: Any, **kwargs: Any) -> dict:
        """Read a file and return the last few lines to simplify testing and ensure the file processed correctly."""
        reader.parse_file(*args, **kwargs)
        captured = capsys.readouterr()
        stdout = captured.out.strip().splitlines()[-10:]
        for index, line in enumerate(stdout):
            if '"file":' in line:
                stdout[index] = re.sub(r'"file": ".*?"', '"file": "replaced_by_test"', line)
        return {
            "stdout": stdout,
            "stderr": captured.err.strip().splitlines()[-10:],
        }

    function_tester(test_case, _get_struct)


@pytest.mark.parametrize_test_case("parseable", reader.PARSEABLES)
def test_parseable_map(parseable: str) -> None:
    """Unit test to ensure every parseable has a corresponding parse_* function."""
    assert getattr(atop_1_26_parsers, f"parse_{parseable}") is not None, (
        f"Failed to find parse function for {parseable}"
    )
