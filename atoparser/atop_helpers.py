"""Helpers used to serialize/deserialize Atop statistics directly from log files.

The basic layout of an Atop log file can be described as the following:
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
"""

from __future__ import annotations

import ctypes
import io
import zlib
from typing import Union

from atoparser.structs import atop_1_26
from atoparser.structs import atop_2_3
from atoparser.structs import atop_2_4
from atoparser.structs import atop_2_5
from atoparser.structs import atop_2_6
from atoparser.structs import atop_2_7
from atoparser.structs import atop_2_8
from atoparser.structs import atop_2_9
from atoparser.structs import atop_2_10

_VERSIONS = [
    atop_1_26,
    atop_2_3,
    atop_2_4,
    atop_2_5,
    atop_2_6,
    atop_2_7,
    atop_2_8,
    atop_2_9,
    atop_2_10,
]
Header = Union[tuple(module.Header for module in _VERSIONS)]
Record = Union[tuple(module.Record for module in _VERSIONS)]
SStat = Union[tuple(module.SStat for module in _VERSIONS)]
TStat = Union[tuple(module.TStat for module in _VERSIONS)]  # pylint: disable=invalid-name
_HEADER_BY_VERSION: dict[str, type[Header]] = {module.Header.supported_version: module.Header for module in _VERSIONS}
_RECORD_BY_VERSION: dict[str, type[Record]] = {module.Header.supported_version: module.Record for module in _VERSIONS}
_SSTAT_BY_VERSION: dict[str, type[SStat]] = {module.Header.supported_version: module.SStat for module in _VERSIONS}
_TSTAT_BY_VERSION: dict[str, type[TStat]] = {module.Header.supported_version: module.TStat for module in _VERSIONS}

# Fallback to latest if there is no custom class provided to attempt backwards compatibility.
_DEFAULT_VERSION = list(_HEADER_BY_VERSION.keys())[-1]

# Default Atop sample is once per minute, but it can be manually increased/decreased.
# Additionally, logs may not rollover as expected, combining multiple hours into 1 log.
# Limit the amount of read attempts to 1 per second for 1 day to ensure we do not get stuck in an infinite loop.
MAX_SAMPLES_PER_FILE = 86400

# Definition from rawlog.c
MAGIC = 0xFEEDBEEF


def generate_statistics(
    raw_file: io.BytesIO,
    header: Header = None,
    raise_on_truncation: bool = True,
    max_samples: int = MAX_SAMPLES_PER_FILE,
) -> tuple[Record, SStat, list[TStat]]:
    """Read statistics groups from an open Atop log file.

    Args:
        raw_file: An open Atop file capable of reading as bytes.
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
            # Atop log files consist of the following after the header, repeated until the end:
            # 1. Record: Metadata about statistics.
            # 2. SStats: System statistics.
            # 3. TStats: Task/process statistics.
            record = get_record(raw_file, record_cls)
            if record.scomplen <= 0:
                # Natural end-of-file, no further bytes were found to populate another record.
                break
            devsstat = get_sstat(raw_file, record, sstat_cls)
            devtstats = get_tstat(raw_file, record, tstat_cls)
            yield record, devsstat, devtstats
    except zlib.error:
        # End of readable data reached. This is common during software restarts.
        # All errors after the header are squashable errors, since that means the file is valid, but was not closed.
        if raise_on_truncation:
            raise


def get_header(raw_file: io.BytesIO, check_compatibility: bool = True) -> Header:
    """Get the raw file header from an open Atop file.

    Args:
        raw_file: An open Atop file capable of reading as bytes.
        check_compatibility: Whether to enforce compatibility check against supported versions on header creation.

    Returns:
        The header at the beginning of an Atop file.

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

    if check_compatibility:
        # Ensure all struct lengths match the lengths specified in the header. If not, we cannot read the file further.
        header.check_compatibility()

    return header


def get_record(raw_file: io.BytesIO, record_cls: type[Record]) -> Record:
    """Get the next raw record from an open Atop file.

    Args:
        raw_file: An open Atop file capable of reading as bytes.
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
    raw_file: io.BytesIO,
    raw_record: Record,
    sstat_cls: type[SStat],
) -> SStat:
    """Get the next raw sstat from an open Atop file.

    Args:
        raw_file: An open Atop file capable of reading as bytes.
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


def get_tstat(
    raw_file: io.BytesIO,
    record: Record,
    tstat_cls: type[TStat],
) -> list[TStat]:
    """Get the next raw tstat array from an open Atop file.

    Args:
        raw_file: An open Atop file capable of reading as bytes.
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
    record_count = record.nlist if isinstance(record, atop_1_26.Record) else record.ndeviat
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


def struct_to_dict(struct: ctypes.Structure) -> dict:
    """Convert C struct, and all nested structs, into a Python dictionary.

    Skips any "future" named fields since they are empty placeholders for potential future versions.

    Args:
        struct: C struct loaded from raw Atop file.

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
                struct_dict[field_name] = field_data.decode(errors="ignore")
            else:
                struct_dict[field_name] = field_data
    return struct_dict
