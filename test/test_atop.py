"""Unit tests for ATOP utilities."""

import io
import zlib

import pytest

from pyatop import atop_helpers
from pyatop import atop_reader
from pyatop.parsers import atop_126 as atop_126_parsers
from pyatop.structs import atop_126 as atop_126_structs

# Raw byes from an ATOP file which can be used to simulate reading the file.
HEADER_BYTES = b'\xef\xbe\xed\xfe\x1a\x81\x00\x00\x00\x00\xe0\x01P\x00d\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x000Y\x01\x00h\x02\x00\x00Linux\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00fires-of-mount-doom1\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x003.16.0-44-mordor1\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00#59~14.04.1 SMP PREEMPT Fri Dec 28 20:04:09 UTC 2018\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00x86_64\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00theshire.co\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x05\x00\x00\x00\x03\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
RECORD_BYTES = b'_j\xc2\\\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xbc\x03\x00\x00\x987\x00\x00<\x00\x00\x009\x03\x00\x00\xea\x00\x00\x00O\x02\x00\x00\x04\x00\x00\x00\x05\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
SSTAT_BYTES = b'x\x9c\xed\xdaMh\x1cU\x1c\x00\xf0M\x9b\xdaZ\x94\x10\xad_\xd0\x94**\x15TL6*\x81\x1a\x14\xc1J\xf5P\x10\xb5\x17\t\x9bl\xdaD\xbb\xf9\xdaF\x11AzW\xf0\xe8\xa1\x16r\xd2[\x8b D\x10Ao\x8a^\x14\xbd\xe8A\xf1 \x1e\xda\xa37\xb1\xc2\xbe\xb7q\xf3\x9a53\xebf]\x9c\xdf\xef\xf2g\xdf\xbe\xf7\xfe\xf3ff\xe7\xcd\xcc\xdb}\xa5\xe0\xf2}\x83\x8d\xf8\xec\xe0\xc1F\xbc\xb0+\x94?\xb6\xff\xc5\xc9\x8b\xc7*\x93\xa5\xd2\xb9\xc9R\x0ek\xa1\xbb\xd2\xbd{7\x97\x9f\xbf\x18\xe2\x83I\xfd\xeb\xf3t\xbe\x85\xa31~\x98\x94\xdfxk\x88\xc9f\x94\x06\xdb\xf4S\x89\x1b\xb2\xf4\xcd\x8f!\xde\xb6\xf9\xfb\x81\x18\x9f\x8c\xf1\xfb\xa4\xfdD\xcc\x97\x8eg\xa0\xb4\xb5\xed\xf2\xc5\xc3P:\x1e\xe3OI\xfb\xbbc\xbe\xddI\xf9\xae\xd2\xd6\xb6\xcb\xd7\xec\xe7L\x8c\x97\x92\xf6\xe5\x98o_R\xde\xe9\xf8\x9a\xc7\xe1\xad\x18\xaf&\xed\xbf\xba%\xc4\xf4\xf8\xb5\xb3]\xbe=1>\x13\xe3\xabI\xfb\x0f\xda\xec\xcfN\xf3]\x17\xe3r\xdcA\x9f\';\xea\x91\x03[\xe7\xebt\x7f6\xf7\xd3=\xb1\x83\x1f\x92\xf6/ty\x7f\x02\x00\x00\x00\x00\x00t\xdb\xc4\xd0\xa1F\\?\x19\x16<\xde\x0f\xcb\x14\xa5?\x1f\r+*O_\x1aj\xc4\xac\xeb9\xa9\xf7\xf6\x86\xf6/\x9d\xce\xb6B\xd9\\\xb7y<\xc67o\xce\x97o8\xd6\x7f%g\xbb\xed\xdc\x1e7\xecDR\xbe\x96\xb1\xfd\xd1$f\xcd\xb7Sy\x96\xdb\x94?\x1cc-c\xbev\xd2\xf6\x07\xffe\x7f\xa9\xe7\x92\xcf\'\xbb\xdc\x7f;\xcd\xdf\xc1\xf3I\xf9\x9e\xb4bF\xcdu\xe6N\x7f_M\xcd\xd3\xe5\x8b\x18?\xfb.\x94\\\x8d~\x89\xe5k1\xa6\xe7\xf1\x9d1^\x18\x0e\xf1\xb7\xe1\xad\xeb5\xd7\x9b\x0f\xc5\xb8\\?\xb5465\xba\xf1\xfd\xc7q@\xe9\xfay\xbb\xf5\xf4\xbc\x8e\x0ct\xb7\xbf\xd4\xfe\x18\xdb\xad\x1f\xa7\xc2\xf8\xc76>\x17s\xfc\xe5\x1d\xda\x9ak\xf5\xe7\xf8\xc7whk\xae\xd5o\xe3_\xadO?\xb04;\xbb\xf2\xd0\x0emO\xbf\x9b\x9e\xa9\x15u\xe8\r\xd5\xd5Z\xed\xf5\x02\xef\x81\xe9\xc5\x85j\xeb\xf0?9q\xb8\x11\xd7\x0f\xe4\xeb\xe7\x9d\x8c\xf5\xde\xb8\x12\xee\x14\xbe\xce\xfa\x07\xa4\x0e\xe5\xb9\xfe\x8d\x17\xfc\xfa?\xder\xff\xb3\xd3\xfas\xfcc\xdbW\xec\x92\xfe\x1c\x7fq\xe7\xffJ\xb56\xbf\xd0r\x01|w=\xc4O\x93\x0e\xba\xf5\x0by\xf9\xae\x10\xbb\xfd<\x99\xca:\xfe\xf9\x95\xcd#;|$\xc4\x89\x9c\xf9\xb2\x1e\xcf\xa9\x9bB\xbc#g\xffy\xe59\xffG\x0b|\xfe\x87\xf1\xff}\x0e|[\xc0\xe7\xbf\xd1\x82\xcf\xff\xa3-\xf3_\xd1\x8e\xff\xcc\\\xa5^\x9f\xafo\xcc\x00\xbf\x9e\x1bi\xc4\xf2P\xbe\xbc7d\xac\xf7\xd4\xf9p\xff;\xd2\'\xf7\xbf\xd3\x85}\xf2\r\xea\xaf\xcd\x9f\x9d\x99\x9b\x9aYZ\xfd\xaf\xb7\xa4;:\xf9\xfd\x97\x0b~\xff_.\xf8\xfc_.\xf8\xf3O\xb9\xc0\xf3\x7f\xf3\xfdg\xef\xae\x00\xfd\xe5\xcc\xe2\xe6\xcf_\x1e\x0f{p$\xeb\x84\x9e\xd3N\xf7\x9fWee\xa5\xd2\xfa\xfe\xf3\x8f\xb80\xf8{\xce~\x8ee\xacw\xe5\xfe\x10\xdf\xce\xd9\x7f^Y\xcf\xff\xda\xe2\xea\xc2\xd9\xff\xe1-P\xf6\xe7\xff\xcd\x83/\xda\xfb_\x8a-\xfdWO\xbdZ\xf9\xc7\xfa\xcd\xff\xa5\xfc\x1cO\xb0\x8f\x9a_\xc4\x17ZO\xc4\xf2\xdd\x19\'\xf8zu:[\xc5.\xa9Wgz\x9c\xaf\xda\xe3|\xb3=\xcew\xaa\xc7\xf9N\xf78\xdf\\\x8f\xf3\xcd\xf74\x1f\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xb4\xfa\x0b\x93\xb7\xb9\xb2x\x9c\xed\x9d\t\x9c\x1cU\xb5\xb8\x8b$@\x08"\x91\xb0\x84\x10\xb4\x81\x90\x00I\xcf\x92\x99d&\x81\x00!\x1bHHB\x12 \t\x84\x99\x9e\xee\x9a\x99JzKu\xf7d\x82\x0b\xc8\x0e.\x08aS\x90MD\\\xf0/\x82\x8a\x02\x12e\x15A\xd9\x17\x89O|\xeasC\x1f.\xf8P\xd1\xfc\xef\xed\xaaJj*\xd3\xddU\xcd\xb9s\xef=s>\x7fCejz\xc6\xd3\x93/\xe7.\xe7\xde[\xbb\x18\xe1\xd8\x85}XY\xab\xe8\xbf\xb7\xc2\xf7\xe7g\xbf\xd1v\x96\xffk\x8d\x85.+\xdb\x18\xfc\x0e\xf9\xec\x12\xe25\xfd\xbe?\x8f\x14\x15H\x9d\xbc\xe5^\'^\xed\\G\xbdOZ(\x91\x18\x11\xf2u\xfc\xefg}\xb1\xd76\x13\xa9\x94w\xaf\x9ag\xaa\x12\xd5\xb3]E\x052\xcc\xe0\xff^\xc3\xb8V\xf6\xac\x90\xeb.Z\xf6\x86TcS\xf9\x1e&\xcf\xfc\xbf\x83\xfe\n\xaf!\xea\x87\xff{\r\xed\xd9\xc6\x9c\xbd\xde\xb4\x1b\x9bf7\x9d\xc8\xefa\xf2\xcc\xe3\x8dm\xdb\xb6\xa5j\xbc\x86\x88\xce\xeeFx\xcf\xecd\xa9#o\x9bf&\xeft\xba\x96\xfb\xbe\xae\x8bg\x1eA\xdf\xfc\xfd0\x7f>\xdb}\x08b\x19\x0e\x8c6"y\x96\xcb\xbbm&\x07S>\xa3vS,{\x18Q=k\xde~o8x\x16f\xdc@\xd4f\x8c\x11\xd5\xb3\xe9\xdb\xefa\xf2\xacR\xbbI\xe3M\x18\xf64\xa2z\xd6\xb2\xfd\x1e&\xcf*\xe53\xd5\xe6\xcft\xe5=FT\xcfZ\xb7\xdf\x1b\x0e\x9e\x85\x9d_$\xaa\xb3\x97\x11\xd5\xb3\x19\xdb\xefa\xf2\xcc\x7f\x9f\xfag\xf0\xbc\xd7\x88\xea\xd9\xcc\xed\xf70yV)\x9f\xed&0\x96\xe1\xc4\xdeFT\xcf\xda\xb6\xdf\xc3\xe4Y\xa5|F\xc00\xd6\x886O[H\xf6\x9a\xde|9&\xcf\xfcP\xbb\t\x0f/\xf7G\xc9g\x05\xa4\xf3\xb4~(\x9f'

TEST_CASES = {
    'get_header': {
        'Valid': {
            'args': [
                io.BytesIO(HEADER_BYTES),
            ],
            'expected_result': {
                'magic': 4276993775,
                'aversion': 33050,
                'future1': 0,
                'future2': 0,
                'rawheadlen': 480,
                'rawreclen': 80,
                'hertz': 100,
                'sstatlen': 88368,
                'pstatlen': 616,
                'pagesize': 4096,
                'supportflags': 5,
                'osrel': 3,
                'osvers': 16,
                'ossub': 0,
            },
        },
        'Incorrect magic number': {
            'args': [
                io.BytesIO(HEADER_BYTES.replace(b'\xef', b'\xed')),
            ],
            'raises': ValueError,
        },
        'Truncated': {
            'args': [
                io.BytesIO(HEADER_BYTES[:32]),
            ],
            'raises': ValueError,
        },
    },
    'get_record': {
        'Valid': {
            'args': [
                io.BytesIO(HEADER_BYTES + RECORD_BYTES),
                atop_126_structs.Record,
            ],
            'expected_result': {
                'curtime': 1556245087,
                'flags': 0,
                'interval': 60,
                'nexit': 591,
                'nlist': 825,
                'npresent': 234,
                'ntrun': 4,
                'ntslpi': 517,
                'ntslpu': 0,
                'nzombie': 0,
                'pcomplen': 14232,
                'scomplen': 956,
            },
        },
        'Truncated': {
            'args': [
                io.BytesIO(HEADER_BYTES + RECORD_BYTES[:16]),
                atop_126_structs.Record,
            ],
            'expected_result': {
                'curtime': 1556245087,
                'flags': 0,
                'interval': 0,
                'nexit': 0,
                'nlist': 0,
                'npresent': 0,
                'ntrun': 0,
                'ntslpi': 0,
                'ntslpu': 0,
                'nzombie': 0,
                'pcomplen': 0,
                'scomplen': 0,
            },
        },
    },
    'get_sstat': {
        'Valid': {
            'args': [
                io.BytesIO(HEADER_BYTES + RECORD_BYTES + SSTAT_BYTES),
                None,
            ],
            'expected_result': {
                'cpu': {
                    'lavg15': 0.25,
                    'nrcpu': 8,
                },
                'dsk': {
                    'ndsk': 9,
                    'nlvm': 0,
                },
                'intf': {
                    'nrintf': 30,
                },
                'mem': {
                    'committed': 616285,
                    'physmem': 1969977,
                },
                'net': {
                    'icmpv4': {
                        'InMsgs': 280,
                        'OutAddrMaskReps': 0,
                    },
                    'icmpv6': {
                        'Icmp6InMsgs': 88,
                        'Icmp6OutGroupMembReductions': 0,
                    },
                    'ipv4': {
                        'Forwarding': 1,
                        'FragCreates': 0,
                    },
                    'ipv6': {
                        'Ip6InReceives': 109,
                        'Ip6OutMcastPkts': 0,
                    },
                    'tcp': {
                        'OutRsts': 4,
                        'RtoAlgorithm': 1,
                    },
                    'udpv4': {
                        'InDatagrams': 113,
                        'OutDatagrams': 53,
                    },
                    'udpv6': {
                        'Udp6InDatagrams': 0,
                        'Udp6OutDatagrams': 0,
                    }
                },
                'www': {
                    'accesses': 0,
                    'iworkers': 0,
                }
            },
        },
        'Truncated': {
            'args': [
                io.BytesIO(HEADER_BYTES + RECORD_BYTES + SSTAT_BYTES[:16]),
                None
            ],
            'raises': zlib.error,
        },
    },
    'header_check_compatibility': {
        '1.26': {
            'args': [
                atop_helpers.get_header(io.BytesIO(HEADER_BYTES))
            ],
            'expected_result': None,
        },
    },
    'header_semantic_version': {
        '1.26': {
            'args': [
                atop_helpers.get_header(io.BytesIO(HEADER_BYTES))
            ],
            'expected_result': 1.26,
        },
    },
    'struct_to_dict': {
        '1.26': {
            'args': [
                atop_helpers.get_header(io.BytesIO(HEADER_BYTES))
            ],
            'expected_result': {
                'aversion': 33050,
                'hertz': 100,
                'magic': 4276993775,
                'osrel': 3,
                'ossub': 0,
                'osvers': 16,
                'pagesize': 4096,
                'pstatlen': 616,
                'rawheadlen': 480,
                'rawreclen': 80,
                'sstatlen': 88368,
                'supportflags': 5,
                'utsname': {
                    'domain': 'theshire.co',
                    'machine': 'x86_64',
                    'nodename': 'fires-of-mount-doom1',
                    'release': '3.16.0-44-mordor1',
                    'sysname': 'Linux',
                    'version': '#59~14.04.1 SMP PREEMPT Fri Dec 28 20:04:09 UTC 2018'
                }
            },
        },
    }
}


def _header_to_dict(header: atop_126_structs.Header) -> dict:
    """Helper to convert header structs into dictionaries for comparison operations."""
    header_map = {
        'magic': header.magic,
        'aversion': header.aversion,
        'future1': header.future1,
        'future2': header.future2,
        'rawheadlen': header.rawheadlen,
        'rawreclen': header.rawreclen,
        'hertz': header.hertz,
        'sstatlen': header.sstatlen,
        'pstatlen': header.pstatlen,
        'pagesize': header.pagesize,
        'supportflags': header.supportflags,
        'osrel': header.osrel,
        'osvers': header.osvers,
        'ossub': header.ossub,
    }
    return header_map


def _record_to_dict(record: atop_126_structs.Record) -> dict:
    """Helper to convert record structs into dictionaries for comparison operations."""
    record_map = {
        'curtime': record.curtime,
        'flags': record.flags,
        'scomplen': record.scomplen,
        'pcomplen': record.pcomplen,
        'interval': record.interval,
        'nlist': record.nlist,
        'npresent': record.npresent,
        'nexit': record.nexit,
        'ntrun': record.ntrun,
        'ntslpi': record.ntslpi,
        'ntslpu': record.ntslpu,
        'nzombie': record.nzombie,
    }
    return record_map


def _sstat_to_dict(sstat: atop_126_structs.SStat) -> dict:
    """Helper to convert sstat structs into dictionaries for comparison operations."""
    # Only pull the first and last value non-array value from each struct.
    # This will prove bytes were read into structs successfully in the correct order.
    sstat_map = {
        'cpu': {
            'nrcpu': sstat.cpu.nrcpu,
            'lavg15': sstat.cpu.lavg15,
        },
        'mem': {
            'physmem': sstat.mem.physmem,
            'committed': sstat.mem.committed,
        },
        'net': {
            'ipv4': {
                'Forwarding': sstat.net.ipv4.Forwarding,
                'FragCreates': sstat.net.ipv4.FragCreates,
            },
            'icmpv4': {
                'InMsgs': sstat.net.icmpv4.InMsgs,
                'OutAddrMaskReps': sstat.net.icmpv4.OutAddrMaskReps,
            },
            'udpv4': {
                'InDatagrams': sstat.net.udpv4.InDatagrams,
                'OutDatagrams': sstat.net.udpv4.OutDatagrams,
            },
            'ipv6': {
                'Ip6InReceives': sstat.net.ipv6.Ip6InReceives,
                'Ip6OutMcastPkts': sstat.net.ipv6.Ip6OutMcastPkts,
            },
            'icmpv6': {
                'Icmp6InMsgs': sstat.net.icmpv6.Icmp6InMsgs,
                'Icmp6OutGroupMembReductions': sstat.net.icmpv6.Icmp6OutGroupMembReductions,
            },
            'udpv6': {
                'Udp6InDatagrams': sstat.net.udpv6.Udp6InDatagrams,
                'Udp6OutDatagrams': sstat.net.udpv6.Udp6OutDatagrams,
            },
            'tcp': {
                'RtoAlgorithm': sstat.net.tcp.RtoAlgorithm,
                'OutRsts': sstat.net.tcp.OutRsts,
            },
        },
        'intf': {
            'nrintf': sstat.intf.nrintf,
        },
        'dsk': {
            'ndsk': sstat.dsk.ndsk,
            'nlvm': sstat.dsk.nlvm,
        },
        'www': {
            'accesses': sstat.www.accesses,
            'iworkers': sstat.www.iworkers,
        },
    }
    return sstat_map


def run_basic_test_case(test_case: dict, context: callable, comparator: callable = None) -> None:
    """Run a basic test_case configuration against the given context.

    Args:
        test_case: A dictionary containing configuration parameters for testing a callable.
        context: A callable to pass args and kwargs that will return value to compare.
        comparator: A function to use for comparing the expected_results and result.
            Defaults to doing a direct "==" comparison.

    Example:
        test_case (test raising an error) = {'raises': ValueError, 'kwargs': {'value': None}}
        test_case (test getting expected result) = {'expected_result': 10, 'args': [5, 12]}
    """
    args = test_case.get('args', [])
    kwargs = test_case.get('kwargs', {})
    raises = test_case.get('raises')
    if raises:
        with pytest.raises(raises):
            context(*args, **kwargs)
    else:
        expected_result = test_case.get('expected_result')
        result = context(*args, **kwargs)
        message = f'Got an unexpected result.\n\nExpected: "{expected_result}"\n\nActual: "{result}"'
        if comparator:
            comparator(result, expected_result)
        else:
            assert result == expected_result, message


@pytest.mark.parametrize(
    'test_case',
    list(TEST_CASES['get_header'].values()),
    ids=list(TEST_CASES['get_header'].keys()),
)
def test_get_header(test_case: dict) -> None:
    """Unit tests for get_header."""
    def comparison_method(result, expected_result):
        """Manual comparison method to convert header into dict."""
        assert _header_to_dict(result) == expected_result
    run_basic_test_case(test_case, atop_helpers.get_header, comparator=comparison_method)


@pytest.mark.parametrize(
    'test_case',
    list(TEST_CASES['get_record'].values()),
    ids=list(TEST_CASES['get_record'].keys()),
)
def test_get_record(test_case: dict) -> None:
    """Unit tests for get_record."""
    def comparison_method(result, expected_result):
        """Manual comparison method to convert record into dict."""
        assert _record_to_dict(result) == expected_result

    # Read the header to ensure the offset is correct prior to reading the record:
    atop_helpers.get_header(test_case['args'][0])
    run_basic_test_case(test_case, atop_helpers.get_record, comparator=comparison_method)


@pytest.mark.parametrize(
    'test_case',
    list(TEST_CASES['get_sstat'].values()),
    ids=list(TEST_CASES['get_sstat'].keys()),
)
def test_get_sstat(test_case: dict) -> None:
    """Unit tests for get_sstat."""
    def comparison_method(result, expected_result):
        """Manual comparison method to convert sstat into dict."""
        assert _sstat_to_dict(result) == expected_result

    # Read the header and record to ensure the offset is correct prior to reading the record:
    header = atop_helpers.get_header(test_case['args'][0])
    record = atop_helpers.get_record(test_case['args'][0], atop_126_structs.Record)
    run_basic_test_case(
        test_case=test_case,
        # Pass in the record that was read from the file since it cannot be declared beforehand
        context=lambda raw_file, _: atop_helpers.get_sstat(raw_file, record, atop_126_structs.SStat),
        comparator=comparison_method
    )


@pytest.mark.parametrize(
    'test_case',
    list(TEST_CASES['header_check_compatibility'].values()),
    ids=list(TEST_CASES['header_check_compatibility'].keys()),
)
def test_header_check_compatibility(test_case: dict) -> None:
    """Unit tests for header check_compatibility."""
    run_basic_test_case(test_case, test_case['args'][0].__class__.check_compatibility)


@pytest.mark.parametrize(
    'test_case',
    list(TEST_CASES['header_semantic_version'].values()),
    ids=list(TEST_CASES['header_semantic_version'].keys()),
)
def test_header_semantic_version(test_case: dict) -> None:
    """Unit tests for header semantic_version."""
    run_basic_test_case(test_case, lambda self: self.semantic_version)


@pytest.mark.parametrize(
    'parseable',
    list(atop_reader.PARSEABLES),
    ids=list(atop_reader.PARSEABLES),
)
def test_parseable_map(parseable: str) -> None:
    """Unit test to ensure every parseable has a corresponding parse_* function."""
    assert getattr(atop_126_parsers, f'parse_{parseable}') is not None, f'Failed to find parse function for {parseable}'


@pytest.mark.parametrize(
    'test_case',
    list(TEST_CASES['struct_to_dict'].values()),
    ids=list(TEST_CASES['struct_to_dict'].keys()),
)
def test_struct_to_dict(test_case: dict) -> None:
    """Unit test to verify conversion of C structs into basic dicts."""
    run_basic_test_case(test_case, atop_helpers.struct_to_dict)
