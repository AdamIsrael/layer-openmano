#!/bin/sh
OPENMANO_TENANT=`/home/openmanod/bin/openmano tenant-create mytenant --description=mytenant |gawk '{print $1}'`
#echo -e "\nexport OPENMANO_TENANT=$OPENMANO_TENANT " >> /home/openmanod/.bashrc
