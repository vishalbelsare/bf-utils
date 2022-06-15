#!/usr/bin/env python
#===============================================================================
#
#          FILE:  bfdircnt.py
# 
#         USAGE:  bfdircnt <directory> 
# 
#   DESCRIPTION:  bftree like on Linux directories  
# 
#       OPTIONS:  ---
#  REQUIREMENTS:  python 2.7.x
#          BUGS:  ---
#       UPDATES:  ---
#        AUTHOR:  Pete Schmitt (discovery), pschmitt@upenn.edu
#       COMPANY:  University of Pennsylvania
#       VERSION:  0.1.0
#       CREATED:  Fri Jun  8 13:37:59 EDT 2018
#      REVISION:  ---
#===============================================================================
import copy
import os
import sys
import collections
###############################################################################
def printf(format, *args):
    """ works just like the C/C++ printf function """
    import sys
    sys.stdout.write(format % args)
    sys.stdout.flush()
###############################################################################
def traverse(path):
    tree = dict()
    for dirName, subdirList, fileList in os.walk(path):
        tree[dirName] = [len(subdirList), len(fileList)]

    ntree = copy.deepcopy(tree)
    return tree, collections.OrderedDict(sorted(ntree.items()))
###############################################################################
try:
    path = sys.argv[1]
except:
    printf("Syntax: bfdircnt <directory>\n")
    sys.exit(1)

if path[-1] == '/':
    path = path[0:-1]

if os.path.exists(path) and os.path.isdir(path):
    BASE = os.path.basename(path)
    os.chdir(path + '/..')
else:
    printf("Error: argument must be existing directory\n")
    sys.exit(2)

atree, otree = traverse(BASE)

for a in otree:
    for b in atree:
        if a in b and a != b:
            otree[a][0] += atree[b][0]
            otree[a][1] += atree[b][1]

for d in otree:
    dirs = otree[d][0]
    files = otree[d][1]
    dlist = d.split('/')
    slashes = len(dlist) - 1
    if slashes > 0:
        printf("%s", "    " * slashes)
    if ((dirs + files) == 0):
        printf("%s (empty)\n", os.path.basename(d))
    else:
        printf("%s (dirs: %d files: %d)\n", os.path.basename(d), dirs, files)
