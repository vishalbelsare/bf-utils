from blackfynn import Blackfynn
from blackfynn.models import BaseCollection
from blackfynn.models import Collection
from shutil import rmtree
import pandas as pd
import sys
import getopt
import os
import time
import re

bf = Blackfynn()
extensions = ['ome.tiff', 'fastq.gz', 'bigWig', 'bw', 'metadata']
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
        if re.match(r"HPAP-\d{3}\s\(\d{2}\D\d{4}\)", d.name):
            tmp = d.name.split()
            dsdict[str(tmp[0])] = str(d.name)
            dsets.append((str(tmp[0]), str(d.name)))
        else:
            # Don't collect non-HPAP datasets
            dsdict[str(d.name)] = str(d.name)
            dsets.append((str(d.name), str(d.name)))

    dsets.sort()
    return dsets, dsdict
###############################################################################
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
###############################################################################
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
###############################################################################
def get_packages(pkgpaths, quick_refresh = False):
    """ download the data into the UNIX directories from the BF server """
    for path in pkgpaths:
        pathlist = path.split('/')
        pkg = pathlist[-1]

        unixdir = '/'.join(pathlist[:-1])

        pkglist = pkg.split(':')
        pkg = pkglist[1:]
        pkg = ':'.join(pkg)

        rootdir = os.getcwd()

        if os.path.isdir(unixdir)==False:
            os.makedirs(unixdir)

        os.chdir(unixdir)

        package = bf.get(pkg)
        pkgname = package.name
        realnam = str(package.sources[0].s3_key.split('/')[-1])

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

        # control bigwig extension
        if "bigWig" in filename.rsplit(".",1)[-1]:
            filename = filename.replace(".bigWig",".bw")

        if quick_refresh:
            pack_check = check_package(pkg, pkgname, filename)

            if pack_check=="Download":
                printf("downloading %s to %s\n", filename, unixdir)
                dlname = package.sources[0].download(realnam)
                if str(dlname) != filename:
                    os.rename(str(dlname), filename)
            else:
                printf("passing %s, no changes to file\n", filename)
        else:
            dlname = package.sources[0].download(realnam)
            if str(dlname) != filename:
                os.rename(str(dlname), filename)

        os.chdir(rootdir)
###############################################################################
def mirror(dspaths, locpaths, rootdir):
    """ ensure both dataset and local directory are equal """
    dspaths.sort(reverse=True)
    locpaths.sort(reverse=True)

    for i in range(len(locpaths)):
        if locpaths[i] not in dspaths:
            printf("%s does not exist in dataset, \n\tremoving ", locpaths[i])
            abspath = rootdir + '/' + locpaths[i]
            printf("%s\n", abspath)

            if os.path.isdir(abspath):
                print os.getcwd(), abspath
                rmtree(abspath)
            elif os.path.isfile(abspath):
                print os.getcwd(), abspath
                os.unlink(abspath)
###############################################################################
def excepted(item, exlist):
    """ return True if package found in exlist """
    checks = [item in x for x in exlist]
    if any(checks):
        return True
    return False
###############################################################################
def extension_remover(file_name):
    for ext in extensions:
        if "."+ext in file_name:
            return file_name.replace("."+ext,"")

    if file_name.count(".")==1:
        return file_name.rsplit(".",1)[0]

    return file_name
###############################################################################
dsets, dsdict = get_datasets()

dsets

dsname = "HPAP-001"
dset = bf.get_dataset(dsdict[dsname])

outdir = "D:/hpapdata"

collections = list()

printf("Gathering Collections from %s ...\n",dset.name)
collections = list()
dslist = get_collections(dset,collections)
dspaths,relpaths = create_paths(dsname, outdir, dslist)
dspaths.sort()

if EXCEPT:
    with open("D:/bfsync/HPAP001.exceptions.txt", "r") as f:
        exlist = f.read().splitlines()
else:
    exlist = list()

exlist

printf("\nCreating local directory structure in %s if necessary\n", outdir)

for i in dspaths:
    if not os.path.isdir(i):
        # If path is a package, skip for now
        if ':package:' in i: continue
        # If excepted = True, then file is an exception and should be passed
        if excepted(i, exlist): continue
        os.makedirs(i)

NODATA = False
QUICKSYNC = False
if not NODATA:
    start = time.time()
    pkgpaths = list()
    printf("\nRetrieving Dataset packages to %s\n", outdir)
    for i in dspaths:
        if ":package:" not in i: continue
        package_split = i.rsplit("/",1)[-1].split(":",1)
        file_name = package_split[0]
        package_id = package_split[1]
        if not excepted(file_name, exlist) and not excepted(package_id, exlist):
            pkgpaths.append(i)

    if QUICKSYNC:
        hpap_files = []
        for root, b, files in os.walk(outdir):
            hpap_files.extend([[root, x] for x in files])

        data_df = pd.DataFrame(hpap_files, columns=['root','file_name'])
        data_df.loc[:,'file_name_clean'] = data_df.file_name.apply(extension_remover)
        get_packages(pkgpaths, quick_refresh=True)

    else:
        get_packages(pkgpaths)

    printf("\n%s Download time: %.2f seconds\n",
            dsname, time.time() - start)
EXCEPT = True
if EXCEPT:
    printf("\nChecking for Exception files ...\n")
    for f in exlist:
        match = [x for x in dspaths if f in x]
        if len(match) > 0:
            del_file = match[0].split(":",1)[0]
            # There should only ever be one match
            # for each file in the exception list
            check_file = os.path.isfile(del_file)
            if check_file:
                printf("\nRemoving %s ...\n", f)
                os.remove(del_file)

def localpaths(rootpath, FILE):
    """ retrieve local paths of directory """
    paths = list()
    for r, d, f in os.walk(rootpath):
        d = [r + "/" + x for x in d]
        f = [r + "/" + x for x in f]
        if FILE:
            dirlist = d + f
        else:
            dirlist = d
        for path in dirlist:
             paths.append(path.replace("\\\\","/").replace("\\","/"))
    paths.sort()
    return paths

def mirror(dspaths, locpaths, rootdir):
    """ ensure both dataset and local directory are equal """
    dspaths.sort(reverse=True)
    # Remove Blackfynn :package: ending to match local paths
    dspaths = [":".join(x.split(":",2)[:2]) for x in dspaths]
    locpaths.sort(reverse=True)

    for i in range(len(locpaths)):
        if locpaths[i] not in dspaths:
            printf("%s does not exist in dataset, \n\tremoving ", locpaths[i])
            printf("%s\n", locpaths[i])

            if os.path.isdir(locpaths[i]):
               print os.getcwd(), locpaths[i]
               os.removedirs(locpaths[i])
            elif os.path.isfile(locpaths[i]):
               print os.getcwd(), locpaths[i]
               os.unlink(locpaths[i])

MIRROR = True
DATASET = True
NODATA
outdir
if MIRROR and DATASET:
    printf("\nMirroring Dataset and Local...\n\n")
    rootdir = outdir + '/' + dsname
    locpaths = localpaths(rootdir, not NODATA)
    #mirror(dspaths, locpaths, rootdir)
