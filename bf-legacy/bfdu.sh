#!/bin/bash
#===============================================================================
#
#          FILE:  bfdu.sh
# 
#         USAGE:  ./bfdu.sh  <directory>
# 
#   DESCRIPTION:  run du -s and subtract directory sizes (4K each))
# 
#       UPDATES:  171208: added syntax check
#                 171214: ensured argument was type directory
#                 171215: switched to printf statement for more format control
#                 180119: fixed issued with dir names with spaces
#         NOTES:  assumes 4K directory size
#        AUTHOR:  Pete Schmitt (hpap), pschmitt@upenn.edu
#       COMPANY:  University of Pennsylvania
#       VERSION:  0.1.2
#       CREATED:  12/08/2017 11:32:11 AM EST
#      REVISION:  Fri Jan 19 13:14:24 EST 2018
#===============================================================================
DIR="$*"

if test "$DIR" = ""
then
    echo "Syntax: bfdu <directory>"
    exit 0
elif ! test -d "$DIR"
then
    echo "Syntax: bfdu <directory>"
    exit 0
fi

dirsize=0
dircnt=`find "$DIR" -type d | wc -l`
dirsize=$((dircnt * 4))
duout=`du -s "$DIR" | awk '{print $1}'`
total=$((duout - dirsize))

printf "%-7d %s\n" $total "$DIR"
