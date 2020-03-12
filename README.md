# python-bt-connect
An application that displays a bluetooth configuration UI for embedded Linux devices.

Inspired by the [wifi-connect](https://github.com/balena-io/wifi-connect) project written by [balena.io](https://www.balena.io/).

# Install and Run

Please read the [INSTALL.md](INSTALL.md) then the [RUN.md](RUN.md) files.


# How it works
![How it works](./docs/images/how-it-works.png?raw=true)

Bluetooth Connect interacts with NetworkManager, which should be the active network manager on the device's host OS.

### 1. Advertise: Device Creates Access Point

WiFi Connect detects available WiFi networks and opens an access point with a captive portal. Connecting to this access point with a mobile phone or laptop allows new WiFi credentials to be configured.

### 2. Connect: User Connects Phone to Device Access Point

Connect to the opened access point on the device from your mobile phone or laptop. The access point SSID is, by default, `Raspibox-<name>` where "name" is something random like "shy-lake" or "green-frog".

### 3. Portal: Phone Shows Captive Portal to User

After connecting to the access point from a mobile phone, it will detect the captive portal and open its web page. Opening any web page will redirect to the captive portal as well.

### 4. Credentials: User Enters Device Information on Phone

The captive portal provides the option to select a Bluettoth Device from a list with detected devices and enter a protocol:port for the desired device.

### 5. Connected!: Device Connects to Bluetooth Device

When the device information's been entered, Bluetooth Connect will disable the access point and try to connect to the device. If the connection fails, it will enable the access point for another attempt. If it succeeds, the configuration will be saved by Bluetooth cache /var/cache/bluetooth/reconnect_device.

# Details
* [Video demo of the application.](https://www.youtube.com/watch?v=TN7jXMmKV50)
* [These are the geeky development details and background on this application.](docs/details.md)
