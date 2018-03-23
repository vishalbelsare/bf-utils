#!/bin/bash
#===============================================================================
#
#          FILE:  install.sh
# 
#         USAGE:  ./install.sh  [install_directory]
# 
#   DESCRIPTION:  Install blackfynn utilities
# 
#       OPTIONS:  ---
#  REQUIREMENTS:  ---
#          BUGS:  ---
#         NOTES:  ---
#        AUTHOR:  Pete Schmitt (debtfree), pschmitt@upenn.edu
#       COMPANY:  University of Pennsylvania
#       VERSION:  1.0
#       CREATED:  03/21/2018 17:16:15 EDT
#      REVISION:  ---
#===============================================================================
syntax() {
    echo
    echo "./install.sh [install_directory] (default: \$HOME/bin)"
    echo
    exit 0
}
################################################################################
# start here

if test "$1" = "-h"
then
    syntax
fi
#
# check for custom INSTDIR
#
if test "$1" = ""
then
    INSTDIR=$HOME/bin
else
    INSTDIR=$1
fi
PATH2APPEND="export PATH=${INSTDIR}:\$PATH"
#
# check INSTDIR in $PATH
#
if 
    echo $PATH | grep $INSTDIR > /dev/null
then
    echo "$INSTDIR already in your \$PATH"
    pathyn="n"
else
    echo "$INSTDIR is NOT in your \$PATH"
    echo -n "Do you want to add $INSTDIR to your \$PATH? [Y/n] "
    read pathyn
    if test "$pathyn" = ""
    then
        pathyn="Y"
    fi
fi
#
# check INSTDIR exists and directory
#
if test -d $INSTDIR
then
    echo "$INSTDIR already exists"
    diryn="n"
else
    echo -n "$INSTDIR does not exist.  Create it? [Y/n] "
    read diryn
    if test "$diryn" = ""
    then
        diryn="Y"
    fi
fi
#
# Check with the user if they want to proceed.
#
echo -n "Are you ready to install the software? [Y/n] "
read yn
if test "$yn" = "" -o "$yn" = 'Y'
then
    echo "Installing Software!!"
    echo
else
    echo "Exiting..."
    echo
    exit 0
fi
#
# Add INSTDIR path to end of $HOME/.bashrc if necessary
#
if test $pathyn = "Y"
then
    echo "Adding $INSTDIR to your path..."
    echo "$PATH2APPEND" >> ~/.bashrc
    echo "The new PATH will take effect on next login"
fi
#
# make INSTDIR if necessary
#
if test $diryn = "Y"
then
    mkdir -vp $INSTDIR
fi
#
#  Copy distro programs to INSTDIR
#
echo "Installing blackfynn utilities into $INSTDIR ..."
for i in bf*.py bfdu.sh
do
    F=`echo $i | cut -f1 -d.`
    if test -f ${INSTDIR}/$F
    then
        echo -n "Overwrite existing $F [Y/n] "
        read yn
        if test "$yn" = "Y" -o "$yn" = ""
        then
            cp -v $i ${INSTDIR}/$F
        fi
    else
        cp -v $i ${INSTDIR}/$F
    fi
done
