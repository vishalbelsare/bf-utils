import sys
import os, errno
import re
import subprocess

ERR_MSG = "define which folder to upload, e.g. python BF.upload.py HPAP-022.mrna"

if(len(sys.argv) <= 1):
    sys.exit(ERR_MSG)

entry = sys.argv[1]

if entry.startswith("HPAP-"):
	t = entry.split('.')
	command = "grep "+ t[0] + " HPAP.list.txt"
	output = os.popen(command).read().strip()
	output = "\"" + output + "\""
	print("pennsieve upload -f -r --dataset "+ output + " " + entry)
	os.system("pennsieve upload -f -r --dataset {} {}".format(output, entry))
else:
    print(ERR_MSG)
