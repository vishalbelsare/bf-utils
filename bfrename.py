#!/usr/bin/env python 
#===============================================================================
#
#         FILE:  bfrename.py
#
#        USAGE:  ./bfrename {options}
#
#  DESCRIPTION:  Rename collection at the end of given path  
#
#      OPTIONS:  -p <dataset path to object to rename>
#                -n <new object name>
#                -d <dataset> (update single dataset)
#                --all (apply to all HPAP datasets)
#                --data (allow renaming of package)
#                -f <file> (use file containing datasets to update)
#                -l (list all datasets)
#                -h (help)
# REQUIREMENTS:  python2, pennsieve python library and license key
#      UPDATES:  171006: collection path can start with / or not
#                171113: renames collections only
#                180215: unified options
#                180322: added --data so packages can be renamed
#       AUTHOR:  Pete Schmitt (discovery), <pschmitt@upenn.edu>
#      COMPANY:  University of Pennsylvania
#      VERSION:  0.2.0
#      CREATED:  Fri Oct  6 13:36:33 EDT 2017
#     REVISION:  Thu Mar 22 15:10:46 EDT 2018
#===============================================================================
from pennsieve import Pennsieve
from pennsieve.models import BaseCollection
from pennsieve.models import Collection
import sys
import getopt
import os
###############################################################################
def syntax():
    SYNTAX =  "\nbfrename -d <dataset>\n"
    SYNTAX += "         --all (apply to ALL HPAP datasets)\n"
    SYNTAX += "         -f <file containing datasets>\n"
    SYNTAX += "         -p <dataset path> "
    SYNTAX += "(renames rightmost object in path)\n"
    SYNTAX += "         -n <new object name>\n"
    SYNTAX += "         --data (rightmost object is data)\n\n"
    SYNTAX += "         -h (help)\n"
    SYNTAX += "         -l (list datasets)\n\n"
    SYNTAX +=  "Note: -d, -f and --all are mutually exlusive\n"
    return SYNTAX
###############################################################################
def printf(format, *args):
    """ works just like the C/C++ printf function """
    sys.stdout.write(format % args)
    sys.stdout.flush()
###############################################################################
def ds_exists(dset,dsets):
    """ check if Dataset exists """
    for ds in dsets:
        if dset in ds[1]:
            return True
    return False
###############################################################################
def file_exists(filename):
    if os.path.exists(filename): return True
    return False
###############################################################################
def object_exists(ds,name):
    """ test if expected collection in path exists """
    for i in ds.items:
        if name == i.name: return True
    return False
###############################################################################
def get_datasets():
    """ return list of tuples with short and long dataset names 
        and dictionary of datasets with short name as key """
    dsets = list()
    dsdict = dict()
    ds = bf.datasets()
    for d in ds:
        if 'HPAP-' in d.name:
            tmp = d.name.split()
            dsdict[str(tmp[0])] = str(d.name)
            dsets.append((str(tmp[0]), str(d.name), d))
        else:
            dsdict[str(d.name)] = str(d.name)
            dsets.append((str(d.name), str(d.name), d))
            
    dsets.sort()
    return dsets, dsdict
###############################################################################
def rename_object(dset, path, newname, DATA):
    if newname == "": 
        printf("need new name for object at the end of path!")
        sys.exit()
    elif path == "": 
        printf("need path to rename!")
        sys.exit()

    # get to bottom collection in path
    ds = bf.get_dataset(dset)
    dirs = path.split('/')
    obj = dirs[-1]
    
    for i in range(len(dirs)): 
        if object_exists(ds,dirs[i]):
            ds = ds.get_items_by_name(dirs[i])[0]
        else:
            printf("Object, %s, does NOT exist.\n", dirs[i])
            printf("Input Path: %s\n", '/'.join(dirs))
            return
    
    # ensure object exists, is not a package, and rename it.
    
    if ":package:" in str(ds.id):
        if not DATA:
            printf("Trying to rename a data package, use --data\n")
        else:
            printf("Package, %s, renamed to %s within dataset %s.\n", 
                    obj, newname, dset)
            ds.name = newname
            ds.update()
    else:
        ds.name = newname
        ds.update()
        printf("Collection, %s, renamed to %s within dataset %s.\n", 
                obj, newname, dset)
    return
###############################################################################
# program starts HERE
bf = Pennsieve()  # use 'default' profile
ALL = False
FILE = False
DATASET = False
DATA = False

if len(sys.argv) < 2:
    printf("%s\n", syntax())
    sys.exit()
argv = sys.argv[1:]

#################
# resolve options
#################
try:
    opts, args = getopt.getopt(argv, "hln:p:d:f:", ['all','data'])
except getopt.GetoptError:
    printf("%s\n", syntax())
    sys.exit()

dsets, dsdict = get_datasets()

for opt, arg in opts:
    if opt in '-h':
        printf("%s\n", syntax())
        sys.exit()
    elif opt in '--all':
        hpap_dsets = list()
        ALL = True
        for ds in dsets:
            if 'HPAP-' in ds[0]: hpap_dsets.append(ds[2])
        hpap_dsets.sort(key = lambda x: x.name)
    elif opt in '-n':
        newname = arg
    elif opt in '-p':
        path = arg
    elif opt in '-l':
        for ds in dsets:
            printf("%s\n", ds[0])
        sys.exit()
    elif opt in '-d':
        DATASET = True
        if not ds_exists(arg, dsets):
            printf("Dataset, %s, does NOT exist.\n", arg)
            sys.exit()
        else:
            dset = dsdict[arg]
    elif opt in '-f':
        filename = arg
        FILE = True
        if not file_exists(filename):
            printf("file, %s, does NOT exist.\n", filename)
            sys.exit()
    elif opt in '--data':
        DATA = True
####################
# here we go
if FILE:
    with open(filename) as f:
        fdsets = f.read().splitlines()
    for dset in fdsets:
        if not ds_exists(dset,dsets):
            printf("dataset, %s, does not exist on server.\n", dset)
            sys.exit()
    for dset in fdsets:
        rename_object(dset, path, newname, DATA)

elif ALL:
    for dset in hpap_dsets:
        rename_object(dset.name, path, newname, DATA)

elif DATASET:
    rename_object(dset, path, newname, DATA)

