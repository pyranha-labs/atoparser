"""Simple ATOP log processor."""

import argparse
import gzip
import json

from pyatop import atop_helpers
from pyatop.parsers import atop_126

PARSEABLES = ['cpu', 'CPL', 'CPU', 'DSK', 'LVM', 'MDD', 'MEM', 'NETL', 'NETU', 'PAG', 'PRC', 'PRG', 'PRM', 'PRN', 'SWP']
PARSEABLE_MAP = {
    1.26: {parseable: getattr(atop_126, f'parse_{parseable}') for parseable in PARSEABLES},
}


def parse_args() -> argparse.Namespace:
    """Parse user arguments.

    Return:
        args: Namespace with all the user arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+', help='Files to process. May be uncompressed or gzip compressed.')
    parser.add_argument('-P', '--parseables', nargs='+', choices=PARSEABLES, required=True,
                        help='One or more ATOP parseable names. See "man atop" for full details.')
    parser.add_argument('--pretty-print', action='store_true',
                        help='Pretty print the JSON output with indentation.')
    args = parser.parse_args()
    return args


def main() -> None:
    """Primary function to load ATOP data."""
    args = parse_args()

    for file in args.files:
        samples = []
        opener = open if '.gz' not in file else gzip.open
        with opener(file, 'rb') as raw_file:
            header = atop_helpers.get_header(raw_file)
            parsers = PARSEABLE_MAP.get(header.get_version(), PARSEABLE_MAP[1.26])
            for record, sstat, tstat in atop_helpers.generate_statistics(raw_file, header, raise_on_truncation=False):
                for parseable in args.parseables:
                    for sample in parsers[parseable](header, record, sstat, tstat):
                        sample['parseable'] = parseable
                        samples.append(sample)
        print(json.dumps(samples, indent=2 if args.pretty_print else None))


if __name__ == '__main__':
    main()
