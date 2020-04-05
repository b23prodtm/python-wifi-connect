#!/usr/bin/env python3
# Our main wifi-connect application, which is based around an HTTP server.

import os, getopt, sys, json, atexit
import bluetooth, re, subprocess, time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs
from io import BytesIO


# Local modules
import netman
import dnsmasq

def bln_device_fetch(attribute='ip_address', idx=0):
    bln_device = os.getenv('BALENA_SUPERVISOR_DEVICE', None)
    if bln_device:
        data = json.loads(bln_device)
        host_ip = str(data[attribute])
        print('Host IP address:', host_ip)
        return host_ip.split(' ')[idx]
    elif attribute == 'ip_address':
        return netman.get_Host_name_IP()
    else:
        return False

# Defaults
ADDRESS = os.getenv('DEFAULT_GATEWAY', bln_device_fetch())
PORT = 80
UI_PATH = '../ui'
BT_BLE = os.getenv('BT_BLE', 0)

if BT_BLE:
    from bluetooth.ble import DiscoveryService

def bt_service(addr, proto_port="", *serv):
    """
    Name:        Audio Sink
    Description: Headset Audio Gateway
    Protocol:    L2CAP
    Provider:    Toshiba
    Port:        25
    Service id:  None
        print " Name: %s" % (services["name"])
        print " Description: %s" % (services["description"])
        print " Protocol: %s" % (services["protocol"])
        print " Provider: %s" % (services["provider"])
        print " Port: %s" % (services["port"])
        print " Service id: %s" % (services["service-id"])
    """
    for services in bluetooth.find_service(address=addr):
        if len(serv) > 0 and (services["name"] in serv or services["service-id"] in serv):
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

def bt_connect_service(nearby_devices, bt_addr="00:00:00:00:00:00", proto_port="", serv=""):
    for addr, name in nearby_devices:
        sock = None
        if bt_addr == "00:00:00:00:00:00":
            print("  - %s , %s:" % (addr, name))
            sock = bt_service(addr, proto_port, serv)
        elif bt_addr == addr:
            print("  - found device %s , %s:" % (addr, name))
            sock = bt_service(addr, proto_port, serv)
        if sock:
            print("  - service %s available" % (serv))
            return sock

#------------------------------------------------------------------------------
# called at exit
def cleanup():
    print("Cleaning up prior to exit.")
    dnsmasq.stop()
    if not int(os.getenv('DISABLE_HOTSPOT', 0)):
        netman.stop_hotspot()


#------------------------------------------------------------------------------
# A custom http server class in which we can set the default path it serves
# when it gets a GET request.
class MyHTTPServer(HTTPServer):
    def __init__(self, base_path, server_address, RequestHandlerClass):
        self.base_path = base_path
        HTTPServer.__init__(self, server_address, RequestHandlerClass)


#------------------------------------------------------------------------------
# A custom http request handler class factory.
# Handle the GET and POST requests from the UI form and JS.
# The class factory allows us to pass custom arguments to the handler.
def RequestHandlerClassFactory(address, nearby_devices, pincode, trusted_devices):

    class MyHTTPReqHandler(SimpleHTTPRequestHandler):

        def __init__(self, *args, **kwargs):
            # We must set our custom class properties first, since __init__() of
            # our super class will call do_GET().
            self.address = address
            self.nearby_devices = nearby_devices
            self.pincode = pincode
            self.trusted_devices = ()
            super(MyHTTPReqHandler, self).__init__(*args, **kwargs)

        # See if this is a specific request, otherwise let the server handle it.
        def do_GET(self):

            print('do_GET {}'.format(self.path))

            # Handle the hotspot starting and a computer connecting to it,
            # we have to return a redirect to the gateway to get the
            # captured portal to show up.
            if '/hotspot-detect.html' == self.path:
                self.send_response(301) # redirect
                new_path = 'http://{}/'.format(self.address)
                print('redirecting to {}'.format(new_path))
                self.send_header('Location', new_path)
                self.end_headers()

            # Handle a REST API request to return the device registration code
            if '/pincode' == self.path:
                self.send_response(200)
                self.end_headers()
                response = BytesIO()
                response.write(self.pincode.encode('utf-8'))
                print('GET {} returning: {}'.format(self.path, response.getvalue()))
                self.wfile.write(response.getvalue())
                return

            # Handle a REST API request to return the list of nearby_devices
            if '/devices' == self.path:
                # Update the list of nearby_devices since we are not connected
                self.nearby_devices = discover_devices(trusted_devices = self.trusted_devices)
                self.send_response(200)
                self.end_headers()
                response = BytesIO()
                """ map whatever we get from bluetooth to our constants:
                Device - 00:16:BC:30:D8:76
                """
                response.write(json.dumps(self.nearby_devices).encode('utf-8'))
                print('GET {} returning: {}'.format(self.path, response.getvalue()))
                self.wfile.write(response.getvalue())
                return

            # Not sure if this is just OSX hitting the captured portal,
            # but we need to exit if we get it.
            if '/bag' == self.path:
                sys.exit()

            # All other requests are handled by the server which vends files
            # from the ui_path we were initialized with.
            super().do_GET()


        # test with: curl localhost:5000 -d "{'name':'value'}"
        def do_POST(self):
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            self.send_response(200)
            self.end_headers()
            response = BytesIO()
            fields = parse_qs(body.decode('utf-8'))
            #print('POST received: {}'.format(fields))

            # Parse the form post
            FORM_BTADDR = 'bt_addr'
            FORM_SERVICE = 'service'
            FORM_PROTOCOL = 'protoport'

            if FORM_BTADDR not in fields:
                print('Error: POST is missing {} field.'.format(FORM_BTADDR))
                return

            bt_addr = fields[FORM_BTADDR][0]
            protoport = None
            service = None
            if FORM_SERVICE in fields:
                service = fields[FORM_SERVICE][0]
            if FORM_PROTOCOL in fields:
                protoport = fields[FORM_PROTOCOL][0]

            if not int(os.getenv('DISABLE_HOTSPOT', 0)):
                # Stop the hotspot
                netman.stop_hotspot()

            # Connect to the user's selected AP
            sock = None
            success='{} Connected: Yes\n'.format(bt_addr)
            error='{} Connected: No\n'.format(bt_addr)
            try:
                sock = bt_connect_service(self.nearby_devices, bt_addr, protoport, service)
                if sock:
                    response.write(success.encode())
                    sock.close()
                else:
                    response.write(error.encode())
            except bluetooth.btcommon.BluetoothError as err:
                print(" Main thread error : %s" % (err))
                exit(1)

            self.wfile.write(response.getvalue())

            # Handle success or failure of the new connection
            if response.getvalue() is success:
                print('Connected! Display device information.')
                self.trusted_devices += (bt_addr, self.nearby_devices[bt_addr])
            else:
                print('Connection failed, restarting the hotspot.')
                # Update the list of nearby_devices since we are not connected
                self.nearby_devices = discover_devices()
            if not int(os.getenv('DISABLE_HOTSPOT', 0)):
                # Start the hotspot again
                netman.start_hotspot()

    return  MyHTTPReqHandler # the class our factory just created.

def discover_devices(timeout = 5, trusted_devices = ()):
    print("looking for nearby devices...")
    try:
        nearby_devices = trusted_devices + tuple(bluetooth.discover_devices(lookup_names = True, flush_cache = True, duration = timeout))
        if BT_BLE:
            service = DiscoveryService()
            devices = service.discover(timeout)

            nearby_devices += tuple(devices.items())

        print("found %d devices" % len(nearby_devices))
        return nearby_devices
    except bluetooth.btcommon.BluetoothError as err:
        print(" Main thread error : %s" % (err))
        exit(1)

#------------------------------------------------------------------------------
# Create the hotspot, start dnsmasq, start the HTTP server.
def main(address, port, ui_path, pincode, service, protoport):
    nearby_devices = discover_devices()
    if not int(os.getenv('DISABLE_HOTSPOT', 0)):
        # Start the hotspot
        if not netman.start_hotspot():
            print('Error starting hotspot, exiting.')
            sys.exit(1)
        # Start dnsmasq (to advertise us as a router so captured portal pops up
        # on the users machine to vend our UI in our http server)
        dnsmasq.start()

    # Find the ui directory which is up one from where this file is located.
    web_dir = os.path.join(os.path.dirname(__file__), ui_path)
    print('HTTP serving directory: {} on {}:{}'.format(web_dir, address, port))

    # Change to this directory so the HTTPServer returns the index.html in it
    # by default when it gets a GET.
    os.chdir(web_dir)

    # Host:Port our HTTP server listens on
    server_address = (address, port)

    # Custom request handler class (so we can pass in our own args)
    MyRequestHandlerClass = RequestHandlerClassFactory(address, nearby_devices, pincode, ())

    # Start an HTTP server to serve the content in the ui dir and handle the
    # POST request in the handler class.
    print('Waiting for a connection to our hotspot {}: {}...'.format(netman.get_hotspot_SSID(), server_address))
    httpd = MyHTTPServer(web_dir, server_address, MyRequestHandlerClass)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        # dnsmasq.stop()
        # netman.stop_hotspot()
        httpd.server_close()


#------------------------------------------------------------------------------
# Util to convert a string to an int, or provide a default.
def string_to_int(s, default):
    try:
        return int(s)
    except ValueError:
        return default


#------------------------------------------------------------------------------
# Entry point and command line argument processing.
if __name__ == "__main__":
    atexit.register(cleanup)

    address = ADDRESS
    port = PORT
    ui_path = UI_PATH
    pincode = '0000'

    service = 'Audio Sink'
    protoport = str(bluetooth.L2CAP) + ":25"

    myenv = dict()
    main.defaults = dict()
    main.defaults = {
        "address": address,
        "port": str(port),
        "ui_path": ui_path,
        "pincode": str(pincode),
        "service": service
        }
    myenv.update(main.defaults)
    myenv.update(os.environ)

    usage = ''\
'Command line args: \n'\
'  -a <HTTP server address>     Default: {} \n'\
'  -p <HTTP server port>        Default: {} \n'\
'  -u <UI directory to serve>   Default: "{}" \n'\
'  -r Device Registration Code  Default: "{}" \n'\
'  -s,--uuid <service-name>     Default: {}\n'\
'  --protocol <proto:port>      Default: {}\n'\
'  --ble                        Default: None\n'\
'  -h,--help Show help.\n'.format(address, port, ui_path, pincode, service, protoport)

    try:
        opts, args = getopt.getopt(sys.argv[1:], "a:p:u:r:s:h",["help", "ble", "uuid=", "protocol="])
    except getopt.GetoptError:
        print(usage)
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(usage)
            sys.exit()

        elif opt in ("-a"):
            address = arg

        elif opt in ("-p"):
            port = string_to_int(arg, port)

        elif opt in ("-u"):
            ui_path = arg

        elif opt in ("-r"):
            pincode = arg

        elif opt in ("-s", "--uuid"):
            service = arg

        elif opt in ("--protocol"):
            protoport = arg

        elif opt in ("--ble"):
            BT_BLE = 1

        else:
            print("Wrong argument %s %s !" % (opt, arg))
            print(usage)

    os.environ.update(main.defaults)

    print('Address={} '\
          'Port={}\n'\
          'UI path={} '\
          'Bluetooth Low Energy={} '
          'Device registration code={}'.format(address, port, ui_path, BT_BLE, pincode))
    main(address, port, ui_path, pincode, service, protoport)
