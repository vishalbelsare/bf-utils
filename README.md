# bf-utils
Blackfynn Utilities for dealing with the Datasets from the Linux command line
### bfcompare.py
bfcompare shows the differences between two datasets or a dataset and a local directory that was created with bfsync.
    bfcompare -d <dataset>
          -c <compared dataset>
          --all (compare with all datasets)
          -p <local path to compare>
          -i (case-insensitive compares)
          --data (also compare data)

          -h (help)
          -l (list datasets)

Note: -c, -p and --all are mutually exclusive.
### bfdelete.py
bfdelete removes directories (collections) from a dataset 
### bfdu.sh
bfdu will give an accurate size of data in a local directory
### bfduplicate.py
bfduplicate clones a dataset to a new dataset (collections only)
### bfinsert.py
bfinsert adds a new collection to a dataset's path
### bfmeta.py
bfmeta will add, remove or show metadata in collections and data in a dataset
### bfmove.py
bfmove will move a collection (and its contents) to another path within a dataset
### bfrename.py
bfrename will rename a collection in a dataset
### bfsync.py
bfsync will clone a dataset to a local directory (including data if requested)
### bftree.py
bftree shows the content of a dataset in tree format
## Note:
Each command comes with a -h option for help and a -l option to list all datasets available to the user
