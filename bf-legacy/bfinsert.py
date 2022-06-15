#!/usr/bin/env python 
#===============================================================================
#
#         FILE:  bfinsert.py
#
#        USAGE:  ./bfinsert -d <dataset> -p <path> 
#                           -l (list datasets)
#                           -h (help)
#
#  DESCRIPTION: Insert collection into given path  
#
#      OPTIONS:  -p <dataset path>
#                -d <dataset> (update single dataset)
#                --all (apply to all HPAP datasets)
#                -f <file> (use file containing datasets to update)
#                -l (list all datasets)
#                -h (help)
#      UPDATES:  171005: added error checking in collection path
#                171006: collection path can start with / or not
#                171009: -p includes collection to insert at bottom of path
#                171103: Added usage of short names for HPAP datasets
#                180215: unified options
#       AUTHOR:  Pete Schmitt (discovery), <pschmitt@upenn.edu>
#      COMPANY:  University of Pennsylvania
#      VERSION:  0.2.1
#      CREATED:  10/02/2017 14:13:54 EDT
#     REVISION:  Thu Feb 15 13:25:30 EST 2018
#===============================================================================
from pennsieve import Pennsieve
from pennsieve.models import BaseCollection
from pennsieve.models import Collection
import sys
import getopt
import os
###############################################################################
def printf(format, *args):
    """ works just like the C/C++ printf function """
    sys.stdout.write(format % args)
    sys.stdout.flush()
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
def syntax():
    SYNTAX =  "\nbfinsert -d <dataset\n"
    SYNTAX += "         --all (apply to ALL HPAP datasets)\n"
    SYNTAX += "         -f <file containing datasets>\n"
    SYNTAX += "         -p <dataset path> "
    SYNTAX += "(inserts rightmost part of path)\n\n"
    SYNTAX += "         -h (help)\n"
    SYNTAX += "         -l (list datasets)\n\n"
    SYNTAX += "Note: -d, -f and --all are mutually exclusive.\n"
    return SYNTAX
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
def insert_collection(dset, collection, insert_where):
    if insert_where == "": 
        path = "root directory"
    else:
        path = insert_where
    
    # get to bottom collection in path
    ds = bf.get_dataset(dset)
    dirs = insert_where.split('/')
    
    for i in range(len(dirs)): 
        if dirs[i] == "": break  # add to root directory
        if collection_exists(ds,dirs[i]):
            ds = ds.get_items_by_name(dirs[i])[0]
        else:
            printf("Collection, %s, does NOT exist.\n", dirs[i])
            sys.exit()

    # ensure collection does not exist and insert it
    FOUND = False
    if len(ds.items) > 0:
        for item in ds.items:
            if collection in item.name:
                FOUND = True
                break
    if FOUND:
        printf("Collection, %s, already exists in \"%s\" within dataset %s\n", 
                collection, path, dset)
    else:
        c = Collection(collection)
        ds.add(c)
        printf("Collection, %s, added to \"%s\" within dataset %s\n", 
                collection, path, dset)
    return
###############################################################################
# program starts HERE
bf = Pennsieve()  # use 'default' profile
ALL = False
FILE = False
DATASET = False
COLLECTION = False

if len(sys.argv) < 2:
    printf("%s\n", syntax())
    sys.exit()
argv = sys.argv[1:]

#################
# resolve options
#################
try:
    opts, args = getopt.getopt(argv, "hlp:d:f:", ['all'])
except getopt.GetoptError:
    printf("%s\n", syntax())
    sys.exit()

dsets, dsdict = get_datasets()
bfdsets = list()
for ds in dsets: 
    bfdsets.append(dsdict[ds[0]])

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
    elif opt in '-p':
        insert_where = arg
        # remove leading / if it exists
        if insert_where[0] == '/': insert_where = insert_where[1:]
        pathlist = insert_where.split('/')
        collection = pathlist[-1]
        insert_where = '/'.join(pathlist[:-1])
    elif opt in '-l':
        for ds in dsets: printf("%s\n", ds[0])
        sys.exit()
    elif opt in '-d':
        dset = dsdict[arg]
        DATASET = True
        if not db_exists(dset,bfdsets):
            printf("dataset %s does not exist on the server.\n", dset)
            sys.exit()
    elif opt in '-f':
        filename = arg
        FILE = True
        if not file_exists(filename):
            printf("file, %s, does not exist.\n", filename)
            sys.exit()
############
# here we go
############
if FILE:
    with open(filename) as f:
        fdsets = f.read().splitlines()
    for dset in fdsets:
        if not db_exists(dset,bfdsets):
            printf("dataset, %s, does not exist on server.\n", dset)
            sys.exit()
    for dset in fdsets:
        insert_collection(dset, collection, insert_where)

elif ALL:
    for dset in hpap_dsets:
        insert_collection(dset.name, collection, insert_where)

elif DATASET:
    insert_collection(dset, collection, insert_where)
