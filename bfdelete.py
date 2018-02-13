#!/usr/bin/env python 
#===============================================================================
#
#         FILE:  bfdelete.py
#
#        USAGE:  ./bfdelete -d <dataset> -c <collection> -p <path> 
#                           -l (list datasets)
#                           -h (help)
#
#  DESCRIPTION: Insert collection into given path  
#
#      OPTIONS:  -c <collection to delete> -p <dataset path> [-d | -a | -f] 
#                -d <dataset> (update single dataset)
#                -a (apply to all HPAP datasets)
#                -f <file> (use file containing datasets to update)
#                -l (list all datasets)
#                -h (help)
# REQUIREMENTS:  blackfynn python library and license key
#      UPDATES:  171006: collection path can start with / or not
#                171103: Added short name usage for HPAP datasets
#       AUTHOR:  Pete Schmitt (discovery), <pschmitt@upenn.edu>
#      COMPANY:  University of Pennsylvania
#      VERSION:  0.2.0
#      CREATED:  Fri Oct  6 13:36:33 EDT 2017
#     REVISION:  Fri Nov  3 13:52:37 EDT 2017
#===============================================================================
from blackfynn import Blackfynn
from blackfynn.models import BaseCollection
from blackfynn.models import Collection
import sys
import getopt
import os
###############################################################################
def syntax():
    SYNTAX =  "bfdelete -p <dataset path> "
    SYNTAX += "[-d | -a | -f] (removes rightmost collection in path)\n"
    SYNTAX += "         -d <dataset>\n"
    SYNTAX += "         -a (apply to ALL HPAP datasets)\n"
    SYNTAX += "         -f <file containing datasets>\n"
    SYNTAX += "         --force (remove collection with content)\n"
    SYNTAX += "\n"
    SYNTAX += "bfdelete -h (help)\n"
    SYNTAX += "bfdelete -l (list datasets)\n"
    SYNTAX += "\nNote: -d, -a and -f are mutually exclusive\n"
    return SYNTAX
###############################################################################
def printf(format, *args):
    """ works just like the C/C++ printf function """
    sys.stdout.write(format % args)
    sys.stdout.flush()
###############################################################################
def db_exists(dset,dsets):
    """ check if Dataset exists """
    if dset in dsets:
        return True
    else:
        return False
###############################################################################
def file_exists(filename):
    if os.path.exists(filename): return True
    return False
###############################################################################
def collection_exists(ds,name):
    """ test if expected collection in path exists """
    for i in ds.items:
        if name == i.name: return True
    return False
###############################################################################
def delete_collection(dset, collection, delete_from, FORCE):
    """ delete collection from dataset """
    if delete_from == "": 
        path = "root directory"
    else:
        path = delete_from

    # get to bottom collection in path
    ds = bf.get_dataset(dset)
    dirs = delete_from.split('/')
    
    for i in range(len(dirs)): 
        if dirs[i] == "": break  # add to root directory
        if collection_exists(ds,dirs[i]):
            ds = ds.get_items_by_name(dirs[i])[0]
        else:
            printf("Collection, %s, does NOT exist!\n", dirs[i])
            printf("%s\n", dirs)
            sys.exit()

    # ensure collection exists and delete it if it is empty or forced
    FOUND = False
    if len(ds.items) > 0:
        for item in ds.items:
            if collection in item.name:
                FOUND = True
                break
    if FOUND:
        if len(item.items) == 0:  
            item.delete()
            printf("Collection, %s, removed in \"%s\" within dataset %s\n",
                    collection, path, dset)
        elif FORCE == True:
            item.delete()
            printf("Collection, %s, not empty but removed with FORCE\n",
                    collection)
        else:
            printf("Collection, %s, not empty.\n", collection)
    else:
        printf("Path, %s/%s, not found within dataset %s\n", path, 
                collection, dset)

    return
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
# program starts HERE
bf = Blackfynn()  # use 'default' profile
ALL = False
FILE = False
DATASET = False
FORCE = False
if len(sys.argv) < 2:
    printf("%s\n",syntax())
    sys.exit()
argv = sys.argv[1:]

#################
# resolve options
#################
try:
    opts, args = getopt.getopt(argv, "Fhalp:d:f:",
          ['force', 'collection=', 'file=', 'help', \
           'list', 'path=', 'dataset=', 'all'])
except getopt.GetoptError:
    printf("%s\n",syntax())
    sys.exit()

dsets, dsdict = get_datasets()
bfdsets = list()
for ds in dsets: 
    bfdsets.append(dsdict[ds[0]])

for opt, arg in opts:
    if opt in ('-h', '--help'):
        printf("%s\n",syntax())
        sys.exit()
    elif opt in ('-a', '--all'):
        hpap_dsets = list()
        ALL = True
        for ds in dsets:
            if 'HPAP-' in ds[0]: hpap_dsets.append(ds[2])
        hpap_dsets.sort(key = lambda x: x.name)
    elif opt in ('-p', '--path'):
        delete_from = arg
        # remove leading / if it exists
        if delete_from[0] == '/': delete_from = delete_from[1:]
        pathlist = delete_from.split('/')
        collection = pathlist[-1]
        delete_from = '/'.join(pathlist[:-1])
    elif opt in ('-l', '--list'):
        for ds in dsets: 
            printf("%s\n", ds[0])
        sys.exit()
    elif opt in ('-d', '--dataset'):
        dset = dsdict[arg]
        DATASET = True
        if not db_exists(dset,bfdsets):
            printf("dataset, %s, does not exist on server.\n", dset)
            sys.exit()
    elif opt in ('-F', '--force'):
        FORCE = True
    elif opt in ('-f', '--file'):
        filename = arg
        FILE = True
        if not file_exists(filename):
            printf("file, %s, does not exist.\n", filename)
            sys.exit()

# here we go
if FILE:
    with open(filename) as f:
        fdsets = f.read().splitlines()
    for dset in fdsets:
        if not db_exists(dset,bfdsets):
            printf("dataset, %s, does not exist on server.\n", dset)
            sys.exit()
    for dset in fdsets:
        delete_collection(dset, collection, delete_from, FORCE)

elif ALL:
    for dset in hpap_dsets:
        delete_collection(dset.name, collection, delete_from, FORCE)

elif DATASET:
    delete_collection(dset, collection, delete_from, FORCE)

