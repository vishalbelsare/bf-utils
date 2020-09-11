# bf-utils
Blackfynn Utilities for dealing with the Datasets from the Linux command line

## Prerequisites
```
Python 2.7.10+ and packages
    blackfynn
    datetime
    getopt
    os
    requests
    shutil
    sys
    termcolor
    time
    urllib3

Python 3.7 and packages
    blackfynn
    pandas
```

## Note:
1. Each command comes with a -h option for help and a -l option to list all datasets available to the user
2. Package installation:
     * [Blackfynn client](https://developer.blackfynn.io/python/latest/quickstart.html#installation)
     * [pandas](https://pandas.pydata.org/pandas-docs/stable/getting_started/install.html)
3. We are in the process of switching to Python3.7. The following scripts work for 3.7.
     * bfsync.py

### bfcompare.py
bfcompare shows the differences between two datasets or a dataset and a local directory that was created with bfsync.
```
bfcompare -d <dataset>
          -c <compared dataset>
          --all (compare with all datasets)
          -p <local path to compare>
          -i (case-insensitive compares)
          --data (also compare data)

          -h (help)
          -l (list datasets)

Note: -c, -p and --all are mutually exclusive.
```
### bfdelete.py
bfdelete removes directories (collections) from a dataset 
```
bfdelete -d <dataset>
         --all (apply to ALL HPAP datasets)
         -f <file containing datasets>
         -p <dataset path> (removes rightmost item in path)
         --force (remove collection with content)

         -h (help)
         -l (list datasets)

Note: -d, -f and --all are mutually exclusive
```
### bfdircnt.py
bfdircnt will provide directory/file counts of directories in a tree.  Each
count is the total of directores, subdirectories and files in a directory.
```
bfdircnt <directory>
```
### bfdu.sh
bfdu will give an accurate size of data in a local directory
```
Syntax: bfdu <directory>
```
### bfduplicate.py
bfduplicate clones a dataset to a new dataset (collections only)
```
bfduplicate.py -d <dataset>
               -n <new dataset>

               -h (help)
               -l (list datasets)
```
### bfinsert.py
bfinsert adds a new collection to a dataset's path
```
bfinsert -d <dataset
         --all (apply to ALL HPAP datasets)
         -f <file containing datasets>
         -p <dataset path> (inserts rightmost part of path)

         -h (help)
         -l (list datasets)

Note: -d, -f and --all are mutually exclusive.
```
### bfmeta.py
bfmeta will add, remove or show metadata in collections and data in a dataset
```
bfmeta -d <dataset>
       --all (apply to ALL HPAP datasets)
       -f <file containing datasets>
       -k <metadata key>
       -v <metadata value>
       -m <metadata file of key:value pairs> (-k -v ignored)
       -c <category> (default = Blackfynn)
       -p <dataset path> (path to collection required)
       -t <data type> (integer, string, date, double)
       --remove (remove metadata instead of adding metadata)
       --show (show metadata)

       -h (help)
       -l (list datasets)

Notes: Adds, removes, or shows metadata to right part of path
       Date format = "MM/DD/YYYY HH:MM:SS"
       Options -d, -f and --all are mutually exclusive
```
### bfmove.py
bfmove will move a collection (and its contents) to another path within a dataset
```
bfmove -d <dataset>
       --all (loop on all HPAP datasets)
       -f <file containing datasets>
       -S <source path>
       -D <destination path> (MUST be directory)

       -h (help)
       -l (list datasets)

Note: -d, -f and --all are mutually exlusive
```
### bfrename.py
bfrename will rename a collection in a dataset
```
bfrename -d <dataset>
         --all (apply to ALL HPAP datasets)
         -f <file containing datasets>
         -p <dataset path> (renames rightmost object in path)
         -n <new object name>
         --data (rightmost object is data)

         -h (help)
         -l (list datasets)

Note: -d, -f and --all are mutually exlusive
```
### bfsync.py
bfsync will clone a dataset to a local directory (including data if requested)
```
bfsync -d <dataset>
       -c <data category, e.g. "Clinical data", "B cell receptor repertoire", "Flow panels for B cells",
    "Flow cytometry - Immune lineage", "Histology", "CyTOF", "ATACseq",
    "mRNAseq", "Sequencing data for sorted cells/Sort data", "WGBS", "Single-cell RNAseq", "Calcium imaging",
    "Patch-Clamp", "Oxygen consumption", "Morphology and viability", "Perifusions",
    "Imaging mass cytometry", "ATAQseq", "Tetramer Ag specific studies by FACS">
       -p <output path for local dataset storage> (default is $PWD)
       -e <file containing exception paths>
       --nodata (do not include data)
       --mirror (remove local data/directories to mirror dataset)
       --refresh (send a signal to hpap data website to refresh. this is the default)
       --norefresh (do not send signal to hpap data website to refresh)
       
       -h (help)
       -l (list datasets)
```

*Data Download* (**This should only be used by HPAP groups because of the Blackfynn license limit**)
1. Share [bfsync.py](bfsync.py) and [this instruction file](DataDownload.txt)
2. The instruction file contains Blackfynn API token and secret for account ibihpap@gmail.com. 

### bftree.py
bftree shows the content of a dataset in tree format
```
bftree -d <dataset>
       --all (loop on all HPAP datasets)
       -p <path to start tree>
       --data (show packages in output)
       --realdata (show packages as uploaded names)
       --nocolor (no colorful output)

       -h (help)
       -l (list datasets)

Note: -d and --all are mutually exclusive
```

