# migrate

## Overview

The [migrate.py](migrate.py) python script has a number of subcommands
for performing Senzing migration tasks.

To see all of the subcommands, run

```console
$ ./migrate.py -h
usage: migrate.py [-h]
                  {add-dscr-etype,json-add-keys,json-add-list-elements,json-pretty-print,migrate-g2config,migrate-opt-senzing}
                  ...

Migrate Senzing configuration

positional arguments:
  {add-dscr-etype,json-add-keys,json-add-list-elements,json-pretty-print,migrate-g2config,migrate-opt-senzing}
                        Subcommands:
    add-dscr-etype      Add existing G2_CONFIG.CFG_DSCR and
                        G2_CONFIG.CFG_ETYPE to a new g2config.json template
    json-add-keys       Add missing JSON keys to a JSON file from a JSON
                        template file
    json-add-list-elements
                        Add elements to existing lists
    json-pretty-print   Sort and pretty print a file of JSON
    migrate-g2config    Migrate g2config.json
    migrate-opt-senzing
                        Migrate /opt/senzing directory by creating a proposal

optional arguments:
  -h, --help            show this help message and exit
```

To see the options for a subcommand, run commands like:

```console
migrate.py json-pretty-print -h
```

### Contents

1. [Sub-command details](#sub-command-details)
    1. [add-descr-etype](#add-descr-etype)
    1. [json-add-keys](#json-add-keys)
    1. [json-add-list-elements](#json-add-list-elements)
    1. [json-pretty-print](#json-pretty-print)
    1. [migrate-g2config](#migrate-g2config)
    1. [migrate-opt-senzing](#migrate-opt-senzing)

## Sub-command details

### add-descr-etype

1. Example invocation

    ```console
    migrate.py add-dscr-etype \
      --existing-g2config-file /opt/senzing/g2/python/g2config.json \
      --template-g2config-file /opt/senzing/g2/data/g2config.json
    ```

1. What does it do?
    1. Start with the template file contents.
    1. Add in the `G2_CONFIG.CFG_DSRC` and `G2_CONFIG.CFG_ETYPE` from the existing file contents.

### json-add-keys

1. Example invocation

    ```console
    migrate.py json-add-keys \
      --existing-file /opt/senzing/g2/python/g2config.json \
      --template-file /opt/senzing/g2/data/g2config.json
    ```

1. What does it do?
    1. Start with the existing file contents.
    1. Add JSON key/value pairs that are in the template file, but not in the existing file.
    1. Values that are in the existing file are *not* overwritten.

### json-add-list-elements

1. Example invocation

    ```console
    migrate.py json-add-list-elements \
      --existing-file /opt/senzing/g2/python/g2config.json \
      --template-file /opt/senzing/g2/data/g2config.json
    ```

1. What does it do?
    1. Start with the existing file contents.
    1. Add new list elements from the template file into the existing file.
    1. List elements in the existing file are *not* overwritten.

### json-pretty-print

1. Example invocation

    ```console
    migrate.py json-pretty-print \
      --input-file /opt/senzing/g2/python/g2config.json
    ```

1. What does it do?
    1. Reorganize the JSON keys into alphabetical order.
    1. Add indentation.

### migrate-g2config

1. Example invocation

    ```console
    migrate.py migrate-g2config \
      --existing-g2config-file /opt/senzing/g2/python/g2config.json \
      --template-g2config-file /opt/senzing/g2/data/g2config.json
    ```

1. What does it do?
    1. Start with the existing file contents.
    1. Add JSON key/value pairs that are in the template file, but not in the existing file.
    1. Add new elements to existing lists.
    1. Values that are in the existing file are *not* overwritten.

### migrate-opt-senzing

1. Example invocation

    ```console
    migrate.py migrate-opt-senzing \
      --old-opt-senzing /opt/senzing-old \
      --new-opt-senzing /opt/senzing-new
    ```

1. What does it do?
    1. Log differences between old and new /opt/senzing directories.
        1. Detects removed, added, and changed files.
    1. Log files to be copied from old /opt/senzing directory.
    1. Log files to be created by synthesizing content from old and new /opt/senzing directories.
    1. Create a directory of "proposed" changes.
        1. These are proposed changes to the new /opt/senzing directory.
        1. Contents of the new /opt/senzing directory is *not* changed.
    1. Contents of the old /opt/senzing directory is *not* changed.
    1. The location of the proposed changes is seen in the log.

    ```console
    YYYY-MM-DD HH:MM:SS,sss INFO: migrate.py migrate-opt-senzing output: /path/to/proposed-opt-senzing-nnnnnnnnnn
    ```
