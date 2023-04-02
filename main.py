# Docker Container -  https://shinesolutions.com/2018/09/13/running-a-web-crawler-in-a-docker-container/

import json
from scrapy import signals
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.signalmanager import dispatcher
import paho.mqtt.client as mqtt
import argparse, sys
import time
from queue import Queue


from pyimgscrape.spiders.imgscrape import ImgscrapeSpider

# call spider and return items : https://github.com/scrapy/scrapy/issues/3856
def spider_results(url=None):
    results = []

    def crawler_results(signal, sender, item, response, spider):
        results.append(item)  

    dispatcher.connect(crawler_results, signal=signals.item_passed)

    # running crawler from script: https://docs.scrapy.org/en/latest/topics/practices.html 
    process = CrawlerProcess(get_project_settings())
    process.crawl(ImgscrapeSpider, url=url)
    process.start()
    return results

# ----- MQTT Call Back functions
def on_connect(client, userdata, flags, rc):
    # https://pypi.org/project/paho-mqtt/#on-connect
    match rc:
        case 0:
            print(f"RC = {rc}: Connection Successful.")
            client.connected_flag=True
        case 1:
            print(f"Error Connecting: RC = {rc}: Invalid Protocl Version.")
            client.loop_stop()
            sys.exit()
        case 2:
            print(f"Error Connecting: RC = {rc}: Invalid Client Identifier.")
            client.loop_stop()
            sys.exit()
        case 3:
            print(f"Error Connecting: RC = {rc}: Server Unavailable.")
            client.loop_stop()
            sys.exit()
        case 4:
            print(f"Error Connecting: RC = {rc}: Bad Username or Password.")
            client.loop_stop()
            sys.exit()
        case 5:
            print(f"Error Connecting: RC = {rc}: Not Authorized.")
            client.loop_stop()
            sys.exit()
        case _:
            print( f"Error Connection: RC = {rc}: Currently Unused code.")
            client.loop_stop()
            sys.exit()

def on_message(client, userdata, message):
    # Convert Message to Json object
    message_received=str(message.payload.decode("utf-8"))
    print(f"Recieved Message from broker: {message_received}")
    msg=json.loads(message_received)
    q.put(msg)

def on_publish(client, userdata, mid):
    print("message published." )

def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))
    client.suback_flag=True

def on_disconnect(client, userdata, rc):
    print(f"disconnected OK: RC = {rc}")

# SearchUrl = 'https://nextdoornikki.com/hosted/gal/watermellon/1581254'

if __name__ == '__main__':
    # process inputs
    parser=argparse.ArgumentParser()

    parser.add_argument("-b","--broker", help="MQ Broker",required=True)
    parser.add_argument("-p","--port", help="MQ Read Port",required=True)

    args=parser.parse_args()

    print("args: ")
    print(args)

    # assign to local vars
    broker=args.broker
    port=int(args.port)
    retainflag=True

    # Initialize Client 
    mqtt.Client.connected_flag=False

    client = mqtt.Client("imgget1") 

    # callbacks
    client.on_connect=on_connect  
    client.on_publish=on_publish
    client.on_message=on_message
    client.on_subscribe=on_subscribe
    client.on_disconnect=on_disconnect
    


    print("Connecting to broker ",broker,": ",port)
    client.connect(broker,port) 

    client.loop_start()   

    # Wait for client to connect
    while not client.connected_flag: 
        print("Waiting for MQTT Connection.")
        time.sleep(1)
    
    client.subscribe("/imgscrape/input",qos=1)

    # Continue forever (loop_forever is giving me problems)
    q=Queue()
    try:
        while True:
            time.sleep(1)
            # print("Retrieving Messages...")

            # pulling data from message into queue
            while not q.empty():
                message = q.get()
                if message is None:
                    continue

                print(f"Scraping site: {message['Url']}")
                results = []
                for item in spider_results(message['Url']):
                    results.append(item['img'])

                if results:
                    for img in results:
                        # images found build object and publish to mqtt topic
                        data = {}
                        data['img'] = img
                        data['path'] = message['Path']
                        jsondata = json.dumps(data)

                        print(f"Image Found, Publishing: {jsondata}")

                        # publish data 
                        client.publish("/imgscrape/save",jsondata,retain=retainflag,qos=2)
    except:
        print("Exception: Stopping")
        client.loop_stop()
        client.disconnect()
    



