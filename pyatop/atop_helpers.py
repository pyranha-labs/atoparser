"""Helpers used to serialize/deserialize ATOP statistics directly from log files.

The basic layout of an ATOP log file can be described as the following:
1. Raw Header:
    - Single instance at the beginning of the file.
    - Contains information about all the following raw records.
2. Raw Record:
    - Single instance repeated in a loop with an SStat array and PStat array until end of file.
    - Contains information about the *Stat structs that immediately follow it.
3. Raw SStat:
    - Single instance repeated in a loop with a Record and PStats array until end of file.
    - Always found directly after a Record.
    - Always found directly before a PStat array.
    - Contains statistics about overall system activity.
4. Raw PStats:
    - Array of PStat instances repeated in a loop with a Record and SStat until end of file.
    - Always found directly after a SStat.
    - Always found directly before the next Record if not the end of file.
    - Contains statistics about every process on the system.

See https://github.com/Atoptool/atop for more information and references to the C process source code.
Using schemas and structs from ATOP 1.26.
"""

import io
import zlib

from typing import List
from typing import Tuple

from pyatop import atop_structs

# Default ATOP sample is once per minute, but it can be manually increased/decreased.
# Additionally, logs may not rollover as expected, combining multiple hours into 1 log.
# Limit the amount of read attempts to 1 per second for 1 day to ensure we do not get stuck in an infinite loop.
MAX_SAMPLES_PER_FILE = 86400


def generate_statistics(
        raw_file: io.FileIO,
        header: atop_structs.Header = None,
        raise_on_truncation: bool = True,
        max_samples: int = MAX_SAMPLES_PER_FILE,
) -> Tuple[atop_structs.Record, atop_structs.SStat, List[atop_structs.PStat]]:
    """Read statistics groups from an open ATOP log file.

    Args:
        raw_file: An open ATOP file capable of reading as bytes.
        header: The header from the file containing metadata about records to read. If not provided, one will be read.
        raise_on_truncation: Raise compression exceptions after header is read. e.g. Software restarts
        max_samples: Maximum number of samples read from a file.

    Yields:
        record, devsstat, devpstats: The next statistic group after reading in raw bytes to objects.
    """
    if header is None:
        # If a header was not provided, read up to the proper length and discard to ensure the correct starting offset.
        get_header(raw_file)

    try:
        for _ in range(max_samples):
            # Read the repeating structured information until the end of the file.
            # ATOP log files consist of the following after the header, repeated until the end:
            # 1. Record: Metadata about statistics.
            # 2. SStats: System statistics.
            # 3. PStats: Process statistics.
            record = get_record(raw_file)
            devsstat = get_sstat(raw_file, record)
            devpstats = get_pstat(raw_file, record)
            yield record, devsstat, devpstats
    except zlib.error:
        # End of readable data reached. This is common during software restarts.
        # All errors after the header are squashable errors, since that means the file is valid, but was not closed.
        if raise_on_truncation:
            raise


def get_header(raw_file: io.FileIO) -> atop_structs.Header:
    """Get the raw file header from an open ATOP file.

    Args:
        raw_file: An open ATOP file capable of reading as bytes.

    Returns:
        raw_header: The header at the beginning of an ATOP file.

    Raises:
        ValueError: If there are not enough bytes to read the header, or the bytes were invalid.
    """
    # Read the header directly into the struct, there is no padding to consume or add.
    header = atop_structs.Header()
    raw_file.readinto(header)

    if header.magic != atop_structs.MAGIC:
        msg = f'File does not contain raw atop/atopsar output (wrong magic number): {hex(header.magic)}'
        raise ValueError(msg)

    # Ensure all struct lengths match the lengths specific in the header. If not, we cannot read the file further.
    header.check_compatibility()

    return header


def get_pstat(
        raw_file: io.FileIO,
        record: atop_structs.Record,
        uncompressed_len: int = atop_structs.SIZEOF_PSTAT
) -> List[atop_structs.PStat]:
    """Get the next raw pstat array from an open ATOP file.

    Args:
        raw_file: An open ATOP file capable of reading as bytes.
        record: The preceding record containing metadata about the PStats to read.
        uncompressed_len: The size of a single raw pstat struct after decompression. Should match sizeof struct.

    Return:
        pstats: All PStat structs after a raw SStat, but before the next raw record.

    Raises:
        ValueError: If there are not enough bytes to read a stat array.
    """
    # Read the requested length instead of the length of the struct.
    # The data is compressed and must be decompressed before it will fill the final list of structs.
    buffer = raw_file.read(record.pcomplen)
    decompressed = zlib.decompress(buffer)

    # The final decompressed data is an array of structs, with the length determined by the raw record.
    pstats = []
    for index in range(record.nlist):
        # Reconstruct one PStat struct for every possible byte chunk, incrementing the offset each pass. For example:
        # First pass: 0 - 21650
        # Second pass: 21651 - 43300
        start = index * uncompressed_len
        end = uncompressed_len * (index + 1)
        pstat = atop_structs.PStat.from_buffer_copy(decompressed[start:end])
        pstats.append(pstat)
    return pstats


def get_record(raw_file: io.FileIO) -> atop_structs.Record:
    """Get the next raw record from an open ATOP file.

    Args:
        raw_file: An open ATOP file capable of reading as bytes.

    Return:
        record: A single record representing the data before an SStat struct.

    Raises:
        ValueError: If there are not enough bytes to read a single record.
    """
    record = atop_structs.Record()
    raw_file.readinto(record)
    return record


def get_sstat(
        raw_file: io.FileIO,
        raw_record: atop_structs.Record,
) -> atop_structs.SStat:
    """Get the next raw sstat from an open ATOP file.

    Args:
        raw_file: An open ATOP file capable of reading as bytes.
        raw_record: The preceding record containing metadata about the SStat to read.

    Return:
        raw_record: A single struct representing the data after a raw record, but before an array of PStat structs.

    Raises:
        ValueError: If there are not enough bytes to read a single stat.
    """
    # Read the requested length instead of the length of the struct.
    # The data is compressed and must be decompressed before it will fill the struct.
    buffer = raw_file.read(raw_record.scomplen)
    decompressed = zlib.decompress(buffer)
    sstat = atop_structs.SStat.from_buffer_copy(decompressed)
    return sstat


# Disable the following pylint warnings to allow functions to match a consistent type across all parseables.
# This helps simplify calls allow dynamic function lookups to have consistent input arguments.
# pylint: disable=unused-argument,invalid-name

def parse_cpu(
        header: atop_structs.Header,
        record: atop_structs.Record,
        sstat: atop_structs.SStat,
        pstats: List[atop_structs.PStat],
) -> dict:
    """Retrieves statistics for Atop 'cpu' parseable representing per core usage."""
    for index, cpu in enumerate(sstat.cpu.cpu):
        if index >= sstat.cpu.nrcpu:
            # Core list contains 100 entries, but only up the count specified in the cpu stat are valid.
            break
        values = {
            'timestamp': record.curtime,
            'interval': record.interval,
            'ticks': header.hertz,
            'proc': index,
            'system': cpu.stime,
            'user': cpu.utime,
            'niced': cpu.ntime,
            'idle': cpu.itime,
            'wait': cpu.wtime,
            'irq': cpu.Itime,
            'softirq': cpu.Stime,
            'steal': cpu.steal,
            'guest': cpu.guest,
        }
        yield values


def parse_CPL(
        header: atop_structs.Header,
        record: atop_structs.Record,
        sstat: atop_structs.SStat,
        pstats: List[atop_structs.PStat],
) -> dict:
    """Retrieves statistics for Atop 'CPL' parseable representing system load."""
    values = {
        'timestamp': record.curtime,
        'interval': record.interval,
        'procs': sstat.cpu.nrcpu,
        'load_1': sstat.cpu.lavg1,
        'load_5': sstat.cpu.lavg5,
        'load_15': sstat.cpu.lavg15,
        'context_switches': sstat.cpu.csw,
        'interrupts': sstat.cpu.devint,
    }
    yield values


def parse_CPU(
        header: atop_structs.Header,
        record: atop_structs.Record,
        sstat: atop_structs.SStat,
        pstats: List[atop_structs.PStat],
) -> dict:
    """Statistics for Atop 'CPU' parseable representing usage across cores combined."""
    values = {
        'timestamp': record.curtime,
        'interval': record.interval,
        'ticks': header.hertz,
        'procs': sstat.cpu.nrcpu,
        'system': sstat.cpu.all.stime,
        'user': sstat.cpu.all.utime,
        'niced': sstat.cpu.all.ntime,
        'idle': sstat.cpu.all.itime,
        'wait': sstat.cpu.all.wtime,
        'irq': sstat.cpu.all.Itime,
        'softirq': sstat.cpu.all.Stime,
        'steal': sstat.cpu.all.steal,
        'guest': sstat.cpu.all.guest,
    }
    yield values


def parse_DSK(
        header: atop_structs.Header,
        record: atop_structs.Record,
        sstat: atop_structs.SStat,
        pstats: List[atop_structs.PStat],
) -> dict:
    """Retrieves statistics for Atop 'DSK' parseable representing disk/drive usage."""
    for disk in sstat.dsk.dsk:
        if not disk.name:
            # Disk list contains 256 entries, but only up the first empty name are valid.
            break
        values = {
            'timestamp': record.curtime,
            'interval': record.interval,
            'name': disk.name.decode(),
            'io_ms': disk.io_ms,
            'reads': disk.nread,
            'read_sectors': disk.nrsect,
            'writes': disk.nwrite,
            'write_sectors': disk.nwsect,
        }
        yield values


def parse_LVM(
        header: atop_structs.Header,
        record: atop_structs.Record,
        sstat: atop_structs.SStat,
        pstats: List[atop_structs.PStat],
) -> dict:
    """Retrieves statistics for Atop 'LVM' parseable representing logical volume usage."""
    for lvm in sstat.dsk.lvm:
        if not lvm.name:
            # LVM list contains 256 entries, but only up the first empty name are valid.
            break
        values = {
            'timestamp': record.curtime,
            'interval': record.interval,
            'name': lvm.name.decode(),
            'io_ms': lvm.io_ms,
            'reads': lvm.nread,
            'read_sectors': lvm.nrsect,
            'writes': lvm.nwrite,
            'write_sectors': lvm.nwsect,
        }
        yield values


def parse_MDD(
        header: atop_structs.Header,
        record: atop_structs.Record,
        sstat: atop_structs.SStat,
        pstats: List[atop_structs.PStat],
) -> dict:
    """Retrieves statistics for Atop 'MDD' parseable representing multiple device drive usage."""
    for mdd in sstat.dsk.mdd:
        if not mdd.name:
            # MDD list contains 256 entries, but only up the first empty name are valid.
            break
        values = {
            'timestamp': record.curtime,
            'interval': record.interval,
            'name': mdd.name.decode(),
            'io_ms': mdd.io_ms,
            'reads': mdd.nread,
            'read_sectors': mdd.nrsect,
            'writes': mdd.nwrite,
            'write_sectors': mdd.nwsect,
        }
        yield values


def parse_MEM(
        header: atop_structs.Header,
        record: atop_structs.Record,
        sstat: atop_structs.SStat,
        pstats: List[atop_structs.PStat],
) -> dict:
    """Retrieves statistics for Atop 'MEM' parseable representing memory usage."""
    values = {
        'timestamp': record.curtime,
        'interval': record.interval,
        'page_size': header.pagesize,
        'phys_mem': sstat.mem.physmem,
        'free_mem': sstat.mem.freemem,
        'page_cache': sstat.mem.cachemem,
        'buffer_cache': sstat.mem.buffermem,
        'slab': sstat.mem.slabmem,
        'dirty_pages': sstat.mem.cachedrt,
    }
    yield values


def parse_NETL(
        header: atop_structs.Header,
        record: atop_structs.Record,
        sstat: atop_structs.SStat,
        pstats: List[atop_structs.PStat],
) -> dict:
    """Retrieves statistics for Atop 'NET' parseable representing network usage on lower interfaces."""
    for interface in sstat.intf.intf:
        if not interface.name:
            # Interface list contains 32 entries, but only up the first empty name are valid.
            break
        values = {
            'timestamp': record.curtime,
            'interval': record.interval,
            'name': interface.name.decode(),
            'pkt_received': interface.rpack,
            'byte_received': interface.rbyte,
            'pkt_transmitted': interface.spack,
            'bytes_transmitted': interface.sbyte,
            'speed': interface.speed,
            'duplex': int.from_bytes(interface.duplex, byteorder='big'),
        }
        yield values


def parse_NETU(
        header: atop_structs.Header,
        record: atop_structs.Record,
        sstat: atop_structs.SStat,
        pstats: List[atop_structs.PStat],
) -> dict:
    """Retrieves statistics for Atop 'NET' parseable representing network usage on upper interfaces."""
    values = {
        'timestamp': record.curtime,
        'interval': record.interval,
        'name': 'upper',
        'tcp_pkt_received': sstat.net.tcp.InSegs,
        'tcp_pkt_transmitted': sstat.net.tcp.OutSegs,
        'udp_pkt_received': sstat.net.udpv4.InDatagrams + sstat.net.udpv6.Udp6InDatagrams,
        'udp_pkt_transmitted': sstat.net.udpv4.OutDatagrams + sstat.net.udpv6.Udp6OutDatagrams,
        'ip_pkt_received': sstat.net.ipv4.InReceives + sstat.net.ipv6.Ip6InReceives,
        'ip_pkt_transmitted': sstat.net.ipv4.OutRequests + sstat.net.ipv6.Ip6OutRequests,
        'ip_pkt_delivered': sstat.net.ipv4.InDelivers + sstat.net.ipv6.Ip6InDelivers,
        'ip_pkt_forwarded': sstat.net.ipv4.ForwDatagrams + sstat.net.ipv6.Ip6OutForwDatagrams,
    }
    yield values


def parse_PAG(
        header: atop_structs.Header,
        record: atop_structs.Record,
        sstat: atop_structs.SStat,
        pstats: List[atop_structs.PStat],
) -> dict:
    """Retrieves statistics for Atop 'PAG' parseable representing paging space usage."""
    values = {
        'timestamp': record.curtime,
        'interval': record.interval,
        'page_size': header.pagesize,
        'page_scans': sstat.mem.pgscans,
        'alloc_stalls': sstat.mem.allocstall,
        'swapins': sstat.mem.swins,
        'swapouts': sstat.mem.swouts,
    }
    yield values


def parse_PRC(
        header: atop_structs.Header,
        record: atop_structs.Record,
        sstat: atop_structs.SStat,
        pstats: List[atop_structs.PStat],
) -> dict:
    """Retrieves statistics for Atop 'PRC' parseable representing process cpu usage."""
    for pstat in pstats:
        values = {
            'timestamp': record.curtime,
            'interval': record.interval,
            'pid': pstat.gen.pid,
            'name': pstat.gen.name.decode(),
            'state': pstat.gen.state.decode(),
            'ticks': header.hertz,
            'user_consumption': pstat.cpu.utime,
            'system_consumption': pstat.cpu.stime,
            'nice': pstat.cpu.nice,
            'priority': pstat.cpu.prio,
            'priority_realtime': pstat.cpu.rtprio,
            'policy': pstat.cpu.policy,
            'cpu': pstat.cpu.curcpu,
            'sleep': pstat.cpu.sleepavg,
        }
        yield values


def parse_PRD(
        header: atop_structs.Header,
        record: atop_structs.Record,
        sstat: atop_structs.SStat,
        pstats: List[atop_structs.PStat],
) -> dict:
    """Retrieves statistics for Atop 'PRD' parseable representing process drive usage."""
    for pstat in pstats:
        values = {
            'timestamp': record.curtime,
            'interval': record.interval,
            'pid': pstat.gen.pid,
            'name': pstat.gen.name.decode(),
            'state': pstat.gen.state.decode(),
            'kernel_patch': 'y' if header.supportflags & atop_structs.PATCHSTAT else 'n',
            'standard_io': 'y' if header.supportflags & atop_structs.IOSTAT else 'n',
            'reads': pstat.dsk.rio,
            'read_sectors': pstat.dsk.rsz,
            'writes': pstat.dsk.wio,
            'written_sectors': pstat.dsk.wsz,
            'cancelled_sector_writes': pstat.dsk.cwsz,
        }
        yield values


def parse_PRG(
        header: atop_structs.Header,
        record: atop_structs.Record,
        sstat: atop_structs.SStat,
        pstats: List[atop_structs.PStat],
) -> dict:
    """Retrieves statistics for Atop 'PRG' parseable representing process generic details."""
    for pstat in pstats:
        values = {
            'timestamp': record.curtime,
            'interval': record.interval,
            'pid': pstat.gen.pid,
            'name': pstat.gen.name.decode(),
            'state': pstat.gen.state.decode(),
            'real_uid': pstat.gen.ruid,
            'real_gid': pstat.gen.rgid,
            'tgid': pstat.gen.pid,  # This is a duplicate of pid per atop documentation.
            'threads': pstat.gen.nthr,
            'exit_code': pstat.gen.excode,
            'start_time': pstat.gen.btime,
            'cmd': pstat.gen.cmdline.decode(),
            'ppid': pstat.gen.ppid,
            'running_threads': pstat.gen.nthrrun,
            'sleeping_threads': pstat.gen.nthrslpi,
            'dead_threads': pstat.gen.nthrslpu,
            'effective_uid': pstat.gen.euid,
            'effective_gid': pstat.gen.egid,
            'saved_uid': pstat.gen.suid,
            'saved_gid': pstat.gen.sgid,
            'filesystem_uid': pstat.gen.fsuid,
            'filesystem_gid': pstat.gen.fsgid,
            'elapsed_time': pstat.gen.elaps,
        }
        yield values


def parse_PRM(
        header: atop_structs.Header,
        record: atop_structs.Record,
        sstat: atop_structs.SStat,
        pstats: List[atop_structs.PStat],
) -> dict:
    """Retrieves statistics for Atop 'PRM' parseable representing process memory usage."""
    for pstat in pstats:
        values = {
            'timestamp': record.curtime,
            'interval': record.interval,
            'pid': pstat.gen.pid,
            'name': pstat.gen.name.decode(),
            'state': pstat.gen.state.decode(),
            'page': header.pagesize,
            'vsize': pstat.mem.vmem * 1024,
            'rsize': pstat.mem.rmem * 1024,
            'ssize': pstat.mem.shtext * 1024,
            'vgrowth': pstat.mem.vgrow * 1024,
            'rgrowth': pstat.mem.rgrow * 1024,
            'minor_faults': pstat.mem.minflt,
            'major_faults': pstat.mem.majflt,
        }
        yield values


def parse_PRN(
        header: atop_structs.Header,
        record: atop_structs.Record,
        sstat: atop_structs.SStat,
        pstats: List[atop_structs.PStat],
) -> dict:
    """Retrieves statistics for Atop 'PRN' parseable representing process network activity."""
    for pstat in pstats:
        values = {
            'timestamp': record.curtime,
            'interval': record.interval,
            'pid': pstat.gen.pid,
            'name': pstat.gen.name.decode(),
            'state': pstat.gen.state.decode(),
            'kernel_patch': 'y' if header.supportflags & atop_structs.PATCHSTAT else 'n',
            'tcp_transmitted': pstat.net.tcpsnd,
            'tcp_transmitted_size': pstat.net.tcpssz,
            'tcp_received': pstat.net.tcprcv,
            'tcp_received_size': pstat.net.tcprsz,
            'udp_transmitted': pstat.net.udpsnd,
            'udp_transmitted_size': pstat.net.udpssz,
            'udp_received': pstat.net.udprcv,
            'udp_received_size': pstat.net.udprsz,
            'raw_transmitted': pstat.net.rawsnd,
            'raw_received': pstat.net.rawrcv,
        }
        yield values


def parse_SWP(
        header: atop_structs.Header,
        record: atop_structs.Record,
        sstat: atop_structs.SStat,
        pstats: List[atop_structs.PStat],
) -> dict:
    """Retrieves statistics for Atop 'SWP' parseable representing swap space usage."""
    values = {
        'timestamp': record.curtime,
        'interval': record.interval,
        'page_size': header.pagesize,
        'swap': sstat.mem.totswap,
        'free_swap': sstat.mem.freeswap,
        'committed_space': sstat.mem.committed,
        'committed_limit': sstat.mem.commitlim,
    }
    yield values
