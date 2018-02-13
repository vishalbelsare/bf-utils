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
#                -a (apply to all HPAP datasets)
#                -f <file> (use file containing datasets to update)
#                -l (list all datasets)
#                -h (help)
# REQUIREMENTS:  python2, blackfynn python library and license key
#      UPDATES:  171006: collection path can start with / or not
#                171113: renames collections only
#       AUTHOR:  Pete Schmitt (discovery), <pschmitt@upenn.edu>
#      COMPANY:  University of Pennsylvania
#      VERSION:  0.1.1
#      CREATED:  Fri Oct  6 13:36:33 EDT 2017
#     REVISION:  Mon Nov 13 16:26:51 EST 2017
#===============================================================================
from blackfynn import Blackfynn
from blackfynn.models import BaseCollection
from blackfynn.models import Collection
import sys
import getopt
import os
###############################################################################
def syntax():
    SYNTAX =  "bfrename -p <dataset path> "
    SYNTAX += "(renames rightmost object in path)\n"
    SYNTAX += "         -n <new object name>\n"
    SYNTAX += "         -d <dataset>\n"
    SYNTAX += "         -a (apply to ALL HPAP datasets)\n"
    SYNTAX += "         -f <file containing datasets>\n\n"
    SYNTAX += "         -h (help)\n"
    SYNTAX += "         -l (list datasets)\n"
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
def rename_object(dset, path, newname):
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
        printf("Unable to rename packages!")
        return
    ds.name = newname
    ds.update()
    printf("Object, %s, renamed to %s within dataset %s.\n", obj, newname, dset)
    return
###############################################################################
# program starts HERE
bf = Blackfynn()  # use 'default' profile
ALL = False
FILE = False
DATASET = False

if len(sys.argv) < 2:
    printf("%s\n", syntax())
    sys.exit()
argv = sys.argv[1:]

#################
# resolve options
#################
try:
    opts, args = getopt.getopt(argv, "Fhaln:p:d:f:",
          ['force', 'collection=', 'file=', 'help', \
           'list', 'path=', 'dataset=', 'all'])
except getopt.GetoptError:
    printf("%s\n", syntax())
    sys.exit()

dsets, dsdict = get_datasets()

for opt, arg in opts:
    if opt in ('-h', '--help'):
        printf("%s\n", syntax())
        sys.exit()
    elif opt in ('-a', '--all'):
        hpap_dsets = list()
        ALL = True
        for ds in dsets:
            if 'HPAP-' in ds[0]: hpap_dsets.append(ds[2])
        hpap_dsets.sort(key = lambda x: x.name)
    elif opt in ('-n'):
        newname = arg
    elif opt in ('-p', '--path'):
        path = arg
    elif opt in ('-l', '--list'):
        for ds in dsets:
            printf("%s\n", ds[0])
        sys.exit()
    elif opt in ('-d', '--dataset'):
        DATASET = True
        if not ds_exists(arg, dsets):
            printf("Dataset, %s, does NOT exist.\n", arg)
            sys.exit()
        else:
            dset = dsdict[arg]
    elif opt in ('-f', '--file'):
        filename = arg
        FILE = True
        if not file_exists(filename):
            printf("file, %s, does NOT exist.\n", filename)
            sys.exit()
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
        rename_object(dset, path, newname)

elif ALL:
    for dset in hpap_dsets:
        rename_object(dset.name, path, newname)

elif DATASET:
    rename_object(dset, path, newname)
