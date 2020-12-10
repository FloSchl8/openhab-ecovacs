# Library for Ecovacs Deebot 960/950/920

A simple library to connect Ecovac Deebots to a MQTT-Broker for usage with OpenHAB or other home automation tools. Currently
known to work with the Ecovacs Deebot 960/950/920 from both North America and Europe.

## Installation

Clone this repository and run like described below. 

There are two methods of running this library:

* Docker
* Python (tested with Python 3.8.5)

### Docker

The easiest was is to use docker-compose. For the library to work, you have to specify some configuration values in an _.env_-File (see [docker docs](https://docs.docker.com/compose/environment-variables/)).  
The _.env_-File must contain the following variables

```
email=your_ecovacs_email
password=ecovacs_password
device_id=randomd_device_id
country=your_country
continent=your_continent
verify_ssl=True
mqtt_client_id=client_name
mqtt_client_host=host_or_ip_of_mqtt_broker
mqtt_client_port=mqtt_port
mqtt_client_keepalive=keep_alive_in_seconds
mqtt_client_bind_address=
mqtt_client_root_topic=root_topic_name
```

You can check the correct values afterwards with `docker-compose config`. If everything is correct you can start the container with `docker-compose up [-d]`

### Python

Set the above mentioned environment variales and run `python main.py`

## Usage

For usage with e.g. openHAB you need the deebot device ID which is retrieved through the API. This device ID is used as subtopic in publishing and recieving messages. To retrieve this ID the easiest way is to start the library and watch the output.

```
openhabdeebot_1  | Device ID: 079a32a4-2650-4f07-9039-6f467024934e
openhabdeebot_1  | ecovacs/079a32a4-2650-4f07-9039-6f467024934e/status STATE_DOCKED
openhabdeebot_1  | ecovacs/079a32a4-2650-4f07-9039-6f467024934e/battery_level 100
...
```

Currently the livemap is updated every 15 seconds (unused at the moment), states every 30 seconds and components every 60 seconds.  
If you wnat to change this, edit `main.py` line 128 and pass in your one values.

```python
vacbot.setScheduleUpdates(livemap_cycle = 60, status_cycle = 120, components_cycle = 240)
```

Currently the following topics for recieving messages exist.

```bash
ecovacs/[device id]/status
ecovacs/[device id]/battery_level
ecovacs/[device id]/fanspeed
ecovacs/[device id]/water_level
ecovacs/[device id]/mop_attached
ecovacs/[device id]/stats_area
ecovacs/[device id]/stats_cid
ecovacs/[device id]/stats_time
ecovacs/[device id]/stats_type
ecovacs/[device id]/components/brush
ecovacs/[device id]/components/sideBrush
ecovacs/[device id]/components/heap
ecovacs/[device id]/last_clean_image
```

To send commands to your Deebot you have to publish to the following topic

`ecovacs/[device id]/command`

Accepted commands are

* "Clean": Deebot starts cleaning
* "CleanPause": Pause while cleaning
* "CleanResume": resume cleaning
* "Charge": return to dock and charge
* "PlaySound": plays the "I am here" sound for locating your Deebot
* "Relocate": sets the relocation status to manual 
* "GetCleanLogs": get the latest cleaning logs
* "SetFanSpeed": sets the fanspeed (currently only to 'normal')

For easier use, you can use the provided examples in [openhab](/openhab)


## Thanks

If you want to support me  
<a href="https://www.buymeacoffee.com/FloSchl" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>

My heartfelt thanks to:

* [And3rsL and his Deebot library](https://github.com/And3rsL/Deebotozmo), without his fork of [sucks](https://github.com/wpietri/sucks) this wouln't be possible and this is also some kind of fork
* [guillebot and his mqtt addon for sucks](https://github.com/guillebot/openhab-sucks) who provided a lot of ideas used in this project
* [xmpppeek](https://www.beneaththewaves.net/Software/XMPPPeek.html),
a great library for examining XMPP traffic flows (yes, your vacuum
speaks Jabbber!),
* [mitmproxy](https://mitmproxy.org/), a fantastic tool for analyzing HTTPS,
* [click](http://click.pocoo.org/), a wonderfully complete and thoughtful
library for making Python command-line interfaces,
* [requests](http://docs.python-requests.org/en/master/), a polished Python
library for HTTP requests,
* [Decompilers online](http://www.javadecompilers.com/apk), which was
very helpful in figuring out what the Android app was up to,
* Albert Louw, who was kind enough to post code from [his own
experiments](https://community.smartthings.com/t/ecovacs-deebot-n79/93410/33)
with his device, and
* All the users who have given useful feedback and contributed code!
