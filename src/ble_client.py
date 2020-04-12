#!/usr/bin/env python3
"""Original coding:
 PyBluez example read_name.py
Copyright (C) 2014, Oscar Acena <oscaracena@gmail.com>
This software is under the terms of GPLv3 or later.
"""

import sys

from gattlib import GATTRequester

class BleClient:
    def __init__(self, address):
        self.requester = GATTRequester(address, False)
        self.connect()
        self.request_data()

    def connect(self):
        print("~ BLE ~ Connecting...", end=' ')
        sys.stdout.flush()

        self.requester.connect(True)
        print("~ BLE ~ OK!")

        time.sleep(1)

    def disconnect(self):
        print("~ BLE ~ Disconnecting...", end=' ')
        sys.stdout.flush()

        self.requester.disconnect()
        print("~ BLE ~ OK!")

        time.sleep(1)

    def request_data(self, uuid="00002a00-0000-1000-8000-00805f9b34fb"):
        data = self.requester.read_by_uuid(uuid)[0]
        try:
            print("~ BLE ~ Device name:", data.decode("utf-8"))
        except AttributeError:
            print("~ BLE ~ Device name:", data)
        else:
            return data

    def wait_disconnection(self):
        status = "connected" if self.requester.is_connected() else "not connected"
        print("~ BLE ~ Checking current status: {}".format(status))
        print("\n~ BLE ~Now, force a hardware disconnect. To do so, please switch off,\n"
              "reboot or move away your device. Don't worry, I'll wait...")

        while self.requester.is_connected():
            time.sleep(1)

        print("\n~ BLE ~OK. Current state is disconnected. Congratulations ;)")
