# start / stop the dnsmasq process

import subprocess, time, os

DEFAULT_GATEWAY=os.getenv("DEFAULT_GATEWAY", "192.168.42.1")
DEFAULT_DHCP_RANGE=os.getenv("DEFAULT_DHCP_RANGE","192.168.42.2,192.168.42.254")
DEFAULT_INTERFACE=os.getenv('DEFAULT_INTERFACE',"wlan0") # use 'ip link show' to see list of interfaces

def stop():
    ps = subprocess.Popen("ps -e | grep ' dnsmasq' | cut -c 1-6", shell=True, stdout=subprocess.PIPE)
    pid = ps.stdout.read()
    ps.stdout.close()
    ps.wait()
    pid = pid.decode('utf-8')
    pid = pid.strip()
    if 0 < len(pid):
        print("Killing dnsmasq, PID='{}'".format(pid))
        ps = subprocess.Popen("kill -9 {pid}", shell=True)
        ps.wait()


def start():
    # first kill any existing dnsmasq
    stop()

    # build the list of args
    args = ["dnsmasq"]
    args.append("--listen-address=/#/{DEFAULT_GATEWAY}")
    args.append("--dhcp-range={DEFAULT_DHCP_RANGE}")
    args.append("--dhcp-option=option:router,{DEFAULT_GATEWAY}")
    args.append("--interface={DEFAULT_INTERFACE}")
    args.append("--keep-in-foreground")
    args.append("--bind-interfaces")
    args.append("--except-interface=lo")
    args.append("--dhcp-authoritative")
    args.append("--no-hosts" )

    # run dnsmasq in the background and save a reference to the object
    ps = subprocess.Popen(args)
    # don't wait here, proc runs in background until we kill it.

    # give a few seconds for the proc to start
    time.sleep(2)
    print('Started dnsmasq, PID={}'.format(ps.pid))
