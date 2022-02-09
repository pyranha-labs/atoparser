# PyAtop

PyAtop is a native python ATOP log processing library. The library supports reading the binary C structs directly from
saved ATOP log files, without the need to call a subprocess, or even install ATOP. The converted data contains
structured python objects, that can then be used for JSON, CSV, or other types of output, storage, and analysis.

For full information on the amazing performance monitoring software that creates these files, known as ATOP, refer to:  
[ATOP - The one stop shop for all your tops](https://www.atoptool.nl/)


## Examples

Read an ATOP log with the example JSON command:
```
pyatop ~/atop.log -P CPU --pretty
```

Iterate over the C structs as Python objects:  
```
with gzip.open(file, 'rb') as raw_file:
    header = atop_helpers.get_header(raw_file)
    for record, sstat, tstat in atop_helpers.generate_statistics(raw_file, header):
        total_cycles = record.interval * sstat.cpu.nrcpu * header.hertz
        usage = 1 - sstat.cpu.all.itime / total_cycles
        print(f'CPU usage was {usage:.02%}')
```

## Limitations
- Supports ATOP 1.26 and 2.30, but may work with other versions.
