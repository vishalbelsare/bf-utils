#!/usr/bin/env python
#===============================================================================
#
#          FILE:  bfduplicate.py
# 
#         USAGE:  ./bfduplicate.py 
# 
#   DESCRIPTION:  
# 
#       OPTIONS:  see options in syntax() function below
#  REQUIREMENTS:  python2, blackfynn python library, blackfynn key
#       UPDATES:  170911: Added CLI opt/arg processing
#                 171108: Added short names for -d option
#                 180215: unified options
#        AUTHOR:  Pete Schmitt (debtfree), pschmitt@upenn.edu
#       COMPANY:  University of Pennsylvania
#       VERSION:  0.2.0
#       CREATED:  09/06/2017 16:54:33 EDT
#      REVISION:  Thu Feb 15 14:31:03 EST 2018
#===============================================================================
from blackfynn import Blackfynn
from blackfynn.models import BaseCollection
from blackfynn.models import Collection
import sys
import getopt
###############################################################################
def printf(format, *args):
    """ works just like the C/C++ printf function """
    sys.stdout.write(format % args)
    sys.stdout.flush()
###############################################################################
def syntax():
    SYNTAX =   "\nbfduplicate.py -d <dataset>\n"
    SYNTAX +=  "               -n <new dataset>\n\n"
    SYNTAX +=  "               -h (help)\n"
    SYNTAX +=  "               -l (list datasets)\n"
    return SYNTAX
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
def db_exists(dset,dsets):
    """ check if Dataset exists """
    for d in dsets:
        if dset in d[0]:
            return True
    return False
###############################################################################
def create_duplicate(element, newdset, indent=0):
    """ duplicate the Collection structure of existing dataset
        to a newly created dataset """
    element._check_exists()
    
    if indent != 0:
        printf("Creating new Collection:%s%s\n", " "*(indent+4), element.name)
        
    for item in element.items:
        if isinstance(item, BaseCollection):
            c = Collection(item.name)
            newdset.add(c)
            create_duplicate(item, c, indent=indent+4)
###############################################################################
# program starts HERE
bf = Blackfynn()  # use 'default' profile

if len(sys.argv) < 2:
    printf("%s\n", syntax())
    sys.exit()

argv = sys.argv[1:]
try:
    opts, args = getopt.getopt(argv,"hld:n:")
except getopt.GetoptError:
    printf("%s\n", syntax())
    sys.exit()

dsets, dsdict = get_datasets()

for opt, arg in opts:
    if opt == '-h':
        printf("%s\n", syntax())
        sys.exit()

    elif opt in '-l':
        for ds in dsets:
            printf("%s\n", ds[0])
        sys.exit()

    elif opt in '-d':
        dset = bf.get_dataset(dsdict[arg])

    elif opt in '-n':
        if db_exists(arg, dsets):
            printf("Dataset %s already exists.  Can not continue.\n", arg)
            EXISTS = True
            sys.exit()
        else:
            printf("Creating new dataset: %s\n", arg)
            bf.create_dataset(arg)
            newdset = bf.get_dataset(arg)

create_duplicate(dset, newdset)
