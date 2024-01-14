"""Structs and definitions used serialize/deserialize Atop statistics directly from log files.

Structs are declared in a way that will help provide as close to a 1 to 1 match as possible for debuggability
and maintenance. The _fields_ of every struct match their original name, however the struct names have been updated
to match python CamelCase standards. Each struct includes the following to help identify the original source:
    C Name: utsname
    C Location: sys/utsname.h

Struct ordering matches the C source to help with comparisons.
If structs match exactly from a previous version, they are reused via aliasing.

See https://github.com/Atoptool/atop for more information and full details about each field.
Using schemas and structs from Atop 2.5.0.
"""

import ctypes

from pyatop.structs import atop_1_26
from pyatop.structs import atop_2_3
from pyatop.structs import atop_2_4

# Disable the following pylint warnings to allow the variables and classes to match the style from the C.
# This helps with maintainability and cross-referencing.
# pylint: disable=invalid-name,too-few-public-methods

# Definitions from atop.h
ACCTACTIVE = 0x00000001
IOSTAT = 0x00000004
NETATOP = 0x00000010
NETATOPD = 0x00000020
DOCKSTAT = 0x00000040
GPUSTAT = 0x00000080

# Definitions from photoproc.h
PNAMLEN = 15
CMDLEN = 255

# Definitions from photosyst.h
MAXCPU = 2048
MAXDSK = 1024
MAXLVM = 2048
MAXMDD = 256
MAXINTF = 128
MAXCONTAINER = 128
MAXNFSMOUNT = 64
MAXIBPORT = 32
MAXGPU = 32
MAXGPUBUS = 12
MAXGPUTYPE = 12
MAXDKNAM = 32
MAXIBNAME = 12


class Header(atop_2_3.Header):
    """Top level struct to describe information about the system running ATOP and the log file itself."""

    supported_version = "2.5"

    def check_compatibility(self) -> None:
        """Verify if the loaded values are compatible with this header version."""
        sizes = [
            (self.rawheadlen, ctypes.sizeof(Header)),
            (self.rawreclen, ctypes.sizeof(Record)),
            (self.sstatlen, ctypes.sizeof(SStat)),
            (self.tstatlen, ctypes.sizeof(TStat)),
        ]
        if any(size[0] != size[1] for size in sizes):
            raise ValueError(f"File has incompatible Atop format. Struct length evaluations (found, expected): {sizes}")


Record = atop_2_3.Record


MemStat = atop_2_3.MemStat


FreqCnt = atop_1_26.FreqCnt


PerCPU = atop_2_3.PerCPU


CPUStat = atop_2_3.CPUStat


PerDSK = atop_2_3.PerDSK


DSKStat = atop_2_3.DSKStat


PerIntf = atop_2_3.PerIntf


IntfStat = atop_2_3.IntfStat


PerNFSMount = atop_2_3.PerNFSMount


Server = atop_2_3.Server


Client = atop_2_3.Client


NFSMounts = atop_2_3.NFSMounts


NFSStat = atop_2_3.NFSStat


PSI = atop_2_4.PSI


Pressure = atop_2_4.Pressure


PerContainer = atop_2_3.PerContainer


ContStat = atop_2_3.ContStat


WWWStat = atop_1_26.WWWStat


PerGPU = atop_2_4.PerGPU


GPUStat = atop_2_4.GPUStat


PerIFB = atop_2_4.PerIFB


IFBStat = atop_2_4.IFBStat


IPv4Stats = atop_1_26.IPv4Stats


ICMPv4Stats = atop_1_26.ICMPv4Stats


UDPv4Stats = atop_1_26.UDPv4Stats


TCPStats = atop_1_26.TCPStats


IPv6Stats = atop_1_26.IPv6Stats


ICMPv6Stats = atop_1_26.ICMPv6Stats


UDPv6Stats = atop_1_26.UDPv6Stats


NETStat = atop_1_26.NETStat


SStat = atop_2_4.SStat


GEN = atop_2_3.GEN


CPU = atop_1_26.CPU


DSK = atop_1_26.DSK


MEM = atop_2_3.MEM


NET = atop_2_3.NET


GPU = atop_2_4.GPU


TStat = atop_2_4.TStat
