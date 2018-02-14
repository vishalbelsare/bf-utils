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
bf = Blackfynn()  # use 'default' profile
###############################################################################
def syntax():
    SYNTAX =   "\nbfmove -d <dataset> \n"
    SYNTAX +=  "       --all (loop on all HPAP datasets)\n"
    SYNTAX +=  "       -S <source path>\n"
    SYNTAX +=  "       -D <destination path> (MUST be directory)\n\n"
    SYNTAX +=  "       -h (help)\n"
    SYNTAX +=  "       -l (list datasets)\n\n"
    SYNTAX +=  "Note: -d and --all are mutually exlusive\n"
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
# program starts HERE
ALL = False
SOURCE = False
DESTINATION = False
DATASET = False
REAL = False

if len(sys.argv) < 2:
    printf("%s\n", syntax())
    sys.exit()

argv = sys.argv[1:]

try:
    opts, args = getopt.getopt(argv, "hld:S:D:",
            ['all', 'help', 'list' ])
except getopt.GetoptError:
    printf("%s\n", syntax())
    sys.exit()
    
dsets, dsdict = get_datasets()

for opt, arg in opts:
    if opt in ('--all'):
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
    elif opt in ('-l', '--list'):
        for ds in dsets:
            printf("%s\n",ds[0])
        sys.exit()
    elif opt in ('-d'):
        DATASET = True
        try:
            dset = bf.get_dataset(dsdict[arg])
        except:
            printf("Dataset, %s, does NOT exist.\n", arg)
            sys.exit()

if not ALL and SOURCE and DESTINATION and DATASET:
    destination = locate_path(dset, dest)
    source = locate_path(dset, src)
    bf.move(destination, source)
    printf("%s moved to %s\n", src, dest)

elif ALL and not DATASET:
    for ds in dsets:
        if 'HPAP-' not in ds[0]: continue
        dset = bf.get_dataset(ds[1])
        destination = locate_path(dset, dest)
        source = locate_path(dset, src)
        bf.move(destination, source)
        printf("%s moved to %s\n", src, dest)
