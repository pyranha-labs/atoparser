"""Helpers used to serialize/deserialize ATOP statistics directly from log files.

The basic layout of an ATOP log file can be described as the following:
1. Raw Header:
    - Single instance at the beginning of the file.
    - Contains information about all the following raw records.
2. Raw Record:
    - Single instance repeated in a loop with an SStat and TStat array until end of file.
    - Contains information about the *Stat structs that immediately follow it.
3. Raw SStat:
    - Single instance repeated in a loop with a Record and TStats array until end of file.
    - Always found directly after a Record.
    - Always found directly before a TStat array.
    - Contains statistics about overall system activity.
4. Raw TStats:
    - Array of TStat instances repeated in a loop with a Record and SStat until end of file.
    - Always found directly after a SStat.
    - Always found directly before the next Record if not the end of file.
    - Contains statistics about every task/process on the system.

See https://github.com/Atoptool/atop for more information and references to the C process source code.
"""

from __future__ import annotations

import ctypes
import io
import zlib
from typing import Union

from pyatop.structs import atop_126
from pyatop.structs import atop_230

Header = Union[
    atop_126.Header,
    atop_230.Header,
]
Record = Union[
    atop_126.Record,
    atop_230.Record,
]
SStat = Union[
    atop_126.SStat,
    atop_230.SStat,
]
TStat = Union[  # pylint: disable=invalid-name
    atop_126.TStat,  # pylint: disable=invalid-name
    atop_230.TStat,  # pylint: disable=invalid-name
]

# Fallback to 1.26 if there is no custom class provided to attempt backwards compatibility.
_DEFAULT_VERSION = 1.26
_HEADER_BY_VERSION: dict[float, type[Header]] = {
    1.26: atop_126.Header,
    2.3: atop_230.Header,
}
_RECORD_BY_VERSION: dict[float, type[Record]] = {
    1.26: atop_126.Record,
    2.3: atop_230.Record,
}
_SSTAT_BY_VERSION: dict[float, type[SStat]] = {
    1.26: atop_126.SStat,
    2.3: atop_230.SStat,
}
_TSTAT_BY_VERSION: dict[float, type[TStat]] = {
    1.26: atop_126.TStat,
    2.3: atop_230.TStat,
}

# Default ATOP sample is once per minute, but it can be manually increased/decreased.
# Additionally, logs may not rollover as expected, combining multiple hours into 1 log.
# Limit the amount of read attempts to 1 per second for 1 day to ensure we do not get stuck in an infinite loop.
MAX_SAMPLES_PER_FILE = 86400

# Definition from rawlog.c
MAGIC = 0xFEEDBEEF


def generate_statistics(
    raw_file: io.FileIO,
    header: Header = None,
    raise_on_truncation: bool = True,
    max_samples: int = MAX_SAMPLES_PER_FILE,
) -> tuple[Record, SStat, list[TStat]]:
    """Read statistics groups from an open ATOP log file.

    Args:
        raw_file: An open ATOP file capable of reading as bytes.
        header: The header from the file containing metadata about records to read. If not provided, one will be read.
        raise_on_truncation: Raise compression exceptions after header is read. e.g. Software restarts
        max_samples: Maximum number of samples read from a file.

    Yields:
        The next record, devsstat, and devtstat statistic groups after reading in raw bytes to objects.
    """
    if header is None:
        # If a header was not provided, read up to the proper length and discard to ensure the correct starting offset.
        header = get_header(raw_file)

    try:
        header_version = header.semantic_version
        record_cls = _RECORD_BY_VERSION.get(header_version, _RECORD_BY_VERSION[_DEFAULT_VERSION])
        sstat_cls = _SSTAT_BY_VERSION.get(header_version, _SSTAT_BY_VERSION[_DEFAULT_VERSION])
        tstat_cls = _TSTAT_BY_VERSION.get(header_version, _TSTAT_BY_VERSION[_DEFAULT_VERSION])
        for _ in range(max_samples):
            # Read the repeating structured information until the end of the file.
            # ATOP log files consist of the following after the header, repeated until the end:
            # 1. Record: Metadata about statistics.
            # 2. SStats: System statistics.
            # 3. TStats: Task/process statistics.
            record = get_record(raw_file, record_cls)
            devsstat = get_sstat(raw_file, record, sstat_cls)
            devtstats = get_tstat(raw_file, record, tstat_cls)
            yield record, devsstat, devtstats
    except zlib.error:
        # End of readable data reached. This is common during software restarts.
        # All errors after the header are squashable errors, since that means the file is valid, but was not closed.
        if raise_on_truncation:
            raise


def get_header(raw_file: io.FileIO) -> Header:
    """Get the raw file header from an open ATOP file.

    Args:
        raw_file: An open ATOP file capable of reading as bytes.

    Returns:
        The header at the beginning of an ATOP file.

    Raises:
        ValueError if there are not enough bytes to read the header, or the bytes were invalid.
    """
    # Read the header directly into the struct, there is no padding to consume or add.
    # Use default Header as the baseline in order to check the version. It can be transferred without re-reading.
    header = _HEADER_BY_VERSION[_DEFAULT_VERSION]()
    raw_file.readinto(header)

    if header.magic != MAGIC:
        msg = f"File does not contain raw atop output (wrong magic number): {hex(header.magic)}"
        raise ValueError(msg)

    header_version = header.semantic_version
    if header_version != _DEFAULT_VERSION and header_version in _HEADER_BY_VERSION:
        # Header byte length is consistent across versions. Transfer the initial read into the versioned header.
        header = _HEADER_BY_VERSION[header_version].from_buffer(header)

    # Ensure all struct lengths match the lengths specific in the header. If not, we cannot read the file further.
    header.check_compatibility()

    return header


def get_tstat(
    raw_file: io.FileIO,
    record: Record,
    tstat_cls: type[TStat],
) -> list[TStat]:
    """Get the next raw tstat array from an open ATOP file.

    Args:
        raw_file: An open ATOP file capable of reading as bytes.
        record: The preceding record containing metadata about the TStats to read.
        tstat_cls: TStat struct class to read the raw bytes into.

    Returns:
        All TStat structs after a raw SStat, but before the next raw record.

    Raises:
        ValueError if there are not enough bytes to read a stat array.
    """
    # Read the requested length instead of the length of the struct.
    # The data is compressed and must be decompressed before it will fill the final list of structs.
    buffer = raw_file.read(record.pcomplen)
    decompressed = zlib.decompress(buffer)

    # The final decompressed data is an array of structs, with the length determined by the raw record.
    uncompressed_len = ctypes.sizeof(tstat_cls)
    record_count = record.nlist if isinstance(record, atop_126.Record) else record.ndeviat
    tstats = []
    for index in range(record_count):
        # Reconstruct one TStat struct for every possible byte chunk, incrementing the offset each pass. For example:
        # First pass: 0 - 21650
        # Second pass: 21651 - 43300
        start = index * uncompressed_len
        end = uncompressed_len * (index + 1)
        tstat = tstat_cls.from_buffer_copy(decompressed[start:end])
        tstats.append(tstat)
    return tstats


def get_record(raw_file: io.FileIO, record_cls: type[Record]) -> Record:
    """Get the next raw record from an open ATOP file.

    Args:
        raw_file: An open ATOP file capable of reading as bytes.
        record_cls: Record struct class to read the raw bytes into.

    Returns:
        A single record representing the data before an SStat struct.

    Raises:
        ValueError if there are not enough bytes to read a single record.
    """
    record = record_cls()
    raw_file.readinto(record)
    return record


def get_sstat(
    raw_file: io.FileIO,
    raw_record: Record,
    sstat_cls: type[SStat],
) -> SStat:
    """Get the next raw sstat from an open ATOP file.

    Args:
        raw_file: An open ATOP file capable of reading as bytes.
        raw_record: The preceding record containing metadata about the SStat to read.
        sstat_cls: SStat struct class to read the raw bytes into.

    Returns:
        A single struct representing the data after a raw record, but before an array of TStat structs.

    Raises:
        ValueError if there are not enough bytes to read a single stat.
    """
    # Read the requested length instead of the length of the struct.
    # The data is compressed and must be decompressed before it will fill the struct.
    buffer = raw_file.read(raw_record.scomplen)
    decompressed = zlib.decompress(buffer)
    sstat = sstat_cls.from_buffer_copy(decompressed)
    return sstat


def struct_to_dict(struct: ctypes.Structure) -> dict:
    """Convert C struct, and all nested structs, into a Python dictionary.

    Skips any "future" named fields since they are empty placeholders for potential future versions.

    Args:
        struct: C struct loaded from raw ATOP file.

    Returns:
        C struct converted into a dictionary using the names of the struct's fields as keys.
    """
    struct_dict = {}
    for field in struct._fields_:  # pylint: disable=protected-access
        field_name = field[0]
        field_data = getattr(struct, field_name)
        if isinstance(field_data, ctypes.Structure):
            struct_dict[field_name] = struct_to_dict(field_data)
        elif "future" not in field_name:
            if isinstance(field_data, ctypes.Array):
                struct_dict[field_name] = []
                limiters = getattr(struct, "fields_limiters", {})
                limiter = limiters.get(field_name)
                if limiter:
                    field_data = field_data[: getattr(struct, limiter)]
                for subdata in field_data[: getattr(struct, struct.fields_limiters.get(field_name))]:
                    struct_dict[field_name].append(struct_to_dict(subdata))
            elif isinstance(field_data, bytes):
                struct_dict[field_name] = field_data.decode()
            else:
                struct_dict[field_name] = field_data
    return struct_dict
