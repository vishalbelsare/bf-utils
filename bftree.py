#!/usr/bin/env python
#===============================================================================
#
#          FILE:  bftree.py
# 
#         USAGE:  ./bftree.py 
# 
#   DESCRIPTION:  
# 
#       OPTIONS:  see syntax() below
#
#  REQUIREMENTS:  python2, blackfynn python library, blackfynn key
#       UPDATES:  170911: Added CLI opt/arg processing
#                 170922: Added -f option to show files
#                 171009: Check for existence of dataset
#                 171009: Added --nocolor option
#                 171102: Added ability to use short names for HPAP datasets
#                 171106: Added -p and -a options
#                 171110: data now shows actual file name
#                 171114: added --realdata
#                 171116: file download names now use the BF name and real
#                         extension of the uploaded filename
#                 171117: --realdata now shows uploaded filename and extension
#                         --data now shows BF filename and uploaded extension
#                 171121: created exceptions for unknown extensions
#                 180215: unified options
#                 180521: added test for package avail in print_tree()
#        AUTHOR:  Pete Schmitt (debtfree), pschmitt@upenn.edu
#       COMPANY:  University of Pennsylvania
#       VERSION:  0.5.3
#       CREATED:  09/06/2017 16:54:33 EDT
#      REVISION:  Mon May 21 11:26:44 EDT 2018
#===============================================================================

from blackfynn import Blackfynn
from blackfynn.models import BaseCollection
from blackfynn.models import Collection
from termcolor import colored
import sys
import getopt
bf = Blackfynn()  # use 'default' profile
# extensions unknown to Blackfynn
extensions = ['tif', 'fcs','bw', 'pptx', 'metadata']
###############################################################################
def syntax():
    SYNTAX =   "\nbftree -d <dataset> \n"
    SYNTAX +=  "       --all (loop on all HPAP datasets)\n"
    SYNTAX +=  "       -p <path to start tree>\n"
    SYNTAX +=  "       --data (show packages in output)\n"
    SYNTAX +=  "       --realdata (show packages as uploaded names)\n"
    SYNTAX +=  "       --nocolor (no colorful output)\n\n"
    SYNTAX +=  "       -h (help)\n"
    SYNTAX +=  "       -l (list datasets)\n\n"
    SYNTAX +=  "Note: -d and --all are mutually exclusive\n"
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
def print_tree(element, FILE, COLOR, REAL, indent=0):
    """ print the contents of a dataset as a tree """
    try:
        element._check_exists()
    except:
        printf("Object %s does NOT exist.\n", element)
        sys.exit()
    
    count = len(element.items)
    if count == 0:
        if COLOR:
            pritems = " (" + colored('empty', 'magenta') + ")" 
        else:
            pritems = " (empty)"
    else:
        pritems = " (" + str(count) + " items)"

    printme = " "*(indent) + element.name 

    if indent != 0:
        if COLOR:
            printme += colored(' (C)', 'green') 
        else:
            printme += ' (C)' 

    printme += pritems
    printf("%s\n", printme)

    for item in element.items:
        if isinstance(item, BaseCollection):
            print_tree(item, FILE, COLOR, REAL, indent=indent+4)
        elif FILE:
            package = bf.get(item)
            pkgname = package.name
            try:
                realnam = str(package.sources[0].s3_key.split('/')[-1])
            except:
                printf("\nERROR: unable to get real name of package: ")
                printf("%s/%s, continuing...\n\n", element.name, pkgname)
                continue
            realext = realnam.split('.')[-1]
            if REAL:
                pkgname = package.sources[0].name
                if realext in extensions:
                    filename = pkgname
                else:
                    filename = pkgname + '.' + realext
            else:
                pkgname = package.name
                if realext in extensions:
                    filename = pkgname
                else:
                    filename = pkgname + '.' + realext

            if COLOR:
                printme = " "*(indent+4) + filename + colored(" (pkg)", "red")
            else:
                printme = " "*(indent+4) + filename + " (pkg)"
            printf("%s\n", printme)
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
            printf("Object, %s, does NOT exist.\n", dirs[i])
            sys.exit()
    return ds
###############################################################################
# program starts HERE
FILE = False
COLOR = True
ALL = False
PATH = False
DATASET = False
REAL = False

if len(sys.argv) < 2:
    printf("%s\n", syntax())
    sys.exit()

argv = sys.argv[1:]

try:
    opts, args = getopt.getopt(argv, "hld:p:",
            ['realdata', 'all', 'nocolor', 'data'])
except getopt.GetoptError:
    printf("%s\n", syntax())
    sys.exit()
    
dsets, dsdict = get_datasets()

for opt, arg in opts:
    if opt == '--data':
        FILE=True
    elif opt in '--all':
        ALL = True
    elif opt == '-p':
        path = arg
        PATH = True
    elif opt == '--realdata':
        REAL = True
        FILE = True
    elif opt == '--nocolor':
        COLOR = False
    elif opt == '-h':
        printf("%s\n", syntax())
        sys.exit()
    elif opt in '-l':
        for ds in dsets:
            printf("%s\n",ds[0])
        sys.exit()
    elif opt in '-d':
        DATASET = True
        try:
            dset = bf.get_dataset(dsdict[arg])
        except:
            printf("Dataset, %s, does NOT exist.\n", arg)
            sys.exit()

if PATH and DATASET:
    dset = locate_path(dset, path)
    print_tree(dset, FILE, COLOR, REAL)
elif ALL:
    for ds in dsets:
        if 'HPAP-' not in ds[0]: continue
        dset = bf.get_dataset(ds[1])
        dataset = dset
        if PATH:
            dset = locate_path(dset, path)
            printf("\n%s:%s\n", dataset.name, path)
        print_tree(dset, FILE, COLOR, REAL)
else:        
    print_tree(dset, FILE, COLOR, REAL)
