#!/usr/bin/env python
#-*- coding:utf-8 -*-

#Copyright (C) 2018, Nudt, JingshengTang, All Rights Reserved
#Author: Jingsheng Tang
#Email: mrtang@nudt.edu.cn


import numpy as np
import socket
import multiprocessing
from multiprocessing import Queue, Event
import platform
import mmap
import time
import uuid
from winclock import global_clock as sysclock
from struct import pack,unpack
import time

class AmpActichamp(object):
    def __init__(self,configs):
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.connect(configs['addr'])
        mac = uuid.uuid1().hex[-12:]
        self.mac = '-'.join(mac[i:i+2].upper() for i in range(0,12,2))  #本机mac地址,长度为17字节
        self.configs = configs
        self.p_once = self.configs['SamplingRate']/20
        self.chlst = np.array(self.configs['Channellist'])
        self.ch = int(len(self.configs['Channellist']))
        self.bytenum = self.p_once*self.ch*8

        print 'synchronizing test...'
        ss = []
        for i in xrange(50):
            clkA0 = sysclock()
            self.sock.send('test'+pack('d',clkA0)+self.mac)
            buffer = self.sock.recv(32)
            clkA1 = sysclock()
            t = (clkA1 - clkA0)/2. # 单程消耗时间
            macB = buffer[-17:]
            if macB == self.mac:    #同一台计算机，无需同步
                self.SYNC_CLOCK = 0
                break
            else:
                clkB = unpack('d',buffer[4:12])[0]
                ss.append(clkA0 + t - clkB)
        self.sock.send('endt00000000')
        if len(ss)>0:
            ss.sort()
            self.SYNC_CLOCK = ss[0]
        print 'synchronizing completed! SYNC_CLOCK: %f'%(self.SYNC_CLOCK,)
        self.check = True

    def read(self):
        buf = self.sock.recv(25600) #可能会收到多个包
        clks = []
        eegs = []
        while len(buf)>0:
            data = np.fromstring(buf[:24],dtype=np.float64)

            if self.check:
                if int(data[0])!=self.configs['SamplingRate']:
                    print 'samplingrate does not match!'
                if int(self.ch)>data[1]:
                    print 'request too much channels of signal!'
                if np.max(self.chlst)>=data[1]:
                    print 'channel indices exceeded the source signal!'
                self.check = False

            clks.append(data[2]+self.SYNC_CLOCK) #校准后的clk
            eegs.append(np.fromstring(buf[24:24+self.bytenum],dtype=np.float64).reshape(self.ch,self.p_once)[self.chlst,:])
            buf = buf[24+self.bytenum:]

        return clks,eegs

if __name__ == '__main__':
    configs = {'addr':('192.168.1.1',9000),'SamplingRate':200,'Channellist':range(9)}
    amp = AmpActichamp(configs)
    c = time.clock()
    for i in range(50):
        clks,eegs = amp.read()
