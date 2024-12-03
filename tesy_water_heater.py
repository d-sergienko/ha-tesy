#!/usr/bin/env python3

import json, requests, re

class WaterHeater:
    modes = ["Dummy-do-not-use", "Manual", "P1", "P2", "P3", "Eco", "EC1", "EC2"]
    def __init__(self, ip=None):
        if (ip == None):
            return None
        self.ip=ip
    #    self.status = self.getStatus()
    #    self.device = self.getDeviceInfo()
    
    def request(self, cmd, body=None):
        url = 'http://'+self.ip+'/'+cmd
        resp = requests.get(url=url, params=body)
        data = json.loads(resp.text)
        return data

    def getStatus(self, param=None):
        self.status = self.request('status')
        if (param):
            return self.status[param]
        return self.status

    def getDeviceInfo(self, param=None):
        self.device = self.request('devstat')
        self.devid = self.device['devid']
        self.macaddr = self.device['macaddr']
        if (param):
            return self.device[param]
        return self.device

    def getDeviceID(self):
        return re.sub(' FW.*@', '', self.device['devid'])

    def getMode(self):
        if (self.status == None):
            mode = int(self.getStatus('mode'))
        else:
            mode = int(self.status['mode'])
        return self.modes[mode]

    def setMode(self, mode):
        if mode not in range(1, 8):
            return None
        return self.request('modeSW', {"mode":mode})

    def setTemp(self, temp):
        if temp not in range(8, 76):
            return None
        if (self.getMode() != "Manual"):
            self.setMode(self.modes.index("Manual"))
        return self.request('setTemp', {"val":temp})

    def boostOn(self):
        return self.request('boostSW', {"mode":1})

    def boostOff(self):
        return self.request('boostSW', {"mode":0})

    def powerOn(self):
        return self.request('power', {"val":"on"})

    def powerOff(self):
        return self.request('power', {"val":"off"})

