#!/usr/bin/env python
#===============================================================================
#
#          FILE:  bfsync.py
#
#         USAGE:  ./bfsync.py
#
#   DESCRIPTION:  create file structure on server based on dataset structure
#
#       OPTIONS:  see syntax() below
#
#  REQUIREMENTS:  python2, blackfynn python library, blackfynn key
#       UPDATES:  171018: added --nodata
#                 171102: added ability to use short names for HPAP datasets
#                         and uses short name on output
#                 171109: added --mirror option
#                 171110: added --refresh option
#                 171114: made --refresh default True, added --norefresh
#                         added -e to provide for exceptions
#                 171116: file download names now use the BF name and real
#                         extension of the uploaded filename
#                 171117: fixed bug with --mirror and . directory
#                 171121: created exceptions for unknown extensions
#                 171206: no longer create local directories in exception list
#                 180215: unified options
#                 180518: added test for package avail in get_collections()
#                 180730: updated URL to contact for refresh
#                 180810: added an additional check for extension
#                         and rename downloaded pkg if needed.
#                 181003: -e removes local excepted files if existing
#                 181106: removed pptx and tif from extensions list
#        AUTHOR:  Pete Schmitt (debtfree), pschmitt@upenn.edu
#       COMPANY:  University of Pennsylvania
#       VERSION:  0.7.1
#       CREATED:  Mon Oct  9 19:56:00 EDT 2017
#      REVISION:  Tue Nov  6 15:07:23 EST 2018
#===============================================================================
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

# extensions unknown to Blackfynn
extensions = ['ome.tiff', 'fastq.gz', 'bigWig', 'bw', 'metadata']

categories = [
    "Clinical data", "B cell receptor repertoire", "Flow panels for B cells",
    "Flow cytometry - Immune lineage", "Histology", "CyTOF", "ATACseq",
    "mRNAseq", "Sequencing data for sorted cells/Sort data", "WGBS", "Single-cell RNAseq", "Calcium imaging",
    "Patch-Clamp", "Oxygen consumption", "Morphology and viability", "Perifusions",
    "Imaging mass cytometry", "ATAQseq", "Tetramer Ag specific studies by FACS"
]

###############################################################################
def syntax():
    SYNTAX =  "\nbfsync -d <dataset> \n"
    SYNTAX += "       -c <data category, "
    SYNTAX += "same categories as https://hpap.pmacs.upenn.edu/explore/download?category> \n"
    SYNTAX += "       -p <output path for local dataset storage> "
    SYNTAX += "(default is $PWD)\n"
    SYNTAX += "       -e <file containing exception paths>\n"
    SYNTAX += "       --nodata (do not include data)\n"
    SYNTAX += "       --mirror (remove local data/directories to mirror "
    SYNTAX += "dataset)\n"
    SYNTAX += "       --refresh (send a signal to hpap data website to "
    SYNTAX += "refresh. this is the default)\n"
    SYNTAX += "       --norefresh (do not send signal to hpap data website to "
    SYNTAX += "refresh)\n\n"
    SYNTAX += "       -h (help)\n"
    SYNTAX += "       -l (list datasets)\n"
    SYNTAX += "       -q (quick sync, check for presence of file before downloading)\n"
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
def check_package(packid, packname, realname):
    """Check the package in question against the recorded hpap-data
     dataframe.

     If the new package is not found in the recorded hpap-data dataframe,
     download the file.

     If it is found check:

        If the new package name is different than the previous,
        download the file.

        Else - pass.

    """
    if packname in data_df.file_name_clean.values.tolist():
        row = data_df[data_df['file_name_clean']==packname]
        old_packname = row['file_name_clean'].astype(str).values[0]
        if os.path.isfile(realname):
            return "Pass"
    return "Download"
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
        try:
            pkgname = package.name
        except AttributeError:
            return

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
                    try:
                        os.rename(str(dlname), filename)
                    except OSError:
                        None
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
    # Remove Blackfynn :package: ending to match local paths
    dspaths = [":".join(x.split(":",2)[:2]) for x in dspaths]
    locpaths.sort(reverse=True)

    for i in range(len(locpaths)):
        if locpaths[i] not in dspaths:
            printf("%s does not exist in dataset, \n\tremoving ", locpaths[i])
            printf("%s\n", locpaths[i])

            if os.path.isdir(locpaths[i]):
               print(os.getcwd(), locpaths[i])
               os.removedirs(locpaths[i])
            elif os.path.isfile(locpaths[i]):
               print(os.getcwd(), locpaths[i])
               os.unlink(locpaths[i])
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
# program starts HERE
bf = Blackfynn()  # use 'default' profile
outdir = './'
NODATA = MIRROR = EXCEPT = DATASET = CATEGORY = False
REFRESH = True # default value
QUICKSYNC = False
HPAPURL = 'https://hpap.pmacs.upenn.edu/services/refreshDirectories'

if len(sys.argv) < 2:
    printf("%s\n", syntax())
    sys.exit()

argv = sys.argv[1:]

try:
    opts, args = getopt.getopt(argv, "hlp:d:c:e:q", ['mirror', 'nodata', 'norefresh', 'refresh'])
except getopt.GetoptError:
    printf("%s\n", syntax())
    sys.exit()

dsets, dsdict = get_datasets()
#################
# process options
#################
for opt, arg in opts:
    if opt == '-h':
        printf("%s\n", syntax())
        sys.exit()
    elif opt == '--mirror':
        MIRROR = True
    elif opt == '--norefresh':
        REFRESH = False
    elif opt == '-e':
        EXCEPT = True
        exfile = arg
    elif opt == '--nodata':
        NODATA = True
    elif opt in ('-p'):
        outdir = arg
        if not os.path.exists(outdir): os.makedirs(outdir)
        if outdir == '.': outdir = os.getcwd()
    elif opt in ('-l'):
        for ds in dsets: printf("%s\n", ds[0])
        sys.exit()
    elif opt in ('-c'):
        CATEGORY = True
        cat = arg
        if cat not in categories:
            printf("Category, %s, does NOT exist.\n", arg)
            sys.exit()
    elif opt in ('-d'):
        DATASET = True
        try:
            dsname = arg
            if dsname.lower() != "all":
                dset = bf.get_dataset(dsdict[dsname])
            else:
                dset = "all"
        except:
            printf("Dataset, %s, does NOT exist.\n", arg)
            sys.exit()
    elif opt == '-q':
        QUICKSYNC = True
#################
# start the sync
#################
if DATASET and dsname != "all":
    printf("Gathering Collections from %s ...\n",dset.name)
    collections = list()
    dslist = get_collections(dset,collections)
    dspaths,relpaths = create_paths(dsname, outdir, dslist)
    dspaths.sort()

    if EXCEPT:
        with open(exfile) as f:
            exlist = f.read().splitlines()
    else:
        exlist = list()

    printf("\nCreating local directory structure in %s if necessary\n", outdir)
    for i in dspaths:
        if not os.path.isdir(i):
            if ':package:' in i: continue
            if not excepted(i, exlist): continue
            os.makedirs(i)

    if not NODATA:
        start = time.time()
        pkgpaths = list()
        printf("\nRetrieving Dataset packages to %s\n", outdir)
        for i in dspaths:
            if CATEGORY:
                if cat not in i:
                    continue
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
elif dsname.lower() == "all":
    # Iterate through all HPAP-000 (00D0000) keys and download
    printf("\nGathering all HPAP Datasets ... \n")
    dspaths = []
    relpaths = []
    for dataset in [x for x in dsets if re.match(r"HPAP-\d{3}\s\(\d{2}\D\d{4}\)", x[1])]:
        dsname = dataset[0]
        dset = bf.get_dataset(dsdict[dsname])
        printf("Gathering Collections from %s ...\n",dset.name)
        collections = list()
        dslist = get_collections(dset,collections)
        d_dspaths,d_relpaths = create_paths(dsname, outdir, dslist)
        dspaths.extend(d_dspaths)
        relpaths.extend(d_relpaths)

    dspaths.sort()

    if EXCEPT:
        with open(exfile) as f:
            exlist = f.read().splitlines()
    else:
        exlist = list()

    printf("\nCreating local directory structure in %s if necessary\n", outdir)
    for i in dspaths:
        if not os.path.isdir(i):
            if ':package:' in i: continue
            if not excepted(i, exlist): continue
            os.makedirs(i)

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
            "All Donors", time.time() - start)

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


if MIRROR and DATASET:
    printf("\nMirroring Dataset and Local...\n\n")
    rootdir = outdir + '/' + dsname
    locpaths = localpaths(rootdir, not NODATA)
    mirror(dspaths, locpaths, rootdir)
elif MIRROR and not DATASET:
    printf("\nMirroring All Datasets and Local...\n\n")
    rootdir = outdir
    locpaths = localpaths(rootdir, not NODATA)
    mirror(dspaths, locpaths, rootdir)

if REFRESH:
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    a = requests.put(HPAPURL, verify=False)
    if '200' not in str(a):
        printf("PUT request Failed: %s returned from %s\n", str(a), HPAPURL)
    else:
        printf("Refresh signal sent to hpap web server.\n")
