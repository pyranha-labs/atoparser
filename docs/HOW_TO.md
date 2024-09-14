# How Tos

Advanced guides for working with Atoparser. For basic guides, refer to the [README](../README.md).


## Table Of Contents

  * [Add a new version](#add-a-new-version)

### Add a new version

1. Copy the previous struct definition in `atoparser/atop_structs/` to a new file by the `<major>_<minor>` version.

1. Update any individual struct definitions as needed. Additional guidelines for this process outlined in the files.

1. Update the `atoparser/utils.py` file to include the new version in the imports and `_VERSIONS` list.

1. Use the `utils/build_atop.sh` script to generate a new sample Atop log file, and place in `atoparser/test/files/`.

1. Compress the new log with `gzip` to reduce storage overhead.

1. Add new tests to `atoparser/test/test_atoparser.py` to ensure the new version is parsed correctly.

1. Update the `README.md` file to include the new supported version.
