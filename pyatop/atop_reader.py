"""Simple ATOP log processor."""

import argparse
import json
import gzip

from pyatop import atop_helpers

PARSEABLES = ['cpu', 'CPL', 'CPU', 'DSK', 'LVM', 'MDD', 'MEM', 'NETL', 'NETU', 'PAG', 'PRC', 'PRG', 'PRM', 'PRN', 'SWP']
PARSEABLE_MAP = {parseable: getattr(atop_helpers, f'parse_{parseable}') for parseable in PARSEABLES}


def parse_args() -> argparse.Namespace:
    """Parse user arguments.

    Return:
        args: Namespace with all the user arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+', help='Files to process. Must be in gzip compressed.')
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
            for record, sstat, pstat in atop_helpers.gen_stats(raw_file, header):
                for parseable in args.parseables:
                    for sample in PARSEABLE_MAP[parseable](header, record, sstat, pstat):
                        sample['parseable'] = parseable
                        samples.append(sample)
        print(json.dumps(samples, indent=2 if args.pretty_print else None))


if __name__ == '__main__':
    main()
