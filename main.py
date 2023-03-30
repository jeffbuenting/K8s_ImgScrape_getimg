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
    process.crawl(ImgscrapeSpider, url=SearchUrl)
    process.start()
    return results

def on_connect(client, userdata, flasgs, rc):
    if rc==0:
        print("connected to MQTT OK. Returned code=",rc)
    else:
        print("Bad MQTT connection Returned code=",rc)

def on_message(client, userdata, message):
    print("message received " ,str(message.payload.decode("utf-8")))
    print("message topic=",message.topic)
    print("message qos=",message.qos)
    print("message retain flag=",message.retain)

    # return message
    q.put(message)

def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))
    client.suback_flag=True




SearchUrl = 'https://nextdoornikki.com/hosted/gal/watermellon/1581254'

if __name__ == '__main__':
    parser=argparse.ArgumentParser()

    parser.add_argument("--broker", help="MQ Broker",required=True)
    parser.add_argument("--readport", help="MQ Read Port",required=True)

    args=parser.parse_args()

    print("num args = ")
    print(args)

    broker=args.broker
    # and convert string to int as docker env vars must be string
    port=int(args.readport)

    # initialize message recv queue
    q = Queue()

    mqtt.Client.suback_flag=False
    client= mqtt.Client()

    client.on_connect = on_connect
    client.on_message=on_message
    client.on_subscribe=on_subscribe

    client.connect(broker,port)
    
    client.loop_start()
    client.subscribe("/imgscrape/input")

    sleep_count=0
    while not client.suback_flag: #wait for subscribe to be acknowledged
        time.sleep(.25)
        if sleep_count>40: #give up
            print("Subscribe failure quitting")
            client.loop_stop()
            sys.exit()
        sleep_count+=1

    print("looping...")
    I = 0
    while  I >= 10:
        print( I )

        time.sleep(5) 

    client.loop_stop()



    # results = []
    # for item in spider_results(SearchUrl):
    #     results.append(item['img'])

    # print(results)