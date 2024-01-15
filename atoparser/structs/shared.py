"""Shared structs and definitions used serialize/deserialize Atop data directly from log files.

Structs are declared in a way that will help provide as close to a 1 to 1 match as possible for debuggability
and maintenance. The _fields_ of every struct match their original name, however the struct names have been updated
to match python CamelCase standards. Each struct includes the following to help identify the original source:
    C Name: utsname
    C Location: sys/utsname.h
"""

import ctypes

# Disable the following pylint warnings to allow the variables and classes to match the style from the C.
# This helps with maintainability and cross-referencing.
# pylint: disable=invalid-name

# Definitions from time.h
time_t = ctypes.c_long

# Definitions from atop.h
count_t = ctypes.c_longlong

# Definitions from sys/types.h
off_t = ctypes.c_long


class HeaderMixin:
    """Shared logic for top level struct describing information contained in the log file.

    Attributes:
        supported_version: The version of Atop that this header is compatible with as <major.<minor>.
    """

    supported_version = None

    @property
    def semantic_version(self) -> str:
        """Convert the raw version into a semantic version.

        Returns:
            The final major.minor version from the header aversion.
                Atop releases have "maintenance" versions, but they do not impact the header or file structure.
                i.e., 2.3.1 is the same as 2.3.
        """
        # Use a general getattr() call to ensure the instance can always set the attribute even on first call.
        # C structs have various ways of creating instances, so __init__ is not always called to set up attributes.
        if not getattr(self, "_version", None):
            major = (self.aversion >> 8) & 0x7F
            minor = self.aversion & 0xFF
            self._version = f"{major}.{minor}"  # pylint: disable=attribute-defined-outside-init
        return self._version


class UTSName(ctypes.Structure):
    """Struct to describe basic system information.

    C Name: utsname
    C Location: sys/utsname.h
    """

    _fields_ = [
        # Standard GNU length is 64 characters + null terminator
        ("sysname", ctypes.c_char * 65),
        ("nodename", ctypes.c_char * 65),
        ("release", ctypes.c_char * 65),
        ("version", ctypes.c_char * 65),
        ("machine", ctypes.c_char * 65),
        ("domain", ctypes.c_char * 65),
    ]
