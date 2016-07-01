#!/bin/sh

export OPENMANO_TENANT=$4
export OPENMANO_DATACENTER=`/home/openmanod/bin/openmano datacenter-create myov http://$1:$2/openvim |gawk '{print $1}'`
#echo "export OPENMANO_DATACENTER=$OPENMANO_DATACENTER " >> /home/openmanod/.bashrc
/home/openmanod/bin/openmano datacenter-attach myov --vim-tenant-name $3
