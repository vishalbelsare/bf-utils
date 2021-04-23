# bf-utils
Pennsieve Utilities for dealing with the Datasets from the Linux command line

## Prerequisites
```
Python 2.7.10+ and packages
    datetime
    getopt
    os
    requests
    shutil
    sys
    numpy>=1.15.1
    termcolor>=1.1.0
    time
    urllib3

Python 3.7 and packages
    [pennsieve client](https://github.com/Pennsieve/pennsieve-python)
    [pandas](https://pandas.pydata.org/pandas-docs/stable/getting_started/install.html)
```

## Note:
1. Each command comes with a -h option for help and a -l option to list all datasets available to the user
2. We are in the process of switching to Python3.7. The following scripts work for 3.7.
     * bfsync.py
3. Legacy [data upload](/upload_legacy) instructions

## Data download for HPAP groups 
**NOTE: we encourage HPAP groups to use [FTP downloading](https://hpap.pmacs.upenn.edu/explore/ftp) too.**
1. Install Python 3.7 or above (https://www.python.org/downloads/)
2. Install Python packages
     - Pandas https://pandas.pydata.org/pandas-docs/stable/getting_started/install.html
     - Pennsieve client 
         * After [pennsieve installation](https://docs.pennsieve.io/docs/the-pennsieve-agent), set [configuration](https://docs.pennsieve.io/docs/configuring-the-client-credentials)
         * API token: [To Be Set]
         * API secret: [To Be Set]
3. Download data
     - Command: python bfsync.py [options, or -h for help]
     - Data categories: "Clinical data", "B cell receptor repertoire", "Flow panels for B cells", "Flow cytometry - Immune lineage", "Histology", "CyTOF", "ATACseq", "mRNAseq", "Sequencing data for sorted cells/Sort data", "WGBS", "Single-cell RNAseq", "Calcium imaging", "Patch-Clamp", "Oxygen consumption", "Morphology and viability", "Perifusions", "Imaging mass cytometry", "ATAQseq", "Tetramer Ag specific studies by FACS".
     - For example, to download scRNAseq data for donor HPAP-008, the command is:     
         `python bfsync.py -d "HPAP-008" -c "Single-cell RNAseq" `

## Scripts
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
       -c <category> (default = Pennsieve)
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
       -c <Data categories: "Clinical data", "B cell receptor repertoire", "Flow panels for B cells", "Flow cytometry - Immune lineage", "Histology", "CyTOF", "ATACseq", "mRNAseq", "Sequencing data for sorted cells/Sort data", "WGBS", "Single-cell RNAseq", "Calcium imaging", "Patch-Clamp", "Oxygen consumption", "Morphology and viability", "Perifusions", "Imaging mass cytometry", "ATAQseq", "Tetramer Ag specific studies by FACS".>
       -p <output path for local dataset storage> (default is $PWD)
       -e <file containing exception paths>
       --nodata (do not include data)
       --mirror (remove local data/directories to mirror dataset)
       --refresh (send a signal to hpap data website to refresh. this is the default)
       --norefresh (do not send signal to hpap data website to refresh)
       
       -h (help)
       -l (list datasets)
```

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

