#!/bin/sh
OPENMANO_TENANT=`/home/openmanod/bin/openmano tenant-create mytenant --description=mytenant |gawk '{print $1}'`
echo $OPENMANO_TENANT
