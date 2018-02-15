#!/usr/bin/env python
#===============================================================================
#
#          FILE:  bfmove.py
# 
#         USAGE:  ./bfmove.py 
# 
#   DESCRIPTION:  move something to another directory  
# 
#   OPTIONS:      -d <dataset>  (show contents of dataset)
#                 -s <source path> bottom of path is moved
#                 -D <destination path> move source here
#                 -l  (list all available datasets)
#                 -h  (show help)
#  REQUIREMENTS:  python2, blackfynn python library, blackfynn key
#       UPDATES:  
#        AUTHOR:  Pete Schmitt (discovery), pschmitt@upenn.edu
#       COMPANY:  University of Pennsylvania
#       VERSION:  0.1.0
#       CREATED:  Wed Feb 14 13:27:32 EST 2018
#      REVISION:  
#===============================================================================

from blackfynn import Blackfynn
from blackfynn.models import BaseCollection
from blackfynn.models import Collection
import sys
import getopt
import os
bf = Blackfynn()  # use 'default' profile
###############################################################################
def syntax():
    SYNTAX =   "\nbfmove -d <dataset> \n"
    SYNTAX +=  "       --all (loop on all HPAP datasets)\n"
    SYNTAX +=  "       -f (file containing datasets)\n"
    SYNTAX +=  "       -S <source path>\n"
    SYNTAX +=  "       -D <destination path> (MUST be directory)\n\n"
    SYNTAX +=  "       -h (help)\n"
    SYNTAX +=  "       -l (list datasets)\n\n"
    SYNTAX +=  "Note: -d, -f and --all are mutually exlusive\n"
    return SYNTAX
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
            dsets.append((str(tmp[0]), str(d.name)))
        else:
            dsdict[str(d.name)] = str(d.name)
            dsets.append((str(d.name), str(d.name)))
            
    dsets.sort()
    return dsets, dsdict
###############################################################################
def collection_exists(ds,name):
    """ test if expected collection in path exists """
    for i in ds.items:
        if name == i.name: return True
    return False
###############################################################################
def locate_path(ds, path):
    """ Return the object that represents where to 
        start to print the tree """
    dirs = path.split('/')
    
    for i in range(len(dirs)):
        if dirs[i] == "":
            pass
        elif collection_exists(ds, dirs[i]):
            ds = ds.get_items_by_name(dirs[i])[0]
        else:
            printf("Object, %s, does NOT exist.\n", path)
            sys.exit()
    return ds
###############################################################################
def file_exists(filename):
    if os.path.exists(filename): return True
    return False
###############################################################################
def db_exists(dset, dsets):
    """ check if Dataset exists """
    if dset in dsets:
        return True
    else:
        return False
###############################################################################
# program starts HERE
ALL = False
FILE = False
DATASET = False
SOURCE = False
DESTINATION = False

if len(sys.argv) < 2:
    printf("%s\n", syntax())
    sys.exit()

argv = sys.argv[1:]

try:
    opts, args = getopt.getopt(argv, "hld:S:D:f:",
            ['all', 'help'])
except getopt.GetoptError:
    printf("%s\n", syntax())
    sys.exit()
    
dsets, dsdict = get_datasets()
bfdsets = list()
for ds in dsets: 
    bfdsets.append(dsdict[ds[0]])

for opt, arg in opts:
    if opt in '--all':
        ALL = True
    elif opt == '-S':
        SOURCE = True
        src = arg
    elif opt == '-D':
        DESTINATION = True
        dest = arg
    elif opt == '-h':
        printf("%s\n", syntax())
        sys.exit()
    elif opt in '-l':
        for ds in dsets:
            printf("%s\n",ds[0])
        sys.exit()
    elif opt in "-f":
        filename = arg
        FILE = True
        if not file_exists(filename):
            printf("file, %s, does not exist.\n", filename)
            sys.exit()
    elif opt in '-d':
        DATASET = True
        try:
            dset = bf.get_dataset(dsdict[arg])
        except:
            printf("Dataset, %s, does NOT exist.\n", arg)
            sys.exit()

# Using single Dataset
if not ALL and SOURCE and DESTINATION and DATASET:
    destination = locate_path(dset, dest)
    source = locate_path(dset, src)
    bf.move(destination, source)
    printf("%s moved to %s\n", src, dest)

# Using a file containing Dataset names
elif not ALL and not DATASET and FILE:
    with open(filename) as f:
        fdsets = f.read().splitlines()
    for dset in fdsets:
        if not db_exists(dset,bfdsets):
            printf("dataset, %s, does not exist on server.\n", dset)
            sys.exit()
    for ds in fdsets:
        dset = bf.get_dataset(dsdict[ds])
        destination = locate_path(dset, dest)
        source = locate_path(dset, src)
        bf.move(destination, source)
        printf("%s moved to %s\n", src, dest)

# Do move on ALL HPAP datasets 
elif ALL and not DATASET:
    for ds in dsets:
        if 'HPAP-' not in ds[0]: continue
        dset = bf.get_dataset(ds[1])
        destination = locate_path(dset, dest)
        source = locate_path(dset, src)
        bf.move(destination, source)
        printf("%s moved to %s\n", src, dest)
