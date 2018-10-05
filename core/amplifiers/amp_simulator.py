#!/usr/bin/env python
#-*- coding:utf-8 -*-

#Copyright (C) 2018, Nudt, JingshengTang, All Rights Reserved
#Author: Jingsheng Tang
#Email: mrtang@nudt.edu.cn


import numpy as np
from winclock import global_clock as sysclock
import time

class AmpSimulator(object):
    def __init__(self,configs):
        self.configs = configs
        self.p_once = self.configs['SamplingRate']/20
        self.ch = len(self.configs['Channellist'])
        self.SYNC_CLOCK = 0

    def read(self):
        time.sleep(0.05)
        return [sysclock()],[100*np.random.rand(self.ch,self.p_once).astype(np.float64)]
