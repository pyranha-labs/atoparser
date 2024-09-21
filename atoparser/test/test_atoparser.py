"""Unit tests for Atop utilities."""

import gzip
import io
import json
import os
import zlib
from types import ModuleType
from typing import Callable

import pytest

import atoparser
from atoparser import reader
from atoparser.parsers import atop_1_26 as atop_1_26_parsers
from atoparser.structs import atop_1_26 as atop_1_26_structs

TEST_FILE_DIR = os.path.join(os.path.dirname(__file__), "files")

# Store raw byes from an Atop file which can be used to simulate calling struct readers while raising errors.
with gzip.open(os.path.join(TEST_FILE_DIR, "atop_1_26.log.gz")) as raw_file:
    HEADER_BYTES = bytearray(atoparser.get_header(raw_file))
    _record = atoparser.get_record(raw_file, atop_1_26_structs.Header.from_buffer(HEADER_BYTES))
    RECORD_BYTES = bytearray(_record)
    SSTAT_BYTES = raw_file.read(_record.scomplen)

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
        "2.4": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_4.log.gz"),
            ],
            "returns": {
                "aversion": 33284,
                "hertz": 100,
                "magic": 4276993775,
                "osrel": 5,
                "ossub": 104,
                "osvers": 10,
                "pagesize": 4096,
                "rawheadlen": 480,
                "rawreclen": 96,
                "semantic_version": "2.4",
                "sstatlen": 716656,
                "supportflags": 53,
                "tstatlen": 840,
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
        "2.5": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_5.log.gz"),
            ],
            "returns": {
                "aversion": 33285,
                "hertz": 100,
                "magic": 4276993775,
                "osrel": 5,
                "ossub": 104,
                "osvers": 10,
                "pagesize": 4096,
                "rawheadlen": 480,
                "rawreclen": 96,
                "semantic_version": "2.5",
                "sstatlen": 716656,
                "supportflags": 53,
                "tstatlen": 840,
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
        "2.6": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_6.log.gz"),
            ],
            "returns": {
                "aversion": 33286,
                "hertz": 100,
                "magic": 4276993775,
                "osrel": 5,
                "ossub": 104,
                "osvers": 10,
                "pagesize": 4096,
                "rawheadlen": 480,
                "rawreclen": 96,
                "semantic_version": "2.6",
                "sstatlen": 716656,
                "supportflags": 53,
                "tstatlen": 840,
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
        "2.7": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_7.log.gz"),
            ],
            "returns": {
                "aversion": 33287,
                "hertz": 100,
                "magic": 4276993775,
                "osrel": 5,
                "ossub": 104,
                "osvers": 10,
                "pagesize": 4096,
                "rawheadlen": 480,
                "rawreclen": 96,
                "semantic_version": "2.7",
                "sstatlen": 954360,
                "supportflags": 53,
                "tstatlen": 840,
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
        "2.7.1": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_7_1.log.gz"),
            ],
            "returns": {
                "aversion": 33287,
                "hertz": 100,
                "magic": 4276993775,
                "osrel": 5,
                "ossub": 104,
                "osvers": 10,
                "pagesize": 4096,
                "rawheadlen": 480,
                "rawreclen": 96,
                "semantic_version": "2.7",
                "sstatlen": 954360,
                "supportflags": 53,
                "tstatlen": 840,
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
        "2.8": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_8.log.gz"),
            ],
            "returns": {
                "aversion": 33288,
                "hertz": 100,
                "magic": 4276993775,
                "osrel": 5,
                "ossub": 104,
                "osvers": 10,
                "pagesize": 4096,
                "pidwidth": 5,
                "rawheadlen": 480,
                "rawreclen": 96,
                "semantic_version": "2.8",
                "sstatlen": 1021960,
                "supportflags": 309,
                "tstatlen": 968,
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
        "2.8.1": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_8_1.log.gz"),
            ],
            "returns": {
                "aversion": 33288,
                "hertz": 100,
                "magic": 4276993775,
                "osrel": 5,
                "ossub": 104,
                "osvers": 10,
                "pagesize": 4096,
                "pidwidth": 5,
                "rawheadlen": 480,
                "rawreclen": 96,
                "semantic_version": "2.8",
                "sstatlen": 1021960,
                "supportflags": 309,
                "tstatlen": 968,
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
        "2.9": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_9.log.gz"),
            ],
            "returns": {
                "aversion": 33289,
                "hertz": 100,
                "magic": 4276993775,
                "osrel": 5,
                "ossub": 104,
                "osvers": 10,
                "pagesize": 4096,
                "pidwidth": 5,
                "rawheadlen": 480,
                "rawreclen": 96,
                "semantic_version": "2.9",
                "sstatlen": 1021960,
                "supportflags": 309,
                "tstatlen": 968,
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
        "2.10": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_10.log.gz"),
            ],
            "returns": {
                "aversion": 33290,
                "hertz": 100,
                "magic": 4276993775,
                "osrel": 5,
                "ossub": 104,
                "osvers": 10,
                "pagesize": 4096,
                "pidwidth": 5,
                "rawheadlen": 480,
                "rawreclen": 96,
                "semantic_version": "2.10",
                "sstatlen": 1030216,
                "supportflags": 309,
                "tstatlen": 992,
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
        "2.11": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_11.log.gz"),
            ],
            "returns": {
                "aversion": 33291,
                "cstatlen": 432,
                "hertz": 100,
                "magic": 4276993775,
                "osrel": 6,
                "ossub": 11,
                "osvers": 5,
                "pagesize": 4096,
                "pidwidth": 5,
                "rawheadlen": 480,
                "rawreclen": 96,
                "semantic_version": "2.11",
                "sstatlen": 1064016,
                "supportflags": 309,
                "tstatlen": 968,
                "utsname": {
                    "domain": "(none)",
                    "machine": "x86_64",
                    "nodename": "fires-of-mount-doom1",
                    "release": "6.5.11-linuxkit",
                    "sysname": "Linux",
                    "version": "#1 SMP PREEMPT Wed Dec  6 17:08:31 UTC 2023",
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
        "2.4": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_4.log.gz"),
            ],
            "returns": {
                "curtime": 1705248745,
                "flags": 32,
                "interval": 1,
                "nactproc": 1,
                "ndeviat": 3,
                "nexit": 0,
                "noverflow": 0,
                "ntask": 3,
                "pcomplen": 247,
                "record_index": 4,
                "scomplen": 1040,
                "totproc": 3,
                "totrun": 1,
                "totslpi": 2,
                "totslpu": 0,
                "totzomb": 0,
            },
        },
        "2.5": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_5.log.gz"),
            ],
            "returns": {
                "curtime": 1705252792,
                "flags": 32,
                "interval": 1,
                "nactproc": 1,
                "ndeviat": 3,
                "nexit": 0,
                "noverflow": 0,
                "ntask": 3,
                "pcomplen": 249,
                "record_index": 4,
                "scomplen": 1039,
                "totproc": 3,
                "totrun": 1,
                "totslpi": 2,
                "totslpu": 0,
                "totzomb": 0,
            },
        },
        "2.6": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_6.log.gz"),
            ],
            "returns": {
                "curtime": 1705252822,
                "flags": 32,
                "interval": 1,
                "nactproc": 1,
                "ndeviat": 3,
                "nexit": 0,
                "noverflow": 0,
                "ntask": 3,
                "pcomplen": 255,
                "record_index": 4,
                "scomplen": 1020,
                "totproc": 3,
                "totrun": 1,
                "totslpi": 2,
                "totslpu": 0,
                "totzomb": 0,
            },
        },
        "2.7": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_7.log.gz"),
            ],
            "returns": {
                "curtime": 1705252857,
                "flags": 32,
                "interval": 1,
                "nactproc": 1,
                "ndeviat": 3,
                "nexit": 0,
                "noverflow": 0,
                "ntask": 3,
                "pcomplen": 254,
                "record_index": 4,
                "scomplen": 1202,
                "totproc": 3,
                "totrun": 1,
                "totslpi": 2,
                "totslpu": 0,
                "totzomb": 0,
            },
        },
        "2.7.1": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_7_1.log.gz"),
            ],
            "returns": {
                "curtime": 1705252898,
                "flags": 32,
                "interval": 1,
                "nactproc": 1,
                "ndeviat": 3,
                "nexit": 0,
                "noverflow": 0,
                "ntask": 3,
                "pcomplen": 248,
                "record_index": 4,
                "scomplen": 1203,
                "totproc": 3,
                "totrun": 1,
                "totslpi": 2,
                "totslpu": 0,
                "totzomb": 0,
            },
        },
        "2.8": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_8.log.gz"),
            ],
            "returns": {
                "ccomplen": 0,
                "coriglen": 0,
                "curtime": 1705252932,
                "flags": 288,
                "icomplen": 0,
                "interval": 1,
                "nactproc": 1,
                "ncgpids": 0,
                "ncgroups": 0,
                "ndeviat": 3,
                "nexit": 0,
                "noverflow": 0,
                "ntask": 3,
                "pcomplen": 270,
                "record_index": 4,
                "scomplen": 1289,
                "totidle": 0,
                "totproc": 3,
                "totrun": 1,
                "totslpi": 2,
                "totslpu": 0,
                "totzomb": 0,
            },
        },
        "2.8.1": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_8_1.log.gz"),
            ],
            "returns": {
                "ccomplen": 0,
                "coriglen": 0,
                "curtime": 1705252967,
                "flags": 288,
                "icomplen": 0,
                "interval": 1,
                "nactproc": 1,
                "ncgpids": 0,
                "ncgroups": 0,
                "ndeviat": 3,
                "nexit": 0,
                "noverflow": 0,
                "ntask": 3,
                "pcomplen": 272,
                "record_index": 4,
                "scomplen": 1272,
                "totidle": 0,
                "totproc": 3,
                "totrun": 1,
                "totslpi": 2,
                "totslpu": 0,
                "totzomb": 0,
            },
        },
        "2.9": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_9.log.gz"),
            ],
            "returns": {
                "ccomplen": 0,
                "coriglen": 0,
                "curtime": 1705253010,
                "flags": 288,
                "icomplen": 0,
                "interval": 1,
                "nactproc": 1,
                "ncgpids": 0,
                "ncgroups": 0,
                "ndeviat": 3,
                "nexit": 0,
                "noverflow": 0,
                "ntask": 3,
                "pcomplen": 278,
                "record_index": 4,
                "scomplen": 1268,
                "totidle": 0,
                "totproc": 3,
                "totrun": 1,
                "totslpi": 2,
                "totslpu": 0,
                "totzomb": 0,
            },
        },
        "2.10": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_10.log.gz"),
            ],
            "returns": {
                "curtime": 1705253060,
                "flags": 288,
                "interval": 1,
                "nactproc": 1,
                "ndeviat": 3,
                "nexit": 0,
                "noverflow": 0,
                "ntask": 3,
                "pcomplen": 272,
                "record_index": 4,
                "scomplen": 1299,
                "totidle": 0,
                "totproc": 3,
                "totrun": 1,
                "totslpi": 2,
                "totslpu": 0,
                "totzomb": 0,
            },
        },
        "2.11": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_11.log.gz"),
            ],
            "returns": {
                "ccomplen": 63,
                "coriglen": 440,
                "curtime": 1726329658,
                "flags": 288,
                "icomplen": 16,
                "interval": 1,
                "nactproc": 1,
                "ncgpids": 2,
                "ncgroups": 1,
                "ndeviat": 6,
                "nexit": 0,
                "noverflow": 0,
                "ntask": 6,
                "pcomplen": 305,
                "record_index": 4,
                "scomplen": 1421,
                "totidle": 0,
                "totproc": 2,
                "totrun": 1,
                "totslpi": 3,
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
        "2.4": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_4.log.gz"),
            ],
            "returns": {
                "cpu": {
                    "nrcpu": 6,
                    "lavg1": 0.3400000035762787,
                },
                "mem": {
                    "physmem": 2037722,
                    "freemem": 1526454,
                },
                "intf": {
                    "nrintf": 4,
                    "intf": [{"name": "lo"}],
                },
                "dsk": {
                    "ndsk": 17,
                    "dsk": [{"name": "nbd0"}],
                },
                "sample_index": 4,
            },
        },
        "2.5": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_5.log.gz"),
            ],
            "returns": {
                "cpu": {
                    "nrcpu": 6,
                    "lavg1": 0.15000000596046448,
                },
                "mem": {
                    "physmem": 2037722,
                    "freemem": 1526707,
                },
                "intf": {
                    "nrintf": 4,
                    "intf": [{"name": "lo"}],
                },
                "dsk": {
                    "ndsk": 17,
                    "dsk": [{"name": "nbd0"}],
                },
                "sample_index": 4,
            },
        },
        "2.6": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_6.log.gz"),
            ],
            "returns": {
                "cpu": {
                    "nrcpu": 6,
                    "lavg1": 0.25,
                },
                "mem": {
                    "physmem": 2037722,
                    "freemem": 1526155,
                },
                "intf": {
                    "nrintf": 4,
                    "intf": [{"name": "lo"}],
                },
                "dsk": {
                    "ndsk": 17,
                    "dsk": [{"name": "nbd0"}],
                },
                "sample_index": 4,
            },
        },
        "2.7": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_7.log.gz"),
            ],
            "returns": {
                "cpu": {
                    "nrcpu": 6,
                    "lavg1": 0.2199999988079071,
                },
                "mem": {
                    "physmem": 2037722,
                    "freemem": 1525662,
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
        "2.7.1": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_7_1.log.gz"),
            ],
            "returns": {
                "cpu": {
                    "nrcpu": 6,
                    "lavg1": 0.23999999463558197,
                },
                "mem": {
                    "physmem": 2037722,
                    "freemem": 1525086,
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
        "2.8": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_8.log.gz"),
            ],
            "returns": {
                "cpu": {
                    "nrcpu": 6,
                    "lavg1": 0.4000000059604645,
                },
                "mem": {
                    "physmem": 2037722,
                    "freemem": 1524637,
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
        "2.8.1": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_8_1.log.gz"),
            ],
            "returns": {
                "cpu": {
                    "nrcpu": 6,
                    "lavg1": 0.46000000834465027,
                },
                "mem": {
                    "physmem": 2037722,
                    "freemem": 1524411,
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
        "2.9": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_9.log.gz"),
            ],
            "returns": {
                "cpu": {
                    "nrcpu": 6,
                    "lavg1": 0.36000001430511475,
                },
                "mem": {
                    "physmem": 2037722,
                    "freemem": 1524598,
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
        "2.10": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_10.log.gz"),
            ],
            "returns": {
                "cpu": {
                    "nrcpu": 6,
                    "lavg1": 0.30000001192092896,
                },
                "mem": {
                    "physmem": 2037722,
                    "freemem": 1523947,
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
        "2.11": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_11.log.gz"),
            ],
            "returns": {
                "cpu": {
                    "nrcpu": 12,
                    "lavg1": 0.47999998927116394,
                },
                "mem": {
                    "physmem": 2008626,
                    "freemem": 365583,
                },
                "intf": {
                    "nrintf": 4,
                    "intf": [{"name": "lo"}],
                },
                "dsk": {
                    "ndsk": 3,
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
        "2.4": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_4.log.gz"),
            ],
            "returns": {
                "gen": {
                    "cmdline": "/mnt/pyatop/atop 1 5 -w /mnt/pyatop/atop_v2.4.0.log",
                    "name": "atop",
                },
                "sample_index": 4,
                "tstat_index": 2,
            },
        },
        "2.5": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_5.log.gz"),
            ],
            "returns": {
                "gen": {
                    "cmdline": "/mnt/pyatop/atop 1 5 -w /mnt/pyatop/atop_v2.5.0.log",
                    "name": "atop",
                },
                "sample_index": 4,
                "tstat_index": 2,
            },
        },
        "2.6": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_6.log.gz"),
            ],
            "returns": {
                "gen": {
                    "cmdline": "/mnt/pyatop/atop 1 5 -w /mnt/pyatop/atop_v2.6.0.log",
                    "name": "atop",
                },
                "sample_index": 4,
                "tstat_index": 2,
            },
        },
        "2.7": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_7.log.gz"),
            ],
            "returns": {
                "gen": {
                    "cmdline": "/mnt/pyatop/atop 1 5 -w /mnt/pyatop/atop_v2.7.0.log",
                    "name": "atop",
                },
                "sample_index": 4,
                "tstat_index": 2,
            },
        },
        "2.7.1": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_7_1.log.gz"),
            ],
            "returns": {
                "gen": {
                    "cmdline": "/mnt/pyatop/atop 1 5 -w /mnt/pyatop/atop_v2.7.1.log",
                    "name": "atop",
                },
                "sample_index": 4,
                "tstat_index": 2,
            },
        },
        "2.8": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_8.log.gz"),
            ],
            "returns": {
                "gen": {
                    "cmdline": "/mnt/pyatop/atop 1 5 -w /mnt/pyatop/atop_v2.8.0.log",
                    "name": "atop",
                },
                "sample_index": 4,
                "tstat_index": 2,
            },
        },
        "2.8.1": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_8_1.log.gz"),
            ],
            "returns": {
                "gen": {
                    "cmdline": "/mnt/pyatop/atop 1 5 -w /mnt/pyatop/atop_v2.8.1.log",
                    "name": "atop",
                },
                "sample_index": 4,
                "tstat_index": 2,
            },
        },
        "2.9": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_9.log.gz"),
            ],
            "returns": {
                "gen": {
                    "cmdline": "/mnt/pyatop/atop 1 5 -w /mnt/pyatop/atop_v2.9.0.log",
                    "name": "atop",
                },
                "sample_index": 4,
                "tstat_index": 2,
            },
        },
        "2.10": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_10.log.gz"),
            ],
            "returns": {
                "gen": {
                    "cmdline": "/mnt/pyatop/atop 1 5 -w /mnt/pyatop/atop_v2.10.0.log",
                    "name": "atop",
                },
                "sample_index": 4,
                "tstat_index": 2,
            },
        },
        "2.11": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_11.log.gz"),
            ],
            "returns": {
                "gen": {
                    "cmdline": "",
                    "name": "atop",
                },
                "sample_index": 4,
                "tstat_index": 5,
            },
        },
    },
    "file_cstat": {
        "2.10": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_10.log.gz"),
            ],
            "returns": None,
        },
        "2.11": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_2_11.log.gz"),
            ],
            "returns": {
                "cstat": {
                    "gen": {
                        "structlen": 440,
                        "nprocs": 2,
                    }
                },
                "proclist": [1, 2979],
                "sample_index": 4,
                "cstat_index": 0,
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
                atop_1_26_structs.Header.from_buffer(HEADER_BYTES),
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
                atop_1_26_structs.Header.from_buffer(HEADER_BYTES),
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
                atop_1_26_structs.Header.from_buffer(HEADER_BYTES),
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
                atop_1_26_structs.Header.from_buffer(HEADER_BYTES),
            ],
            "raises": zlib.error,
        },
    },
    "parseable": {
        "1.26": {
            "args": [
                os.path.join(TEST_FILE_DIR, "atop_1_26.log.gz"),
                [
                    "cpu",
                    "CPL",
                    "CPU",
                    "DSK",
                    "LVM",
                    "MDD",
                    "MEM",
                    "NETL",
                    "NETU",
                    "PAG",
                    "PRC",
                    "PRG",
                    "PRM",
                    "PRN",
                    "SWP",
                ],
                atop_1_26_parsers,
            ],
            "returns": {
                "sample_index": 4,
                "CPL": {
                    "context_switches": 375,
                    "interrupts": 231,
                    "interval": 1,
                    "load_1": 0.0,
                    "load_15": 0.0,
                    "load_5": 0.0,
                    "procs": 6,
                    "timestamp": 1705174821,
                },
                "CPU": {
                    "guest": 0,
                    "idle": 600,
                    "interval": 1,
                    "irq": 0,
                    "niced": 0,
                    "procs": 6,
                    "softirq": 0,
                    "steal": 0,
                    "system": 1,
                    "ticks": 100,
                    "timestamp": 1705174821,
                    "user": 0,
                    "wait": 0,
                },
                "DSK": {
                    "interval": 1,
                    "io_ms": 0,
                    "name": "vda",
                    "read_sectors": 0,
                    "reads": 0,
                    "timestamp": 1705174821,
                    "write_sectors": 0,
                    "writes": 0,
                },
                "MEM": {
                    "buffer_cache": 73771,
                    "dirty_pages": 13,
                    "free_mem": 1664263,
                    "interval": 1,
                    "page_cache": 178807,
                    "page_size": 4096,
                    "phys_mem": 2037722,
                    "slab": 60201,
                    "timestamp": 1705174821,
                },
                "NETL": {
                    "byte_received": 0,
                    "bytes_transmitted": 0,
                    "duplex": 1,
                    "interval": 1,
                    "name": "eth0",
                    "pkt_received": 0,
                    "pkt_transmitted": 0,
                    "speed": 0,
                    "timestamp": 1705174821,
                },
                "NETU": {
                    "interval": 1,
                    "ip_pkt_delivered": 0,
                    "ip_pkt_forwarded": 0,
                    "ip_pkt_received": 0,
                    "ip_pkt_transmitted": 0,
                    "name": "upper",
                    "tcp_pkt_received": 0,
                    "tcp_pkt_transmitted": 0,
                    "timestamp": 1705174821,
                    "udp_pkt_received": 0,
                    "udp_pkt_transmitted": 0,
                },
                "PAG": {
                    "alloc_stalls": 0,
                    "interval": 1,
                    "page_scans": 0,
                    "page_size": 4096,
                    "swapins": 0,
                    "swapouts": 0,
                    "timestamp": 1705174821,
                },
                "PRC": {
                    "cpu": 3,
                    "interval": 1,
                    "name": "atop",
                    "nice": 0,
                    "pid": 294,
                    "policy": 0,
                    "priority": 120,
                    "priority_realtime": 0,
                    "sleep": 0,
                    "state": "R",
                    "system_consumption": 0,
                    "ticks": 100,
                    "timestamp": 1705174821,
                    "user_consumption": 0,
                },
                "PRG": {
                    "cmd": "atop 1 5 -w /mnt/pyatop/atop_1_26.log",
                    "dead_threads": 0,
                    "effective_gid": 0,
                    "effective_uid": 0,
                    "elapsed_time": 0,
                    "exit_code": 0,
                    "filesystem_gid": 0,
                    "filesystem_uid": 0,
                    "interval": 1,
                    "name": "atop",
                    "pid": 294,
                    "ppid": 1,
                    "real_gid": 0,
                    "real_uid": 0,
                    "running_threads": 1,
                    "saved_gid": 0,
                    "saved_uid": 0,
                    "sleeping_threads": 0,
                    "start_time": 1705174814,
                    "state": "R",
                    "tgid": 294,
                    "threads": 1,
                    "timestamp": 1705174821,
                },
                "PRM": {
                    "interval": 1,
                    "major_faults": 0,
                    "minor_faults": 40,
                    "name": "atop",
                    "page": 4096,
                    "pid": 294,
                    "rgrowth": 0,
                    "rsize": 2924544,
                    "ssize": 151552,
                    "state": "R",
                    "timestamp": 1705174821,
                    "vgrowth": 0,
                    "vsize": 17149952,
                },
                "PRN": {
                    "interval": 1,
                    "kernel_patch": "n",
                    "name": "atop",
                    "pid": 294,
                    "raw_received": 0,
                    "raw_transmitted": 0,
                    "state": "R",
                    "tcp_received": 0,
                    "tcp_received_size": 0,
                    "tcp_transmitted": 0,
                    "tcp_transmitted_size": 0,
                    "timestamp": 1705174821,
                    "udp_received": 0,
                    "udp_received_size": 0,
                    "udp_transmitted": 0,
                    "udp_transmitted_size": 0,
                },
                "SWP": {
                    "committed_limit": 1281004,
                    "committed_space": 756909,
                    "free_swap": 262143,
                    "interval": 1,
                    "page_size": 4096,
                    "swap": 262143,
                    "timestamp": 1705174821,
                },
                "cpu": {
                    "guest": 0,
                    "idle": 99,
                    "interval": 1,
                    "irq": 0,
                    "niced": 0,
                    "proc": 5,
                    "softirq": 0,
                    "steal": 0,
                    "system": 0,
                    "ticks": 100,
                    "timestamp": 1705174821,
                    "user": 0,
                    "wait": 0,
                },
            },
        }
    },
}


def _read_log(log: str) -> list[dict]:
    """Convert an Atop log into an easily testable structured result."""
    samples = []
    opener = open if not log.endswith(".gz") else gzip.open
    with opener(log, "rb") as raw_file:
        header = atoparser.get_header(raw_file)
        for index, (record, sstat, tstats, cgroups) in enumerate(atoparser.generate_statistics(raw_file, header)):
            converted = {
                "header": atoparser.struct_to_dict(header),
                "record": atoparser.struct_to_dict(record),
                "sstat": atoparser.struct_to_dict(sstat),
                "tstat": [atoparser.struct_to_dict(stat) for stat in tstats],
                "cgroup": [atoparser.struct_to_dict(stat) for stat in cgroups],
            }
            converted["header"]["semantic_version"] = header.semantic_version
            converted["record"]["record_index"] = index
            samples.append(json.loads(json.dumps(converted, sort_keys=True)))
    return samples


def _read_parseables(log: str, parseables: list[str], module: ModuleType) -> list[dict]:
    """Convert an Atop log's "parseables" into an easily testable structured result."""
    samples = []
    opener = open if not log.endswith(".gz") else gzip.open
    with opener(log, "rb") as raw_file:
        header = atoparser.get_header(raw_file)
        parsers = {parseable: getattr(module, f"parse_{parseable}") for parseable in parseables}
        for record, sstat, tstat, cstat in atoparser.generate_statistics(raw_file, header, raise_on_truncation=False):
            sample = {}
            for parseable in parseables:
                for result in parsers[parseable](header, record, sstat, tstat):
                    sample.setdefault(parseable, []).append(result)
            samples.append(sample)
    return samples


def _sstat_to_simple_dict(sstat: dict | atoparser.SStat) -> dict:
    """Convert sstat structs into simplified dictionaries for comparison operations."""
    # Only pull enough values prove bytes were read into structs successfully in the correct order,
    # without overwhelming test output.
    if isinstance(sstat, atoparser.SStat):
        sstat = atoparser.struct_to_dict(sstat)
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


def _tstat_to_simple_dict(tstat: dict | atoparser.TStat) -> dict:
    """Convert tstat structs into simplified dictionaries for comparison operations."""
    # Only pull enough values prove bytes were read into structs successfully in the correct order,
    # without overwhelming test output.
    if isinstance(tstat, atoparser.TStat):
        tstat = atoparser.struct_to_dict(tstat)
    simple_tstat = {
        "gen": {
            "cmdline": tstat["gen"]["cmdline"],
            "name": tstat["gen"]["name"],
        },
    }
    return simple_tstat


def _cgchain_to_simple_dict(cgchainer: dict | atoparser.CGChainer) -> dict:
    """Convert cgchain structs into simplified dictionaries for comparison operations."""
    # Only pull enough values prove bytes were read into structs successfully in the correct order,
    # without overwhelming test output.
    if isinstance(cgchainer, atoparser.CGChainer):
        cgchainer = atoparser.struct_to_dict(cgchainer)
    simple_cgchainer = {
        "cstat": {
            "gen": {
                "structlen": cgchainer["cstat"]["gen"]["structlen"],
                "nprocs": cgchainer["cstat"]["gen"]["nprocs"],
            }
        },
        "proclist": cgchainer["proclist"],
    }
    return simple_cgchainer


@pytest.mark.parametrize_test_case("test_case", TEST_CASES["file_header"])
def test_file_header(test_case: dict, function_tester: Callable) -> None:
    """Read a file and ensure the values in the header match expectations."""

    def _get_struct(log: str) -> dict:
        """Read a log and return the header."""
        opener = open if not log.endswith(".gz") else gzip.open
        with opener(log, "rb") as raw_file:
            raw_header = atoparser.get_header(raw_file)
            header = atoparser.struct_to_dict(raw_header)
            header["semantic_version"] = raw_header.semantic_version
            return json.loads(json.dumps(header, sort_keys=True))

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


@pytest.mark.parametrize_test_case("test_case", TEST_CASES["file_cstat"])
def test_file_cstat(test_case: dict, function_tester: Callable) -> None:
    """Read a file and ensure the values in the cstats match expectations."""

    def _get_struct(log: str) -> dict | None:
        """Read a log and return the cstat from the last sample to ensure the entire file processed correctly."""
        sample = _read_log(log)[-1]
        cstats = sample["cgroup"]
        if not cstats:
            return None
        dict_cstat = _cgchain_to_simple_dict(cstats[-1])
        dict_cstat["sample_index"] = sample["record"]["record_index"]
        dict_cstat["cstat_index"] = len(cstats) - 1
        return dict_cstat

    function_tester(test_case, _get_struct)


@pytest.mark.parametrize_test_case("test_case", TEST_CASES["get_header"])
def test_get_header(test_case: dict, function_tester: Callable) -> None:
    """Unit tests for get_header."""

    def _get_header(raw_file: io.BytesIO) -> dict:
        """Convert raw byte sample into dict for tests."""
        return json.loads(
            json.dumps(
                atoparser.struct_to_dict(atoparser.get_header(raw_file)),
                sort_keys=True,
            )
        )

    function_tester(test_case, _get_header)


@pytest.mark.parametrize_test_case("test_case", TEST_CASES["get_record"])
def test_get_record(test_case: dict, function_tester: Callable) -> None:
    """Unit tests for get_record."""

    def _get_record(raw_file: io.BytesIO, record_cls: atoparser.Record) -> dict:
        """Convert raw byte sample into dict for tests."""
        return json.loads(
            json.dumps(
                atoparser.struct_to_dict(atoparser.get_record(raw_file, record_cls)),
                sort_keys=True,
            )
        )

    # Read the header to ensure the offset is correct prior to reading the record:
    atoparser.get_header(test_case["args"][0])
    function_tester(test_case, _get_record)


@pytest.mark.parametrize_test_case("test_case", TEST_CASES["get_sstat"])
def test_get_sstat(test_case: dict, function_tester: Callable) -> None:
    """Unit tests for get_sstat."""

    def _get_sstat(raw_file: io.BytesIO, header: atoparser.Header) -> dict:
        """Convert raw byte sample into dict for tests."""
        return json.loads(
            json.dumps(
                _sstat_to_simple_dict(atoparser.get_sstat(raw_file, header, record)),
                sort_keys=True,
            )
        )

    # Read the header and record to ensure the offset is correct prior to reading the stats.
    mock_file = test_case["args"][0]
    header = atoparser.get_header(mock_file)
    record = atoparser.get_record(mock_file, header)
    function_tester(test_case, _get_sstat)


@pytest.mark.parametrize_test_case("parseable", reader.PARSEABLES)
def test_parseable_map(parseable: str) -> None:
    """Unit test to ensure every parseable has a corresponding parse_* function."""
    assert (
        getattr(atop_1_26_parsers, f"parse_{parseable}") is not None
    ), f"Failed to find parse function for {parseable}"


@pytest.mark.parametrize_test_case("test_case", TEST_CASES["parseable"])
def test_parseable(test_case: dict, function_tester: Callable) -> None:
    """Read a file and ensure the values in the "parseable" output match expectations."""

    def _get_parseables(log: str, parseables: list[str], module: ModuleType) -> dict:
        """Read a log and return the "parseable" set from the last sample to ensure the file processed correctly."""
        results = _read_parseables(log, parseables, module)
        final_result = results[-1]
        last_values = {parseable: values[-1] for parseable, values in final_result.items()}
        last_values["sample_index"] = len(results) - 1
        return json.loads(json.dumps(last_values, sort_keys=True))

    function_tester(test_case, _get_parseables)
