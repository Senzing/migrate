# migrate

## Overview

The [migrate.py](migrate.py) python script has a number of subcommands
for performing Senzing migration tasks.

To see all of the subcommands, run

```console
$ ./migrate.py -h

usage: migrate.py [-h]
                  {add-dscr-etype,json-add-keys,json-add-list-elements,json-pretty-print,migrate-g2config,migrate-senzing-dir}
                  ...

Migrate Senzing configuration

positional arguments:
  {add-dscr-etype,json-add-keys,json-add-list-elements,json-pretty-print,migrate-g2config,migrate-senzing-dir}
                        Subcommands:
    add-dscr-etype      Add existing G2_CONFIG.CFG_DSCR and
                        G2_CONFIG.CFG_ETYPE to a new g2config.json template
    json-add-keys       Add missing JSON keys to a JSON file from a JSON
                        template file
    json-add-list-elements
                        Add elements to existing lists
    json-pretty-print   Sort and pretty print a file of JSON
    migrate-g2config    Migrate g2config.json
    migrate-senzing-dir
                        Migrate /opt/senzing directory by creating a proposal

optional arguments:
  -h, --help            show this help message and exit
```

To see the options for a subcommand, run commands like:

```console
migrate.py json-pretty-print -h
```

### Contents

1. [Use cases](#use-cases)
    1. [Download migrate.py](#download-migratepy)
    1. [Migrating to a new Senzing_API.tgz](#migrating-to-a-new-senzing_apitgz)
1. [Sub-command details](#sub-command-details)
    1. [add-descr-etype](#add-descr-etype)
    1. [json-add-keys](#json-add-keys)
    1. [json-add-list-elements](#json-add-list-elements)
    1. [json-pretty-print](#json-pretty-print)
    1. [migrate-g2config](#migrate-g2config)
    1. [migrate-senzing-dir](#migrate-senzing-dir)

## Use cases

### Download migrate.py

1. Download [migrate.py](https://raw.githubusercontent.com/Senzing/migrate/master/migrate.py).

    ```console
    curl -X GET \
      --output migrate.py \
      https://raw.githubusercontent.com/Senzing/migrate/master/migrate.py
    ```

1. Make `migrate.py` executable.

    ```console
    chmod +x migrate.py
    ```

1. Test `migrate.py`.

    ```console
    ./migrate.py -h
    ```

### Migrating to a new Senzing_API.tgz

This use case shows how to apply the contents of a new version of 
Senzing_API.tgz to an existing `/opt/senzing` Senzing directory.

#### Create NEW_SENZING_DIR

1. Download [Senzing_API.tgz](https://s3.amazonaws.com/public-read-access/SenzingComDownloads/Senzing_API.tgz).

    ```console
    curl -X GET \
      --output /tmp/Senzing_API.tgz \
      https://s3.amazonaws.com/public-read-access/SenzingComDownloads/Senzing_API.tgz
    ```

1. Set environment variable.

    ```console
    export NEW_SENZING_DIR=/opt/senzing.$(date +%s)
    ```

1. Extract [Senzing_API.tgz](https://s3.amazonaws.com/public-read-access/SenzingComDownloads/Senzing_API.tgz)
   to `${NEW_SENZING_DIR}`.

    1. Linux

        ```console
        sudo mkdir -p ${NEW_SENZING_DIR}

        sudo tar \
          --extract \
          --owner=root \
          --group=root \
          --no-same-owner \
          --no-same-permissions \
          --directory=${NEW_SENZING_DIR} \
          --file=/tmp/Senzing_API.tgz
        ```

    1. macOS
        ```console
        sudo mkdir -p ${NEW_SENZING_DIR}

        sudo tar \
          --extract \
          --no-same-owner \
          --no-same-permissions \
          --directory=${NEW_SENZING_DIR} \
          --file=/tmp/Senzing_API.tgz
        ```

#### Identify OLD_SENZING_DIR

1. Determine where Senzing_API.tgz was last installed.
   By convention, it is usually at `/opt/senzing`.
1. Set environment variable.

    ```console
    export OLD_SENZING_DIR=/opt/senzing
    ```

#### Create a migration proposal

1. **Note:** This step will *not* modify either the `$OLD_SENZING_DIR` or the `$NEW_SENZING_DIR` directories.
1. Create the proposal.

    ```console
    ./migrate.py migrate-senzing-dir \
        --old-senzing-dir ${OLD_SENZING_DIR} \
        --new-senzing-dir ${NEW_SENZING_DIR}
    ```

1. The location of the proposal will be in the log output.  Example:

    ```console
    YYYY-MM-DD HH:MM:SS,sss INFO: migrate.py migrate-senzing-dir output: /path/to/senzing-proposal-nnnnnnnnnn
    ```

1. The log output will also show:
    1. Files only in the ${OLD_SENZING_DIR}. They are prefixed with `INFO: old-only:`
    1. Files only in the ${NEW_SENZING_DIR}. They are prefixed with `INFO: new-only:`
    1. Files which have changed.  They are prefixed with `INFO: changed:`
    1. Files in the proposal. They are prefixed with `INFO: copy-file:` and `INFO: make-file:`.

1. To see the proposal, look in the `/path/to/senzing-proposal-nnnnnnnnnn` directory.  Example:

    ```console
    $ cd /path/to/senzing-proposal-nnnnnnnnnn

    $ tree
    .
    └── g2
        ├── data
        │   └── g2.lic
        └── python
            ├── demo
            │   └── my-test.py
            ├── g2config.json
            ├── G2Module.ini
            └── G2Project.ini
    ```

    To install `tree`, run `sudo yum install tree` or `sudo apt-get install tree`.

1. The proposal directory contains only the files that need to be applied to the $NEW_SENZING_DIR.

#### Apply proposal

1. Identify PROPOSED_SENZING_DIR.  From the `migrate.py` log, find the line with the proposal directory.

    ```console
    YYYY-MM-DD HH:MM:SS,sss INFO: migrate.py migrate-opt-senzing output: /path/to/senzing-proposal-nnnnnnnnnn
    ```

1. Set environment variable.

    ```console
    export PROPOSED_SENZING_DIR=/path/to/senzing-proposal-nnnnnnnnnn
    ```

1. Copy proposal into NEW_SENZING_DIR.

    ```console
    cp -r ${PROPOSED_SENZING_DIR}/* ${NEW_SENZING_DIR}
    ```  

    An alternative is to pick-and-choose the files to be copied individually.  

#### Switch directories

1. **Note:** This set of steps changes the configuration for Senzing.

1. Verify Senzing processes are not running.

    ```console
    ???
    ```

1. Rename old Senzing directory.

    ```console
    mv ${OLD_SENZING_DIR} ${OLD_SENZING_DIR}.$(date +%s)
    ```

1. Rename the new Senzing Directory to be the name of the "original" Senzing directory.

    ```console
    mv ${NEW_SENZING_DIR} ${OLD_SENZING_DIR}
    ```

## Sub-command details

### add-descr-etype

1. Example invocation.

    ```console
    migrate.py add-dscr-etype \
      --existing-g2config-file /opt/senzing/g2/python/g2config.json \
      --template-g2config-file /opt/senzing/g2/data/g2config.json
    ```

1. What does it do?
    1. Start with the template file contents.
    1. Add in the `G2_CONFIG.CFG_DSRC` and `G2_CONFIG.CFG_ETYPE` from the existing file contents.

### json-add-keys

1. Example invocation.

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

1. Example invocation.

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

1. Example invocation.

    ```console
    migrate.py json-pretty-print \
      --input-file /opt/senzing/g2/python/g2config.json
    ```

1. What does it do?
    1. Reorganize the JSON keys into alphabetical order.
    1. Add indentation.

### migrate-g2config

1. Example invocation.

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

### migrate-senzing-dir

1. Example invocation.

    ```console
    migrate.py migrate-senzing-dir \
      --old-senzing-dir /opt/senzing-old \
      --new-senzing-dir /opt/senzing-new
    ```

1. What does it do?
    1. Log differences between old and new "/opt/senzing" directories.
        1. Detects removed, added, and changed files.
    1. Log files to be copied from old directory.
    1. Log files to be created by synthesizing content from old and new directories.
    1. Create a directory of "proposed" changes.
        1. These are proposed changes to the new directory.
        1. Contents of the new directory is *not* changed.
    1. Contents of the old directory is *not* changed.
    1. The location of the proposed changes is seen in the log.

        ```console
        YYYY-MM-DD HH:MM:SS,sss INFO: migrate.py migrate-senzing-dir output: /path/to/senzing-proposal-nnnnnnnnnn
        ```
