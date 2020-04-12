#!/usr/bin/python
import bluetooth, sys, os, re, subprocess, time, getopt

BT_BLE = int(os.getenv('BT_BLE', 0))
BT_SCAN_TIMEOUT = int(os.getenv('BT_SCAN_TIMEOUT', 2))

if BT_BLE:
    from gattlib import DiscoveryService
    from ble_client import BleClient

def parse_argv (myenv, argv):
    usage = 'Command line args: \n'\
'  -d,--duration <seconds>      Default: {}\n'\
'  -s,--uuid <service-name>     Default: {}\n'\
'  --protocol <proto:port>      Default: {}\n'\
'  [bt-address]                 Default: {}\n'\
'  -h,--help Show help.\n'.format(myenv["BT_SCAN_TIMEOUT"],myenv["service"],myenv["proto-port"],'myenv["BTSPEAKER_SINK"]')
    try:
        opts, args = getopt.getopt(argv[1:], "u:d:s:h",["help", "duration=", "uuid=", "protocol="])
    except getopt.GetoptError:
        print(usage)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(usage)
            sys.exit()
        if opt in ("-d", "--duration"):
            myenv['BT_SCAN_TIMEOUT'] = arg
        elif opt in ("-s", "--uuid"):
            myenv['service'] = arg
        elif opt in ("--protocol"):
            myenv['proto-port'] = arg
        elif re.compile("([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}").match(arg):
            myenv["BTSPEAKER_SINK"] = arg
        else:
            print("Wrong argument %s !" % argv[i])
            print(usage)

def bt_service(addr, proto_port="", serv=""):
    for services in bluetooth.find_service(address=addr):
        if len(serv) > 0 and (services["name"] is serv or services["service-id"] is serv):
            return bt_connect(services["protocol"], addr, services["port"])
        else:
            print("  UUID: %s (%s)" % (services["name"], services["service-id"]))
            print("    Protocol: %s, %s, %s" % (services["protocol"], addr, services["port"]))
    if proto_port != "" and re.compile("[^:]+:[0-9]+").match(proto_port):
        s = proto_port.find(":")
        proto = proto_port[0:s]
        port = proto_port[s+1:]
        return bt_connect(proto, addr, port)

def bt_connect(proto, addr, port):
    timeout = 0
    while timeout < 5:
        try:
            print("  Attempting %s connection to %s (%s)" % (proto, addr, port))
            s = bluetooth.BluetoothSocket(int(proto))
            s.connect((addr,int(port)))
            print("Success")
            return s
        except bluetooth.btcommon.BluetoothError as err:
            print("%s\n" % (err))
            print("  Fail, probably timeout. Attempting reconnection... (%s)" % (timeout))
            timeout += 1
            time.sleep(1)
    print("  Service or Device not found")
    return None
#------------------------------------------------------------------------------
# Connects to Audio Service (Audio Sink, Audio Source, more in bluetoothctl <<EOF
# info <address>
# EOF
# raise bluetooth.btcommon.BluetoothError
def bt_connect_service(nearby_devices, bt_addr="00:00:00:00:00:00", proto_port="", serv=""):
    sock = None
    for addr, name in nearby_devices:
        if bt_addr == "00:00:00:00:00:00":
            print("  - %s , %s:" % (addr, name))
            sock = bt_service(addr, proto_port, serv)
            if sock:
                sock.close()
        elif bt_addr == addr:
            print("  - found device %s , %s:" % (addr, name))
            sock = bt_service(addr, proto_port, serv)
            break
        else:
            continue
    if sock:
        print("  - service %s available" % (serv))
    else:
        print(" - service %s unavailable at %s" % (serv, bt_addr))
    return sock

#------------------------------------------------------------------------------
# Devices discovery with bluetooth low energy (BT_BLE) support
# return devices list in argument (list append)
def discover_devices(nearby_devices = []):
    timeout = BT_SCAN_TIMEOUT
    print("looking for nearby devices...")
    try:
        nearby_devices += bluetooth.discover_devices(lookup_names = True, flush_cache = True, duration = timeout)
        print("found %d devices" % len(nearby_devices))

        if BT_BLE:
            service = DiscoveryService()
            try:
                devices = service.discover(timeout)
                for addr, name in devices.items():
                    if not name or name is "":
                        b = BleClient(addr)
                        name = b.request_data().decode('utf-8')
                        b.disconnect()
                    nearby_devices += ((addr, name))
            except RuntimeError as err:
                print("~ BLE ~ Error ", err)
            else:
                print("found %d devices (ble)" % len(devices.items()))

        return nearby_devices
    except bluetooth.btcommon.BluetoothError as err:
        print(" Main thread error : %s" % (err))
        exit(1)

def main(argv):
    myenv = dict()
    main.defaults = dict()
    main.defaults = {
        "file":argv[0],
        "BT_SCAN_TIMEOUT":"5",
        "service":"Audio Sink",
        "BTSPEAKER_SINK":"00:00:00:00:00:00",
        "proto-port": str(bluetooth.L2CAP) + ":25"
        }
    myenv.update(main.defaults)
    myenv.update(os.environ)
    parse_argv(myenv, argv)
    print("looking for nearby devices...")
    try:
        nearby_devices = discover_devices()
        print("found %d devices" % len(nearby_devices))
        print("discovering %s services... %s" % (myenv["BTSPEAKER_SINK"], myenv["service"]))
        sock = bt_connect_service(nearby_devices, myenv["BTSPEAKER_SINK"], myenv["proto-port"], myenv["service"])
        if sock:
            # pair the new device as known device
            print("bluetooth pairing...")
            ps = subprocess.Popen("printf \"pair %s\\nexit\\n\" \"$1\" | bluetoothctl", shell=True, stdout=subprocess.PIPE)
            print(ps.stdout.read())
            ps.stdout.close()
            ps.wait()
            sock.close()
    except bluetooth.btcommon.BluetoothError as err:
        print(" Main thread error : %s" % (err))
        exit(1)

if __name__ == '__main__':
    main(sys.argv)
