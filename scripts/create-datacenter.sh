#!/bin/sh
HOME=/home/openmanod
OPENMANO=$HOME/bin/openmano
export OPENMANO_TENANT=$4

OPENMANO_DATACENTER=`$OPENMANO datacenter-list myov`
if [ $? -ne 0 ]; then
    OPENMANO_DATACENTER=`$OPENMANO datacenter-create myov http://$1:$2/openvim`
fi
export OPENMANO_DATACENTER=`echo $OPENMANO_DATACENTER |gawk '{print $1}'`

#export OPENMANO_DATACENTER=`$OPENMANO datacenter-create myov http://$1:$2/openvim |gawk '{print $1}'`
# FIXME: don't add this to .bashrc if it already exists.
if ! grep -q "^export OPENMANO_DATACENTER" $HOME/.bashrc
then
    echo "export OPENMANO_DATACENTER=$OPENMANO_DATACENTER " >> $HOME/.bashrc
fi

# TODO: Test idempotency. We may need to check and remove existing data
$OPENMANO datacenter-attach myov --vim-tenant-name $3
$OPENMANO datacenter-netmap-import -f --datacenter $OPENMANO_DATACENTER
