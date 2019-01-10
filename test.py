from blackfynn import Blackfynn
from blackfynn.models import BaseCollection
from blackfynn.models import Collection
from shutil import rmtree
import pandas as pd
import sys
import getopt
import os
import time

bf = Blackfynn()
extensions = ['ome.tiff', 'fastq.gz', 'bigWig', 'bw', 'metadata']

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

def create_paths(dsetname, outdir, thelist):
    """ create a list of UNIX-like paths from BF Dataset """
    paths = list()
    relpaths = list()
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

    for i in range(len(paths)):
        tmpath = paths[i].split(':')
        relpaths.append(str(tmpath[0]))
        paths[i] = outdir + '/' + dsetname + '/' + str(paths[i])

    relpaths.sort()
    return paths, relpaths

def get_collections(element, collections, indent=0):
    """ gather the contents of a dataset to be processed later """
    element._check_exists()

    if indent > 0:
        a = str(indent-1) + ':' + element.name
        collections.append(a)

    for item in element.items:
        if isinstance(item, BaseCollection):
            get_collections(item, collections, indent=indent+1)
        else:
            package = bf.get(item)
            pkgname = package.name
            try:
                realnam = str(package.sources[0].s3_key.split('/')[-1])
            except:
                printf("ERROR: unable to get real name of package: ")
                printf("%s/%s, so it will be ignored.\n", element.name, pkgname)
                continue

            realext = False
            for ext in extensions:
                if realnam.lower().endswith(ext.lower()):
                    realext = ext
                    if realext == "bigWig":
                        realext = "bw"
                    break

            if realext == False:
                realext = realnam.rsplit(".",1)[-1]

            if pkgname[-len(realext):]==realext:
                filename = pkgname
            else:
                filename = pkgname.replace(realext,"")+"."+realext

            b = str(indent) + ':' + filename + ':' + item.id
            collections.append(b)

    return collections

dsets, dsdict = get_datasets()

with open("D:/bfsync/HPAP001.exceptions.txt", "r") as f:
    exlist = f.read().splitlines()

exlist

dsname = "HPAP-001"
dset = bf.get_dataset(dsdict[dsname])

outdir = "/hpapdata"

collections = list()

dslist = get_collections(dset,collections)

dspaths,relpaths = create_paths(dsname, outdir, dslist)

def excepted(package, exlist):
    """ return True if package found in exlist """
    if package in exlist:
        return True
    return False

for i in dspaths:
    file_name = i.rsplit("/",1)[-1].split(":",1)[0].strip()
    except_pkg = excepted(file_name, exlist)
    if file_name in exlist:
        print(file_name)

pkgpaths = list()
for i in dspaths:
    file_name = i.rsplit("/",1)[-1].split(":",1)[0].strip()
    if ':package:' in i and  file_name not in exlist:
        pkgpaths.append(i)

# Match file name in exlist to dspaths full file path, if file exists, remove
for f in exlist:
    match = [x for x in dspaths if f in x]
    if len(match) > 0:
        # There should only ever be one match
        # for each file in the exception list
        check_file = os.path.isfile(match[0])
        if check_file:
            os.remove(match[0])
