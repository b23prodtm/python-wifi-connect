#!/usr/bin/env bash

# Command line args:
#  -a <HTTP server address>     Default: 192.168.42.1
#  -p <HTTP server port>        Default: 80
#  -u <UI directory to serve>   Default: "../ui"
#  -d Delete Connections First  Default: False
#  -r Device Registration Code  Default: ""
#  -h Show help.

# Check OS we are running on.  NetworkManager only works on Linux.
if [[ "$OSTYPE" != "linux"* ]]; then
    echo "ERROR: This application only runs on Linux."
    exit 1
fi

# Save the path to THIS script (before we go changing dirs)
TOPDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
# The top of our source tree is the parent of this scripts dir
cd $TOPDIR

# Introduced in supervisor v1.6. Returns the current device state
export BALENA_SUPERVISOR_DEVICE="$BALENA_SUPERVISOR_ADDRESS/v1/device?apikey=$BALENA_SUPERVISOR_API_KEY"
printf "curl -X GET --header \"Content-Type:application/json\" %s/v1/device?apikey=%s\n" $BALENA_SUPERVISOR_ADDRESS $BALENA_SUPERVISOR_API_KEY
export BALENA_SUPERVISOR_DEVICE=$(curl -X GET --header "Content-Type:application/json" $BALENA_SUPERVISOR_DEVICE)
printf "  %s\n" $BALENA_SUPERVISOR_DEVICE

# Sometimes it takes a couple of seconds to connect the wifi,..
sleep 15
# Use the venv
source $TOPDIR/venv/bin/activate
# Start our application
python3 $TOPDIR/src/http_server.py -u $TOPDIR/ui/ $*
