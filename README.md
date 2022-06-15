# pennsieve-utils

This repository includes some scripts that can process Pennsieve datasets on
Linux command line.

## Prerequisites:

1. Python 3.7+

2. Packages in `requirements.txt`, which can be installed by:
   ```
   pip install -r requirements.txt
   ```

## Installation:

To install these scripts, run the following command:

```shell
./install.sh <installation_dir>
```

If `<installation_dir>` is not specified, they will be installed in `$HOME/bin`.
Please also make sure that `<installation_dir>` is in your shell's `$PATH`.
For example, If you are using bash, add this line at the end of your `.bashrc`:

```shell
export PATH=<installation_dir>:$PATH
```

## Data Download for HPAP Groups:

1. Install Python 3.7 or above (https://www.python.org/downloads/)

2. Install Python packages: `pip install -r requirements.txt`

3. Configure Pennsieve client: follow the steps in
   [Pennsive client credentials](https://docs.pennsieve.io/docs/configuring-the-client-credentials)
   to set API key/secret pair to access Pennsieve.

4. Download data: use `py-sync.py` command, which supports the following
   data categories:
     * `Clinical data`
     * `B cell receptor repertoire`
	 - `Flow panels for B cells`
	 - `Flow cytometry - Immune lineage`
     * `Histology`
	 - `CyTOF`
	 - `ATACseq`
	 - `mRNAseq`
     * `Sequencing data for sorted cells/Sort data`
	 - `WGBS`
     * `Single-cell RNAseq`
	 - `Calcium imaging`
	 - `Patch-Clamp`
     * `Oxygen consumption`
	 - `Morphology and viability`
	 - `Perifusions`
     * `Imaging mass cytometry`
	 - `ATAQseq`
     * `Tetramer Ag specific studies by FACS`

   For example, to download `scRNAseq` data for donor `HPAP-008`, use:
   ```
   psv-sync.py -d "HPAP-008" -c "Single-cell RNAseq"
   ```

You can also download data from the web UI at:
[FTP downloading](https://hpap.pmacs.upenn.edu/explore/ftp)


## Usage of Scripts:

Each script comes with a `-h` option for help.

### psv-compare.py
Show differences between two datasets or a dataset and a local directory
that was created with `psv-sync.py`.

```
psv-compare.py -h (help)
               -c <compared dataset>
               -p <local path to compare>
               --all (compare with all datasets)
               -d <dataset> (required)
               -i (optional, case-insensitive comparison)
               --data (optional, also compare data)

Note: `-c`, `-p` and `--all` are mutually exclusive.
```

### psv-delete.py
Remove directories (collections) from a dataset.

```
psv-delete.py -h (help)
              -p <path> (removes rightmost collection in path)
              -d <dataset>
              -f <file_containing_datasets>
              --all (apply to ALL HPAP datasets)
              --force (remove collection even if it's non-empty)"

Note: `-d`, `-f` and `--all` options are mutually exclusive.
```

### psv-du.sh
Print out the accurate size of data in a local directory.

```
psv-du.sh <directory>
```

### psv-duplicate.py
Clone an exsiting dataset to a new dataset (collections only).

```
psv-duplicate.py -h (help)
                 -d <original_dataset>
                 -n <new_dataset>
```

### psv-insert.py
Add a new collection to a dataset's path

```
psv-insert.py -h (help)
              -p <path> (insert rightmost part of path)
              -d <dataset>
              -f <file_containing_datasets>
              --all (apply to ALL HPAP datasets)

Note: `-d`, `-f` and `--all` options are mutually exclusive.
```

### psv-list.py
List all datasets that you can access on Pennsieve.

```
psv-list.py
```

### psv-meta.py
Add, remove or show metadata in collections and data in a dataset

```
psv-meta.py -h (help)
            -p <dataset path> (path to collection required)
            -d <dataset>
            -f <file containing datasets>
            --all (apply to ALL HPAP datasets)
            -k <metadata key>
            -v <metadata value>
            -m <metadata file of key:value pairs> (`-k` and `-v` will be ignored)
            -c <category> (default: 'Pennsieve')
            -t <data type> (integer, string, date, double)
            --show (show metadata)
            --remove (remove metadata)

Notes:
  * Add, remove, or show metadata to rightmost part of path;
  * Date format: "MM/DD/YYYY HH:MM:SS";
  * Options `-d`, `-f` and `--all` options are mutually exclusive.
```

### psv-move.py
Move a collection (and its contents) to another path within a dataset

```
psv-move.py -h (help)
            -d <dataset>
            -f <file_containing_datasets>
            --all (apply to all HPAP datasets)
            -S <source>
            -D <destination> (<destination> MUST be a directory)

Note: `-d`, `-f` and `--all` options are mutually exlusive.
```

### psv-rename.py
Rename a collection in dataset.

```
psv-rename.py -h (help)
              -p <path> (renames rightmost object in path)
              -d <dataset>
              -f <file_containing_datasets>
              --all (apply to ALL HPAP datasets)
              -n <new_name>
              --data (rightmost object is data)

Note: `-d`, `-f` and `--all` options are mutually exlusive.
```

### psv-sync.py
Synchronize Pennsieve dataset(s) with local directory.

```
psv-sync.py -h (help)
     	    -q (quick sync, check existence of file before downloading)
            -c <category>
            -d <dataset>
            -o <output_path_for_local_storage> (default is $PWD)
            -x <file_containing_excluded_paths>
            --all (apply to all HPAP datasets)
            --nodata (do not include data)
            --mirror (remove local data/directories to mirror dataset)
            --refresh (refresh HPAP website)

Note:
  * `-d` and `--all` options are mutually exclusive.
  * Categories supported by `-c` option are:
      - "ATACseq"
      - "B cell receptor repertoire"
      - "Calcium imaging"
      - "Clinical data"
      - "CyTOF"
      - "Flow panels for B cells"
      - "Flow cytometry - Immune lineage"
      - "Histology"
      - "Imaging mass cytometry"
      - "Morphology and viability"
      - "mRNAseq"
      - "Oxygen consumption"
      - "Patch-Clamp",
      - "Perifusions",
      - "Sequencing data for sorted cells/Sort data"
      - "Single-cell RNAseq"
      - "Tetramer Ag specific studies by FACS"
      - "WGBS"
```

### psv-tree.py
Show contents of a dataset in tree format.

```
psv-tree.py -h: (help)
            -d <dataset>: specify dataset
            --all: show all HPAP datasets
            -p <path_to_start_tree>: (optional) specify the path
            --data: (optional) show packages in output
            --realdata: (optional) show packages as uploaded names
            --nocolor: (optional) disable color in output

Note: `-d` and `--all` options are mutually exclusive.
```

### psv-upload.bash
Upload local data to Pennsieve server.

```
psv-upload.bash [local_data] [HPAP-###] [optional_destination]

Example #1: upload './my data' to the root folder of HPAP-001:
  psv-upload.bash './my data' HPAP-001

Example #2: upload './my data' to 'Histology/Bone Marrow' folder of HPAP-001:
  psv-upload.bash './my data' HPAP-001 'Histology/Bone Marrow'
```
