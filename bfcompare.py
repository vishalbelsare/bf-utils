#!/usr/bin/env python
#===============================================================================
#
#          FILE:  bfcompare.py
#
#         USAGE:  ./bfcompare.py
#
#   DESCRIPTION:  Compare Collections between datasets
#
#       OPTIONS:  see syntax() below
#
#  REQUIREMENTS:  python2, pennsieve python library, pennsieve key
#       UPDATES:  170911: Added CLI opt/arg processing
#                 170915: Created create_paths()
#                 170918: Created find()
#                         Created compare()
#                         Added -a option to compare dataset against all others
#                 170919: Added -i for case-insensitive compares
#                 170927: For -a, datasets list is sorted
#                 171030: Added -p to support comparing datasets
#                         with local directories
#                         Added --data to allow comparing data in the path
#                 171103: Added support for short HPAP dataset names
#                 171121: created exceptions for unknown extensions
#                 180214: unified options
#                 180521: added test for package avail in get_collections()
#                 180810: added an additional check for extension
#                 181106: removed pptx and tif from extensions list
#        AUTHOR:  Pete Schmitt (debtfree), pschmitt@upenn.edu
#       COMPANY:  University of Pennsylvania
#       VERSION:  2.1.1
#       CREATED:  09/12/2017 18:00:00 EDT
#      REVISION:  Tue Nov  6 15:07:23 EST 2018
#===============================================================================
from pennsieve import Pennsieve
from pennsieve.models import BaseCollection
from pennsieve.models import Collection
import os
import sys
import getopt
# extensions unknown to Pennsieve
extensions = ['ome.tiff', 'fastq.gz', 'bigWig', 'bw', 'metadata']
###############################################################################
def syntax():
    SYNTAX =  "\nbfcompare -d <dataset>\n"
    SYNTAX += "          -c <compared dataset>\n"
    SYNTAX += "          --all (compare with all datasets)\n"
    SYNTAX += "          -p <local path to compare>\n"
    SYNTAX += "          -i (case-insensitive compares)\n"
    SYNTAX += "          --data (also compare data)\n\n"
    SYNTAX += "          -h (help)\n"
    SYNTAX += "          -l (list datasets)\n"
    SYNTAX += "\nNote: -c, -p and --all are mutually exclusive.\n"
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
def get_collections(element, collections, FILE, indent=0):
    """ output the contents of a dataset as a tree """
    element._check_exists()

    if indent > 0:
        a = str(indent-1) + ':' + element.name
        collections.append(a)
        printf(".")

    for item in element.items:
        if isinstance(item, BaseCollection):
            get_collections(item, collections, FILE, indent=indent+1)
        elif FILE:
            package = bf.get(item)
            pkgname = package.name
            try:
                realnam = str(package.sources[0].s3_key.split('/')[-1])
            except:
                printf("\nERROR: unable to get real name of package: ")
                printf("%s/%s, so it will be ignored.\n", element.name, pkgname)
                continue

            realext = False
            for ext in extensions:
                if realnam.lower().endswith(ext.lower()):
                    realext = ext
                    break

            if realext == False:
                realext = realnam.rsplit(".",1)[-1]

            if pkgname[-len(realext):]==realext:
                filename = pkgname
            else:
                filename = pkgname.replace(realext,"")+"."+realext

            collections.append(str(indent) + ':' + filename)

    return collections
###############################################################################
def create_paths(thelist):
    """ create a list of UNIX-like paths from BF Dataset """
    paths = list()
    for i in thelist:
        colon = i.find(':')
        indent = int(i[:colon])
        collection = i[colon+1:]

        if indent == 0:
            path = [0] * 100
            path[0] = collection
            paths.append(collection)
        else:
            path[indent] = collection
            PATH = path[0]

            for i in range(1,indent+1):
                if path[i] != 0:
                    PATH += "/" + path[i]

            paths.append(PATH)

    return paths
###############################################################################
def find(collection, paths, CASE):
    """ search paths for collection """
    for c in paths:
        if CASE == True and c == collection:
            return True
        elif c.upper()  == collection.upper():
            return True
    return False
###############################################################################
def compare(dset, dspaths, cdset, CASE, FILE):
    printf("\nGathering Collections from %s ",cdset.name)
    collections = []
    cdslist = get_collections(cdset, collections, FILE)
    cdspaths = create_paths(cdslist)
    cdspaths.sort()

    printf("\n\n")
    printf("Data found in %s that are NOT in %s:\n", dset.name, cdset.name)
    for d in dspaths:
        if not find(d, cdspaths, CASE):
            printf("%s\n", d)

    printf("\n")

    printf("Data found in %s that are NOT in %s:\n", cdset.name, dset.name)
    for c in cdspaths:
        if not find(c, dspaths, CASE):
            printf("%s\n", c)
###############################################################################
def localpaths(rootpath, FILE):
    os.chdir(rootpath)
    paths = list()
    for r, d, f in os.walk('.'):
        if FILE:
            dirlist = d + f
        else:
            dirlist = d
        for path in dirlist:
            paths.append((r + '/' + path)[2:])
    paths.sort()
    return paths
###############################################################################
def compare2local(dset, locpaths, dspaths, CASE):
    printf("\nData found in %s that are NOT in %s:\n", dset.name, 'LOCAL')
    for d in dspaths:
        if not find(d, locpaths, CASE):
            printf("%s\n",d)

    printf("\n")

    printf("Data found in %s that are NOT in %s:\n", 'LOCAL', dset.name)
    for c in locpaths:
        if not find(c, dspaths, CASE):
            printf("%s\n",c)
###############################################################################
# program starts HERE
ALL = False
FILE = False
CASE = True
PATH = None
bf = Pennsieve()  # use 'default' profile

if len(sys.argv) < 2:
    printf("%s\n", syntax())
    sys.exit()

argv = sys.argv[1:]

try:
    opts, args = getopt.getopt(argv, "hilp:d:c:",
            ['all', 'data'])
except getopt.GetoptError:
    printf("%s\n", syntax())
    sys.exit()

dsets, dsdict = get_datasets()

for opt, arg in opts:
    if opt == '-h':
        printf("%s\n", syntax())
        sys.exit()
    elif opt == '-i':
        CASE=False
        printf("Note: case-insensitive compares\n")
    elif opt in ('-d'):
        try:
            dset = bf.get_dataset(dsdict[arg])
        except:
            printf("Dataset, %s, does NOT exist.\n", arg)
            sys.exit()
    elif opt == '--all':
        ALL = True
        dsets = []
        for ds in bf.datasets():
            if 'HPAP-' in ds.name: dsets.append(ds)
        dsets.sort(key = lambda x: x.name)
    elif opt in ('-l'):
        for ds in dsets: printf("%s\n", ds[0])
        sys.exit()
    elif opt in ('--data'):
        FILE = True
    elif opt in ('-p'):
        PATH = arg
    elif opt in ('-c'):
        try:
            cdset = bf.get_dataset(dsdict[arg])
        except:
            printf("Dataset, %s, does NOT exist.\n", arg)
            sys.exit()

printf("Gathering Collections from %s ", dset.name)
collections = []
dslist = get_collections(dset, collections, FILE)
dspaths = create_paths(dslist)
dspaths.sort()

if ALL == True:
    for ds in dsets:
        if dset.name != ds.name:
            compare(dset, dspaths, ds, CASE, FILE)
elif PATH != None:
    paths = localpaths(PATH, FILE)
    compare2local(dset, paths, dspaths, CASE)
else:
    compare(dset, dspaths, cdset, CASE, FILE)
