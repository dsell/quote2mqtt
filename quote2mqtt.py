#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim tabstop=4 expandtab shiftwidth=4 softtabstop=4

# 


__author__ = "Dennis Sell"
__copyright__ = "Copyright (C) Dennis Sell"


APPNAME = "quote2mqtt"
VERSION = "0.11"
WATCHTOPIC = "/raw/" + APPNAME + "/command"

import subprocess
import logging
import random
from daemon import Daemon
from mqttcore import MQTTClientCore
from mqttcore import main
import threading
import time
import csv


class MyMQTTClientCore(MQTTClientCore):
    def __init__(self, appname, clienttype):
        MQTTClientCore.__init__(self, appname, clienttype)
        self.clientversion = VERSION
        self.watchtopic = WATCHTOPIC
        self.workingdir = self.cfg.WORKINGDIR
        self.clienttopic = "/clients/" + APPNAME
        self.quotes = []
        self.do_read_quotes()

    def on_connect(self, mself, obj, rc):
        MQTTClientCore.on_connect(self, mself, obj, rc)
        self.mqttc.subscribe(self.watchtopic, qos=0)
        self.mqttc.subscribe('/raw/clock/day', qos=0)

    def do_read_quotes(self):
        cr = csv.reader(open(self.workingdir + "quotes.csv","rb"))
        for row in cr:
            new_quote = Quote(row[0], row[1], row[2])
            self.quotes.append(new_quote)

    def do_list_quotes(self):
        for x in self.quotes:
            print x.quote + " " + x.author + " " + x.reference + " " + x.category

    def do_quote(self):
        x = random.choice(self.quotes)
        self.mqttc.publish(self.clienttopic + "/quote", x.quote, qos=2, retain=True)
        self.mqttc.publish(self.clienttopic + "/author", x.author, qos=2, retain=True)
        self.mqttc.publish(self.clienttopic + "/reference", x.reference, qos=2, retain=True)
        self.mqttc.publish(self.clienttopic + "/full", x.quote + " - " + x.author + " -- " + x.reference, qos=2, retain=True)

    def on_message(self, mself, obj, msg):
        MQTTClientCore.on_message(self, mself, obj, msg)
        if (msg.topic == '/raw/clock/day'):
            self.do_quote()
        if (msg.topic == self.watchtopic):
            if(msg.payload == "update"):
                self.do_read_quotes()
        if (msg.topic == self.watchtopic):
            if(msg.payload == "list"):
                self.do_list_quotes()
        if (msg.topic == self.watchtopic):
            if(msg.payload == "quote"):
                self.do_quote()

class Quote:
    def __init__(self, quote, author, reference, category=""):
        self.quote = quote
        self.author = author
        self.reference = reference
        self.category = category


class MyDaemon(Daemon):
    def run(self):
        mqttcore = MyMQTTClientCore(APPNAME, clienttype="type1")
        mqttcore.main_loop()


if __name__ == "__main__":
    daemon = MyDaemon('/tmp/' + APPNAME + '.pid')
    main(daemon)

