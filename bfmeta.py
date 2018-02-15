#!/usr/bin/env python 
#===============================================================================
#
#         FILE:  bfmeta.py
#
#        USAGE:  ./bfmeta options arguments
#
#  DESCRIPTION: Insert metadata into base object of given path  
#
#      OPTIONS:  see options in syntax() function
# REQUIREMENTS:  python2, blackfynn library and license
#      UPDATES:  171012: added a show option
#                171016: added a remove option
#                171023: added a type and category options
#                171106: added short name usage for HPAP datasets
#                        added show (--show) support for -a and -f
#                171205: removed support for add/del metadata from dataset
#                180215: unified options
#       AUTHOR:  Pete Schmitt (discovery), <pschmitt@upenn.edu>
#      COMPANY:  University of Pennsylvania
#      VERSION:  0.2.2
#      CREATED:  Fri Oct 13 11:06:25 EDT 2017
#     REVISION:  Thu Feb 15 13:49:24 EST 2018
#===============================================================================
from blackfynn import Blackfynn
from blackfynn.models import BaseCollection
from blackfynn.models import Collection
import sys
import getopt
import os
import datetime as dt
import time
###############################################################################
def printf(format, *args):
    """ works just like the C/C++ printf function """
    sys.stdout.write(format % args)
    sys.stdout.flush()
###############################################################################
def syntax():
    SYNTAX =  "\nbfmeta -d <dataset>\n"
    SYNTAX += "       --all (apply to ALL HPAP datasets)\n"
    SYNTAX += "       -f <file containing datasets>\n"
    SYNTAX += "       -k <metadata key>\n"
    SYNTAX += "       -v <metadata value> \n"
    SYNTAX += "       -m <metadata file of key:value pairs> (-k -v ignored) \n"
    SYNTAX += "       -c <category> (default = Blackfynn)\n"
    SYNTAX += "       -p <dataset path> (path to collection required)\n"
    SYNTAX += "       -t <data type> (integer, string, date, double)\n"
    SYNTAX += "       --remove (remove metadata instead of adding metadata)\n"
    SYNTAX += "       --show (show metadata)\n\n"
    SYNTAX += "       -h (help)\n"
    SYNTAX += "       -l (list datasets)\n\n"
    SYNTAX += "Notes: Adds, removes, or shows metadata to right part of path\n"
    SYNTAX += '       Date format = "MM/DD/YYYY HH:MM:SS"\n' 
    SYNTAX += '       Options -d, -f and --all are mutually exclusive\n' 
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
            dsets.append((str(tmp[0]), str(d.name), d))
        else:
            dsdict[str(d.name)] = str(d.name)
            dsets.append((str(d.name), str(d.name), d))
            
    dsets.sort()
    return dsets, dsdict
###############################################################################
def db_exists(dset,dsets):
    """ check if Dataset exists """
    if dset in dsets:
        return True
    else:
        return False
###############################################################################
def print_date(epoch):
    """ return human readable date from epoch """
    ts = float(epoch[:10])
    return dt.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
###############################################################################
def file_exists(filename):
    """ Check for existance of local file """
    if os.path.exists(filename): return True
    return False
###############################################################################
def collection_exists(ds,name):
    """ test if expected collection in path exists """
    for i in ds.items:
        if name == i.name: return True
    return False
###############################################################################
def print_properties(obj):
    """ print the properties (metadata) of an bf object """
    for i in obj.properties:
        idict = i.as_dict()
        if idict['dataType'] != 'date':
            printf("Key: %s, Value: %s, Type: %s, Category: %s\n",
                    idict['key'], idict['value'], idict['dataType'], 
                    idict['category'])
        else:
            printf("Key: %s, Value: %s, Type: %s, Category: %s\n",
                    idict['key'], print_date(idict['value']),
                    idict['dataType'], idict['category'])

###############################################################################
def show_metadata(dset, meta_path):
    ds = bf.get_dataset(dset)
    dirs = meta_path.split('/')

    for i in range(len(dirs)):
        if dirs[i] == "":
            pass
        elif collection_exists(ds, dirs[i]):
            ds = ds.get_items_by_name(dirs[i])[0]
        else:
            printf("Object, %s, does NOT exist.\n", dirs[i])
            return
            
    printf("\nmetadata for: %s/%s\n", dset, meta_path)
    print_properties(ds)
###############################################################################
def add_remove_metadata(dset, mdlines, meta_path, CATEGORY, ADD, TYPE):
    """ add metadata to object at bottom of meta_path """
    # get to bottom collection in path
    ds = bf.get_dataset(dset)
    dirs = meta_path.split('/')
    
    for i in range(len(dirs)): 
        if dirs[i] == "": break  # add to dataset
        if collection_exists(ds,dirs[i]):
            ds = ds.get_items_by_name(dirs[i])[0]
        else:
            printf("Object, %s, does NOT exist.\n", dirs[i])
            sys.exit()
    
    for i in range(len(mdlines)):
        key, value = mdlines[i].split(':', 1)
        meta_path = dset + '/' + meta_path 

        if ADD:
            if TYPE != 'date':
                if TYPE == None:
                    ds.insert_property(key, value, category=CATEGORY)
                else:
                    ds.insert_property(key, value, category=CATEGORY,
                            data_type=TYPE)
            else:
                pattern = "%m/%d/%Y %H:%M:%S"
                dtime = str(value)
                try:
                    EPOCH = int(time.mktime(time.strptime(dtime, pattern)))
                except:
                    printf("%s does not match format MM/DD/YYYY HH:MM:SS", 
                            dtime)
                    sys.exit()
                EPOCH *= 1000
                ds.set_property(key, EPOCH, category=CATEGORY, data_type=TYPE)

            printf("metadata with key, %s, added to %s\n", key, meta_path)
        else:
            try:
                ds.remove_property(key, CATEGORY)
            except:
                printf("metadata with key, %s, does not exist in %s.\n", 
                        key, meta_path)
                sys.exit()

            printf("metadata with key, %s, removed from %s.\n", key, meta_path)
###############################################################################
# program starts HERE
bf = Blackfynn()  # use 'default' profile
ALL = False
ADD=True
CATEGORY = 'Blackfynn'  # default category
DATASET = False
FILE = False
KEY = False
METAFILE = False
PATH=False
SHOW=False
TYPE=None
VALUE = False
meta_path = ""

if len(sys.argv) < 2:
    printf("%s\n", syntax())
    sys.exit()
argv = sys.argv[1:]

#################
# resolve options
#################
try:
    opts, args = getopt.getopt(argv, "hlt:c:p:d:f:k:v:m:", 
            ['remove','show','all'])
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
    elif opt == '--all':
        hpap_dsets = list()
        ALL = True
        for ds in dsets:
            if 'HPAP-' in ds[0]: hpap_dsets.append(ds[2])
        hpap_dsets.sort(key = lambda x: x.name)
    elif opt == '-p':
        meta_path = arg
        # remove leading / if it exists
        if meta_path[0] == '/': meta_path = meta_path[1:]
        if meta_path == '/': 
            printf("Not possible to update dataset\n")
            sys.exit()
        PATH = True
    elif opt == '-c':
        CATEGORY = arg
    elif opt == '--remove':
        ADD = False
    elif opt in '--show':
        SHOW = True
    elif opt == '-t':
        TYPE = arg
    elif opt == '-l':
        bfdsets.sort()
        for ds in dsets: printf("%s\n", ds[0])
        sys.exit()
    elif opt == '-d':
        try:
            dset = dsdict[arg]
            DATASET = True
        except:
            printf("dataset, %s, does not exist on server.\n", arg)
            sys.exit()
    elif opt in '-f':
        filename = arg
        FILE = True
        if not file_exists(filename):
            printf("file, %s, does not exist.\n", filename)
            sys.exit()
    elif opt == '-m':
        metafile = arg
        METAFILE = True
        if not file_exists(metafile):
            printf("file, %s, does not exist.\n", metafile)
            sys.exit()
    elif opt == '-k':
        KEY = True
        key = arg
    elif opt == '-v':
        VALUE = True
        value = arg

######################
# check metadata input
######################
if not PATH:
    printf("Need to specify a path to a collection with -p\n")
    sys.exit()
if METAFILE:
    with open(metafile) as mf:
        mdlines = mf.read().splitlines()
elif KEY and VALUE:
    mdlines = [0]
    mdlines[0] = key + ':' + value
elif KEY and not ADD:
    mdlines = [0]
    mdlines[0] = key + ':' + 'NOOP'
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
        if SHOW:
            show_metadata(dset, meta_path)
        else:
            add_remove_metadata(dset, mdlines, meta_path, CATEGORY, 
                    ADD, TYPE)

elif ALL:
    for dset in hpap_dsets:
        if SHOW:
            show_metadata(dset.name, meta_path)
        else:
            add_remove_metadata(dset.name, mdlines, meta_path, CATEGORY, 
                    ADD, TYPE)

elif DATASET:
    if SHOW:
        show_metadata(dset, meta_path)
    else:
        add_remove_metadata(dset, mdlines, meta_path, CATEGORY, ADD, TYPE)
