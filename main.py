from deebotozmo import *
import configparser
from deebotozmo.cli import *
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
import json
import os
import sys
import logging
import time

from ObservableVacBot import *


logging.basicConfig(stream=sys.stdout, format='%(asctime)s: %(name)s %(levelname)s: %(message)s')
log = logging.getLogger(__name__)
log.level = logging.INFO

# reading config from env
config = {
    'email' : os.environ.get('email',''),
    'password' : os.environ.get('password',''),
    'device_id' : os.environ.get('device_id',''),
    'country' : os.environ.get('country','').lower(),
    'continent' : os.environ.get('continent','').lower(),
    'verify_ssl' : os.environ.get('verify_ssl',''),
    'mqtt_client_id' : os.environ.get('mqtt_client_id',''),
    'mqtt_client_host' : os.environ.get('mqtt_client_host',''),
    'mqtt_client_port' : os.environ.get('mqtt_client_port',''),
    'mqtt_client_username' : os.environ.get('mqtt_client_username', ''),
    'mqtt_client_password' : os.environ.get('mqtt_client_password', ''),
    'mqtt_client_keepalive' : os.environ.get('mqtt_client_keepalive',''),
    'mqtt_client_bind_address' : os.environ.get('mqtt_client_bind_address',''),
    'mqtt_client_root_topic' : os.environ.get('mqtt_client_root_topic','')
}

log.debug("Starting with configuration: {}".format(str(config)))
try:
    # init the api
    api = EcoVacsAPI(config['device_id'], config['email'], EcoVacsAPI.md5(config['password']),  config['country'], config['continent'])

    # first device in list
    my_vac = api.devices()[0]
except e:
    log.error("Could not open Ecovacs API", exc_info=e)
# Device ID for a future multi device version
if my_vac is not None:
    did=str(my_vac['did'])
    log.debug("Device ID: "+did)
else: 
    log.error("Could not connect to EcoVaps {}".format(config['device_id']))


try:
    vacbot = ObservableVacBot(api.uid, api.REALM, api.resource, api.user_access_token, my_vac, config['continent'])
    vacbot.connect_and_wait_until_ready()
except e:
    log.error("Could not connect to Deebot", exc_info=e)

# MQTT INIT
try:
    log.debug("Connecting to MQTT host {} with user {}".format(config['mqtt_client_host'], config['mqtt_client_username']))
    mqttclient = mqtt.Client(config['mqtt_client_id'])
    mqttclient.enable_logger(logger=logging.getLogger('mqtt_client'))
    if config['mqtt_client_username']:
        log.debug("MQTT User \'{}\' supplied, using it to log in to MQTT server".format(config['mqtt_client_username']))
        mqttclient.username_pw_set(config['mqtt_client_username'], config['mqtt_client_password'])
    mqttclient.connect(host=config['mqtt_client_host'], port=int(config['mqtt_client_port']), keepalive=int(config['mqtt_client_keepalive']),bind_address=config['mqtt_client_bind_address'])
    log.debug("Connected to MQTT host")
    
except e:
    log.error("Could not connect to MQTT Server {}".format(config["mqtt_client_host"], exc_info=e))



## ECOVACS ---> MQTT
## Callback functions. Triggered when sucks receives a status change from Ecovacs.

## Callback function for battery events 
def battery_report(level):    
    mqttpublish(did,"battery_level",str(level))

# Callback function for status events
def status_report(status):
    mqttpublish(did,"status",status)
    
# Callback function for lifespan (components) events
def lifespan_report(event):
    response = event['body']['data'][0]

    type = COMPONENT_FROM_ECOVACS[response['type']]
        
    left = int(response['left'])
    total = int(response['total'])        
    lifespan = (left/total) * 100

    mqttpublish(did, "components/" + type, lifespan)

def fan_speed_report(speed):
    mqttpublish(did, "fanspeed", speed)

def clean_log_report(event):
    (logs, image) = event
    #mqttpublish(did,"lastCleanLogs", logs)
    mqttpublish(did,"last_clean_image", image)

def water_level_report(event):
    (water_level,mop_attached) = event
    mqttpublish(did, "water_level", water_level)
    mqttpublish(did, "mop_attached", mop_attached)

def stats_events_report(event):
    response = event['body']

    if response['code'] == 0:
        if 'area' in  response['data']:
            stats_area = response['data']['area']
            mqttpublish(did,"stats_area", stats_area)

        if 'cid' in  response['data']:
            stats_cid = response['data']['cid']
            mqttpublish(did,"stats_cid", stats_cid)
        
        if 'time' in  response['data']:
            stats_time = response['data']['time'] / 60
            mqttpublish(did,"stats_time", stats_time)

        if 'type' in response['data']:
            stats_type = response['data']['type']
            mqttpublish(did,"stats_type", stats_type)

# Callback function for error events
# THIS NEEDS A LOT OF WORK
def error_report(event):
    error_str=str(event)
    mqttpublish(did,"error",error_str)
    log.error("Error: "+error_str)


# Publish to MQTT. Root topic should be in a config file or at least defined at the top.
def mqttpublish(did,subtopic,message):
    topic=config['mqtt_client_root_topic']+"/"+did+"/"+subtopic
    try:
        mqttclient.publish(topic, message)
        log.info("Published message \'{}\' to topic \'{}\'".format(message, topic))
    except e:
        log.error("Error publishing MQTT message", exc_info=e)

vacbot.errorEvents.subscribe(error_report)
vacbot.lifespanEvents.subscribe(lifespan_report)

vacbot.fanspeedEvents.subscribe(fan_speed_report)
vacbot.cleanLogsEvents.subscribe(clean_log_report)
vacbot.waterEvents.subscribe(water_level_report)          
vacbot.batteryEvents.subscribe(battery_report)
vacbot.statusEvents.subscribe(status_report)
vacbot.statsEvents.subscribe(stats_events_report)


# For the first run, try to get & report all statuses
vacbot.setScheduleUpdates()
vacbot.refresh_statuses()
vacbot.refresh_components()

# Publish all known rooms by thier id and type
for room in vacbot.getSavedRooms():
    mqttpublish(did, "rooms/{}".format(room['id']), room['subtype'])


## MQTT ----> Ecovacs
# Subscribe to this ecovac topics, translate mqtt commands into sucks commands to robot
subscribe_topic=config['mqtt_client_root_topic']+"/"+did+"/command"
log.debug("Subscribe topic: "+subscribe_topic)
mqttclient.subscribe(subscribe_topic)

def on_message(client, userdata, message):
    received_command=str(message.payload.decode("utf-8")).lstrip()
    log.debug("message received=-"+received_command+"-")
    log.debug("message topic=",message.topic)
    log.debug("message qos=",message.qos)
    log.debug("message retain flag=",message.retain)
    if received_command == "Clean":  
        vacbot.Clean()
    elif received_command == "CleanPause":
        vacbot.CleanPause()
    elif received_command == "CleanResume":
        vacbot.CleanResume()
    elif received_command == "Charge":
        vacbot.Charge()
    elif received_command == "PlaySound":
        vacbot.PlaySound()
    elif received_command == "Relocate":
        vacbot.Relocate()
    elif received_command == "GetCleanLogs":
        vacbot.GetCleanLogs()
    elif received_command == "CustomArea":
        pass
        #vacbot.CustomArea()
    elif received_command.startswith("SpotArea:"):
        area = received_command[9:]
        log.info("Cleaing area: " + area)
        pass
        vacbot.SpotArea(area)
    elif received_command == "SetFanSpeed":
        vacbot.SetFanSpeed(speed=0)
    elif received_command == "SetWaterLevel":
        pass
        #vacbot.SetWaterLevel()
    else:
        log.debug("Unknown command")
        
mqttclient.on_message=on_message

mqttclient.loop_forever()
