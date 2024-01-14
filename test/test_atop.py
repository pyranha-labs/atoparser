"""Unit tests for Atop utilities."""

import gzip
import io
import json
import os
import zlib
from typing import Callable

import pytest

from pyatop import atop_helpers
from pyatop import atop_reader
from pyatop.parsers import atop_1_26 as atop_1_26_parsers
from pyatop.structs import atop_1_26 as atop_1_26_structs

# Raw byes from an Atop file which can be used to simulate reading the file.
# Samples taken from 1.26 test log.
HEADER_BYTES = b"\xef\xbe\xed\xfe\x1a\x81\x00\x00\x00\x00\xe0\x01P\x00d\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x000Y\x01\x00h\x02\x00\x00Linux\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00fires-of-mount-doom1\x00theshire.co\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x005.10.104-linuxkit\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00#1 SMP Thu Mar 17 17:08:06 UTC 2022\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00x86_64\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00(none)\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x04\x00\x00\x00\x05\x00\x00\x00\n\x00\x00\x00h\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
RECORD_BYTES = b"!\xe7\xa2e\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x1b\x02\x00\x00\x0f\x01\x00\x00\xed`\x01\x00\x02\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
SSTAT_BYTES = b'x\x9c\xed\xdc\xbdk\x14A\x18\x07\xe0\xe8\xe9%F\x83\x82`\xb01~ \x18+A8\x08\x88\xa4\xd6\x80\x01\xb5\xd2+"\x06"^T\xe4\x92\xc2B,\x15m\x05\xed,\xec\x04\xc1F%\xa0D\xb0P\xd4NP\xfc\x07\x84\x98\xc2\xc6/,N\xdc\x99Uv1\xb9\xbb\r&\x90<O\xf3\xe3fv\xf6\xdd\xbda\xd8b\xf6\xae\xdc\x11L<\xbe\x9b\xe4\xec\xf8L\x92O\x8e\x85\xf6\xeew\xbb\x0et\x14\xf0\xb1\x12\xf2\xe4p\xb6\xbdsx\xa0\xf4;/wf\xdb\xbf\x96\x8aT\xf9\xeb{w\xc8W\x1b\xb2\xed\xf7/^K\xf2\xec\xaal{5\xf79\xefV\xd7\xbf\xdb\xd3a;b\xbd\xcf\x1b\xb3\xfd\x0f\xae\x86z\x95\xdc\xf9_\xce_n\xcez\xabcV\xe2}\x1d\xdd\x94\xed\xef\x1a\x0b\xf5\xfar\xf5^\x17\xac\x97NC5\xce\xcf\x9e\x9el\xff\xd0\x9dP\xefT\xae\xde\xf1\x82\xf5\xd6\xc4<\x12\xeb\x1d\xca\xcd\xdf\x89{\xa1\xdeH\xae\xdex\xc1zkc\xce\x94C\xbe_\x97\xed\xff\x16\xef\xefGn\xdc`\xc1z\x00\x00\x00\x00\x00\x00\xb4\xe7Co_\x92\xcfG\xb7&\xd9\xbf=l\x14\xf5\x7f\n\xfd\x93Sa\x07-\xdd\xd7j4J\x99lf\xf6\xfa\xe6$/\xddX\xdf\xd2\xf1\xe96\xd5`\xcc\xa9\xfd-\r\xfb#=~wo{\xe3V\x9a\xb9f/m\xef\x99\xa3\xbf\x99\xa2\xe3X\x98t\xdd\xbc\x889\xfd6\xb44\xa2r\x8b\xe7y\x14\xd7\xcf\xce&\xeb\'\xddw\xae\x9do\xe3"\x97\xa1\xfa\xc4\xb9\xda\xbe\xa5\xbe\x88%t\xe6B\xa5\xbe\x92\xbf\x81\xd1\xfaX\xe6\xe6\x9f\xde\xdc\x92,\xbc7m>\xb7Z\xf5\xe5gXy{\xff\xf3\xf3\xad\xc9\xeb=\x00\x00\x00\x00\x00\x00\xc02\x94\xdf\'\x9c<=2\xef\xf1\xb5j\xc8\x87W\xc2\x0f\xff\x0fn\x0bg\x98\x1e\n/\x12\x0c\xdc\x0e\xfd\xcf\x0e/\xf0\x0f\r\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00XT\xbf\x00;/O\xbc'

TEST_FILE_DIR = os.path.join(os.path.dirname(__file__), "files")

TEST_CASES = {
    "file_header": {
        "1.26": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_1_26.log.gz"),
            ],
            "returns": {
                "aversion": 33050,
                "hertz": 100,
                "magic": 4276993775,
                "osrel": 5,
                "ossub": 104,
                "osvers": 10,
                "pagesize": 4096,
                "pstatlen": 616,
                "rawheadlen": 480,
                "rawreclen": 80,
                "semantic_version": "1.26",
                "sstatlen": 88368,
                "supportflags": 4,
                "utsname": {
                    "domain": "(none)",
                    "machine": "x86_64",
                    "nodename": "fires-of-mount-doom1",
                    "release": "5.10.104-linuxkit",
                    "sysname": "Linux",
                    "version": "#1 SMP Thu Mar 17 17:08:06 UTC 2022",
                },
            },
        },
        "2.3": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_3.log.gz"),
            ],
            "returns": {
                "aversion": 33283,
                "hertz": 100,
                "magic": 4276993775,
                "osrel": 5,
                "ossub": 104,
                "osvers": 10,
                "pagesize": 4096,
                "rawheadlen": 480,
                "rawreclen": 96,
                "semantic_version": "2.3",
                "sstatlen": 711904,
                "supportflags": 53,
                "tstatlen": 784,
                "utsname": {
                    "domain": "(none)",
                    "machine": "x86_64",
                    "nodename": "fires-of-mount-doom1",
                    "release": "5.10.104-linuxkit",
                    "sysname": "Linux",
                    "version": "#1 SMP Thu Mar 17 17:08:06 UTC 2022",
                },
            },
        },
    },
    "file_record": {
        "1.26": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_1_26.log.gz"),
            ],
            "returns": {
                "curtime": 1705174821,
                "flags": 0,
                "interval": 1,
                "nexit": 0,
                "nlist": 1,
                "npresent": 2,
                "ntrun": 1,
                "ntslpi": 1,
                "ntslpu": 0,
                "nzombie": 0,
                "pcomplen": 113,
                "record_index": 4,
                "scomplen": 313,
            },
        },
        "2.3": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_3.log.gz"),
            ],
            "returns": {
                "curtime": 1705175104,
                "flags": 32,
                "interval": 1,
                "nactproc": 1,
                "ndeviat": 2,
                "nexit": 0,
                "noverflow": 0,
                "ntask": 2,
                "pcomplen": 276,
                "record_index": 4,
                "scomplen": 949,
                "totproc": 2,
                "totrun": 1,
                "totslpi": 1,
                "totslpu": 0,
                "totzomb": 0,
            },
        },
    },
    "file_sstat": {
        "1.26": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_1_26.log.gz"),
            ],
            "returns": {
                "cpu": {
                    "nrcpu": 6,
                    "lavg1": 0.0,
                },
                "mem": {
                    "physmem": 2037722,
                    "freemem": 1664263,
                },
                "intf": {
                    "nrintf": 4,
                    "intf": [{"name": "lo"}],
                },
                "dsk": {
                    "ndsk": 1,
                    "dsk": [{"name": "vda"}],
                },
                "sample_index": 4,
            },
        },
        "2.3": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_3.log.gz"),
            ],
            "returns": {
                "cpu": {
                    "nrcpu": 6,
                    "lavg1": 0.019999999552965164,
                },
                "mem": {
                    "physmem": 2037722,
                    "freemem": 1652417,
                },
                "intf": {
                    "nrintf": 4,
                    "intf": [{"name": "lo"}],
                },
                "dsk": {
                    "ndsk": 1,
                    "dsk": [{"name": "vda"}],
                },
                "sample_index": 4,
            },
        },
    },
    "file_tstat": {
        "1.26": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_1_26.log.gz"),
            ],
            "returns": {
                "gen": {
                    "cmdline": "atop 1 5 -w /mnt/pyatop/atop_1_26.log",
                    "name": "atop",
                },
                "sample_index": 4,
                "tstat_index": 0,
            },
        },
        "2.3": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_3.log.gz"),
            ],
            "returns": {
                "gen": {
                    "cmdline": "atop 1 5 -w /mnt/pyatop/test/files/atop_2_3.log",
                    "name": "atop",
                },
                "sample_index": 4,
                "tstat_index": 1,
            },
        },
    },
    "get_header": {
        "Valid": {
            "args": [
                io.BytesIO(HEADER_BYTES),
            ],
            "returns": {
                "aversion": 33050,
                "hertz": 100,
                "magic": 4276993775,
                "osrel": 5,
                "ossub": 104,
                "osvers": 10,
                "pagesize": 4096,
                "pstatlen": 616,
                "rawheadlen": 480,
                "rawreclen": 80,
                "sstatlen": 88368,
                "supportflags": 4,
                "utsname": {
                    "domain": "(none)",
                    "machine": "x86_64",
                    "nodename": "fires-of-mount-doom1",
                    "release": "5.10.104-linuxkit",
                    "sysname": "Linux",
                    "version": "#1 SMP Thu Mar 17 17:08:06 UTC 2022",
                },
            },
        },
        "Incorrect magic number": {
            "args": [
                io.BytesIO(HEADER_BYTES.replace(b"\xef", b"\xed")),
            ],
            "raises": ValueError,
        },
        "Truncated": {
            "args": [
                io.BytesIO(HEADER_BYTES[:32]),
            ],
            "raises": ValueError,
        },
    },
    "get_record": {
        "Valid": {
            "args": [
                io.BytesIO(HEADER_BYTES + RECORD_BYTES),
                atop_1_26_structs.Record,
            ],
            "returns": {
                "curtime": 1705174817,
                "flags": 1,
                "interval": 90349,
                "nexit": 0,
                "nlist": 2,
                "npresent": 2,
                "ntrun": 1,
                "ntslpi": 1,
                "ntslpu": 0,
                "nzombie": 0,
                "pcomplen": 271,
                "scomplen": 539,
            },
        },
        "Truncated": {
            "args": [
                io.BytesIO(HEADER_BYTES + RECORD_BYTES[:16]),
                atop_1_26_structs.Record,
            ],
            "returns": {
                "curtime": 1705174817,
                "flags": 1,
                "interval": 0,
                "nexit": 0,
                "nlist": 0,
                "npresent": 0,
                "ntrun": 0,
                "ntslpi": 0,
                "ntslpu": 0,
                "nzombie": 0,
                "pcomplen": 0,
                "scomplen": 0,
            },
        },
    },
    "get_sstat": {
        "Valid": {
            "args": [
                io.BytesIO(HEADER_BYTES + RECORD_BYTES + SSTAT_BYTES),
                atop_1_26_structs.SStat,
            ],
            "returns": {
                "cpu": {
                    "lavg1": 0.009999999776482582,
                    "nrcpu": 6,
                },
                "dsk": {
                    "dsk": [{"name": "vda"}],
                    "ndsk": 1,
                },
                "intf": {
                    "intf": [{"name": "lo"}],
                    "nrintf": 4,
                },
                "mem": {
                    "freemem": 1664452,
                    "physmem": 2037722,
                },
            },
        },
        "Truncated": {
            "args": [
                io.BytesIO(HEADER_BYTES + RECORD_BYTES + SSTAT_BYTES[:16]),
                atop_1_26_structs.SStat,
            ],
            "raises": zlib.error,
        },
    },
}


def _read_log(log: str) -> list[dict]:
    """Convert an Atop log into an easily testable structured result."""
    samples = []
    opener = open if not log.endswith(".gz") else gzip.open
    with opener(log, "rb") as raw_file:
        header = atop_helpers.get_header(raw_file)
        for index, (record, sstat, tstat) in enumerate(atop_helpers.generate_statistics(raw_file, header)):
            converted = {
                "header": atop_helpers.struct_to_dict(header),
                "record": atop_helpers.struct_to_dict(record),
                "sstat": atop_helpers.struct_to_dict(sstat),
                "tstat": [atop_helpers.struct_to_dict(stat) for stat in tstat],
            }
            converted["header"]["semantic_version"] = header.semantic_version
            converted["record"]["record_index"] = index
            samples.append(json.loads(json.dumps(converted, sort_keys=True)))
    return samples


def _sstat_to_simple_dict(sstat: dict | atop_helpers.SStat) -> dict:
    """Convert sstat structs into simplified dictionaries for comparison operations."""
    # Only pull enough values prove bytes were read into structs successfully in the correct order,
    # without overwhelming test output.
    if isinstance(sstat, atop_helpers.SStat):
        sstat = atop_helpers.struct_to_dict(sstat)
    simple_sstat = {
        "cpu": {
            "nrcpu": sstat["cpu"]["nrcpu"],
            "lavg1": sstat["cpu"]["lavg1"],
        },
        "mem": {
            "physmem": sstat["mem"]["physmem"],
            "freemem": sstat["mem"]["freemem"],
        },
        "intf": {
            "nrintf": sstat["intf"]["nrintf"],
            "intf": [{"name": sstat["intf"]["intf"][0]["name"]}],
        },
        "dsk": {
            "ndsk": sstat["dsk"]["ndsk"],
            "dsk": [{"name": sstat["dsk"]["dsk"][0]["name"]}],
        },
    }
    return simple_sstat


def _tstat_to_simple_dict(tstat: dict | atop_helpers.TStat) -> dict:
    """Convert tstat structs into simplified dictionaries for comparison operations."""
    # Only pull enough values prove bytes were read into structs successfully in the correct order,
    # without overwhelming test output.
    if isinstance(tstat, atop_helpers.TStat):
        tstat = atop_helpers.struct_to_dict(tstat)
    simple_tstat = {
        "gen": {
            "cmdline": tstat["gen"]["cmdline"],
            "name": tstat["gen"]["name"],
        },
    }
    return simple_tstat


@pytest.mark.parametrize_test_case("test_case", TEST_CASES["file_header"])
def test_file_header(test_case: dict, function_tester: Callable) -> None:
    """Read a file and ensure the values in the header match expectations."""

    def _get_struct(log: str) -> dict:
        """Read a log and return the header from the first sample (headers are the same across all samples)."""
        return _read_log(log)[0]["header"]

    function_tester(test_case, _get_struct)


@pytest.mark.parametrize_test_case("test_case", TEST_CASES["file_record"])
def test_file_record(test_case: dict, function_tester: Callable) -> None:
    """Read a file and ensure the values in the records match expectations."""

    def _get_struct(log: str) -> dict:
        """Read a log and return the record from the last sample to ensure the entire file processed correctly."""
        return _read_log(log)[-1]["record"]

    function_tester(test_case, _get_struct)


@pytest.mark.parametrize_test_case("test_case", TEST_CASES["file_sstat"])
def test_file_sstat(test_case: dict, function_tester: Callable) -> None:
    """Read a file and ensure the values in the sstats match expectations."""

    def _get_struct(log: str) -> dict:
        """Read a log and return the sstat from the last sample to ensure the entire file processed correctly."""
        sample = _read_log(log)[-1]
        simple_sstat = _sstat_to_simple_dict(sample["sstat"])
        simple_sstat["sample_index"] = sample["record"]["record_index"]
        return simple_sstat

    function_tester(test_case, _get_struct)


@pytest.mark.parametrize_test_case("test_case", TEST_CASES["file_tstat"])
def test_file_tstat(test_case: dict, function_tester: Callable) -> None:
    """Read a file and ensure the values in the tstats match expectations."""

    def _get_struct(log: str) -> dict:
        """Read a log and return the tstat from the last sample to ensure the entire file processed correctly."""
        sample = _read_log(log)[-1]
        tstats = sample["tstat"]
        dict_tstat = _tstat_to_simple_dict(tstats[-1])
        dict_tstat["sample_index"] = sample["record"]["record_index"]
        dict_tstat["tstat_index"] = len(tstats) - 1
        return dict_tstat

    function_tester(test_case, _get_struct)


@pytest.mark.parametrize_test_case("test_case", TEST_CASES["get_header"])
def test_get_header(test_case: dict, function_tester: Callable) -> None:
    """Unit tests for get_header."""

    def _get_header(raw_file: io.BytesIO) -> dict:
        """Convert raw byte sample into dict for tests."""
        return json.loads(
            json.dumps(
                atop_helpers.struct_to_dict(atop_helpers.get_header(raw_file)),
                sort_keys=True,
            )
        )

    function_tester(test_case, _get_header)


@pytest.mark.parametrize_test_case("test_case", TEST_CASES["get_record"])
def test_get_record(test_case: dict, function_tester: Callable) -> None:
    """Unit tests for get_record."""

    def _get_record(raw_file: io.BytesIO, record_cls: atop_helpers.Record) -> dict:
        """Convert raw byte sample into dict for tests."""
        return json.loads(
            json.dumps(
                atop_helpers.struct_to_dict(atop_helpers.get_record(raw_file, record_cls)),
                sort_keys=True,
            )
        )

    # Read the header to ensure the offset is correct prior to reading the record:
    atop_helpers.get_header(test_case["args"][0])
    function_tester(test_case, _get_record)


@pytest.mark.parametrize_test_case("test_case", TEST_CASES["get_sstat"])
def test_get_sstat(test_case: dict, function_tester: Callable) -> None:
    """Unit tests for get_sstat."""

    def _get_sstat(raw_file: io.BytesIO, sstat_cls: atop_helpers.SStat) -> dict:
        """Convert raw byte sample into dict for tests."""
        return json.loads(
            json.dumps(
                _sstat_to_simple_dict(atop_helpers.get_sstat(raw_file, record, sstat_cls)),
                sort_keys=True,
            )
        )

    # Read the header and record to ensure the offset is correct prior to reading the stats.
    mock_file = test_case["args"][0]
    atop_helpers.get_header(mock_file)
    record = atop_helpers.get_record(mock_file, atop_1_26_structs.Record)
    function_tester(test_case, _get_sstat)


@pytest.mark.parametrize_test_case("parseable", atop_reader.PARSEABLES)
def test_parseable_map(parseable: str) -> None:
    """Unit test to ensure every parseable has a corresponding parse_* function."""
    assert (
        getattr(atop_1_26_parsers, f"parse_{parseable}") is not None
    ), f"Failed to find parse function for {parseable}"
