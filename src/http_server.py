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

def bt_connect_service(nearby_devices, btsink="00:00:00:00:00:00", proto_port="", serv=""):
    for addr, name in nearby_devices:
        sock = None
        if btsink == "00:00:00:00:00:00":
            print("  - %s , %s:" % (addr, name))
            sock = bt_service(addr, proto_port, serv)
        elif btsink == addr:
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
def RequestHandlerClassFactory(address, nearbydevices, pincode):

    class MyHTTPReqHandler(SimpleHTTPRequestHandler):

        def __init__(self, *args, **kwargs):
            # We must set our custom class properties first, since __init__() of
            # our super class will call do_GET().
            self.address = address
            self.nearbydevices = nearbydevices
            self.pincode = pincode
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

            # Handle a REST API request to return the list of nearbydevices
            if '/devices' == self.path:
                # Update the list of nearbydevices since we are not connected
                self.nearbydevices = bluetooth.discover_devices(lookup_names = True, flush_cache = True, duration = int(os.environ["BTSPEAKER_SCAN_DURATION"]))

                self.send_response(200)
                self.end_headers()
                response = BytesIO()
                """ map whatever we get from bluetooth to our constants:
                Device - 00:16:BC:30:D8:76
                """
                response.write(json.dumps(self.nearbydevices).encode('utf-8'))
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
            success='OK\n'
            error='ERROR\n'
            try:
                bt_connect_service(self.nearby_devices, bt_addr, protoport, service)
                if sock:
                    response.write(b'{}'.format(success))
                    # pair the new device as known device
                    print("bluetooth pairing...")
                    ps = subprocess.Popen("printf \"pair %s\\nexit\\n\" \"$1\" | bluetoothctl", shell=True, stdout=subprocess.PIPE)
                    print(ps.stdout.read())
                    ps.stdout.close()
                    ps.wait()
                    sock.close()
                else:
                    response.write(b'{}'.format(error))
            except bluetooth.btcommon.BluetoothError as err:
                print(" Main thread error : %s" % (err))
                exit(1)

            self.wfile.write(response.getvalue())

            # Handle success or failure of the new connection
            if response.getvalue() is success:
                print('Connected!  Exiting app.')
                sys.exit()
            else:
                print('Connection failed, restarting the hotspot.')
                # Update the list of nearbydevices since we are not connected
                self.nearbydevices = bluetooth.discover_devices(lookup_names = True, flush_cache = True, duration = int(os.environ["BTSPEAKER_SCAN_DURATION"]))
                if not int(os.getenv('DISABLE_HOTSPOT', 0)):
                    # Start the hotspot again
                    netman.start_hotspot()

    return  MyHTTPReqHandler # the class our factory just created.

#------------------------------------------------------------------------------
# Create the hotspot, start dnsmasq, start the HTTP server.
def main(address, port, ui_path, pincode, timeout, service, protoport, bt_address):
    print("looking for nearby devices...")
    # Get list of available devices from net man.
    nearbydevices = None
    try:
        nearby_devices = bluetooth.discover_devices(lookup_names = True, flush_cache = True, duration = timeout)
        print("found %d devices" % len(nearby_devices))
    except bluetooth.btcommon.BluetoothError as err:
        print(" Main thread error : %s" % (err))
        exit(1)

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
    MyRequestHandlerClass = RequestHandlerClassFactory(address, nearbydevices, pincode)

    # Start an HTTP server to serve the content in the ui dir and handle the
    # POST request in the handler class.
    print('Waiting for a connection to our hotspot {} ...'.format(netman.get_hotspot_SSID()))
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
        "service": service,
        "BTSPEAKER_SCAN_DURATION":"5",
        "BTSPEAKER_SINK":"00:00:00:00:00:00"
        }
    myenv.update(main.defaults)
    myenv.update(os.environ)

    usage = ''\
'Command line args: \n'\
'  -a <HTTP server address>     Default: {address} \n'\
'  -p <HTTP server port>        Default: {port} \n'\
'  -u <UI directory to serve>   Default: "{ui_path}" \n'\
'  -r Device Registration Code  Default: "{pincode}" \n'\
'  -d,--duration <seconds>      Default: {myenv["BTSPEAKER_SCAN_DURATION"]}\n'\
'  -s,--uuid <service-name>     Default: {service}\n'\
'  --protocol <proto:port>      Default: {protoport}\n'\
'  [bt-address]                 Default: {myenv["BTSPEAKER_SINK"]}\n'\
'  -h,--help Show help.\n'

    try:
        opts, args = getopt.getopt(sys.argv[1:], "a:p:u:r:d:s:h",["help", "duration=", "uuid=", "protocol="])
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

        elif opt in ("-d", "--duration"):
            myenv['BTSPEAKER_SCAN_DURATION'] = arg

        elif opt in ("-s", "--uuid"):
            service = arg

        elif opt in ("--protocol"):
            protoport = arg

        elif re.compile("([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}").match(arg):
            myenv["BTSPEAKER_SINK"] = arg

        else:
            print("Wrong argument %s !" % arg)
            print(usage)

    os.environ.update(main.defaults)

    print('Address={}'\
          'Port={}'\
          'UI path={}'\
          'Device registration code={}'\
          'Bluetooth Device={}'.format(address, port, ui_path, pincode, myenv['BTSPEAKER_SINK']))
    main(address, port, ui_path, pincode, int(myenv['BTSPEAKER_SCAN_DURATION']), service, protoport, myenv['BTSPEAKER_SINK'])
