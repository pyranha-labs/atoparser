#! /usr/bin/env python3

"""Simple Atop log processor."""

import argparse
import gzip
import json

import atoparser
from atoparser.parsers import atop_1_26

PARSEABLES = ["cpu", "CPL", "CPU", "DSK", "LVM", "MDD", "MEM", "NETL", "NETU", "PAG", "PRC", "PRG", "PRM", "PRN", "SWP"]
PARSEABLE_MAP = {
    "1.26": {parseable: getattr(atop_1_26, f"parse_{parseable}") for parseable in PARSEABLES},
}


def parse_args() -> argparse.Namespace:
    """Parse user arguments.

    Returns:
        Namespace with all the user arguments.
    """
    parser = argparse.ArgumentParser(
        "Convert binary files into JSON output.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="Files to process. May be uncompressed or gzip compressed.",
    )
    parser.add_argument(
        "-P",
        "--parseables",
        nargs="+",
        choices=PARSEABLES,
        metavar="PARSEABLE",
        help='Display output in Atop "parseable" format, instead of full structs. See "man atop" for full details. e.g. "CPU", "DSK", etc.',
    )
    parser.add_argument(
        "-p",
        "--pretty-print",
        action="store_true",
        help="Pretty print the JSON output with indentation.",
    )
    parser.add_argument(
        "--tstats",
        dest="show_tstats",
        action="store_true",
        help="Include TStats/PStats in output. Very verbose.",
    )
    parser.add_argument(
        "--cstats",
        dest="show_cstats",
        action="store_true",
        help="Include CGroup/CStats in output. Only available with Atop 2.11+ logs. Verbose.",
    )
    args = parser.parse_args()
    return args


def parse_file(  # pylint: disable=too-many-locals
    file: str,
    parseables: list[str] | None = None,
    pretty_print: bool = True,
    show_tstats: bool = False,
    show_cstats: bool = False,
) -> None:
    """Parse a single file.

    Args:
        file: File path to process.
        parseables: Atop "parseable" formats to display, instead of full structs.
        pretty_print: Whether to pretty print the JSON output with indentation.
        show_tstats: Whether to include TStats/PStats in output.
        show_cstats: Wheter to include CGroup/CStats in output
    """
    samples = []
    opener = open if ".gz" not in file else gzip.open
    with opener(file, "rb") as raw_file:
        header = atoparser.get_header(raw_file)
        if parseables and header.semantic_version not in PARSEABLE_MAP:
            samples.append(
                {
                    "error": f"Atop version {header.semantic_version} does not support parseables, only full raw output.",
                    "file": file,
                }
            )
        else:
            parsers = PARSEABLE_MAP.get(header.semantic_version, PARSEABLE_MAP["1.26"])
            for record, sstat, tstats, cgroups in atoparser.generate_statistics(
                raw_file,
                header,
                raise_on_truncation=False,
            ):
                if parseables:
                    for parseable in parseables:
                        for sample in parsers[parseable](header, record, sstat, tstats):
                            sample["parseable"] = parseable
                            samples.append(sample)
                else:
                    converted = {
                        "header": atoparser.struct_to_dict(header),
                        "record": atoparser.struct_to_dict(record),
                        "sstat": atoparser.struct_to_dict(sstat),
                    }
                    if show_tstats:
                        converted["tstat"] = [atoparser.struct_to_dict(stat) for stat in tstats]
                    if show_cstats:
                        converted["cgroup"] = [atoparser.struct_to_dict(stat) for stat in cgroups]
                    samples.append(converted)
    print(json.dumps(samples, indent=2 if pretty_print else None))


def main() -> None:
    """Primary function to load Atop data."""
    args = parse_args()

    for file in args.files:
        parse_file(
            file,
            args.parseables,
            args.pretty_print,
            args.show_tstats,
            args.show_cstats,
        )


if __name__ == "__main__":
    main()
