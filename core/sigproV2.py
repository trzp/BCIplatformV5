#!/usr/bin/env python
#-*- coding:utf-8 -*-

#Copyright (C) 2018, Nudt, JingshengTang, All Rights Reserved
#Author: Jingsheng Tang
#Email: mrtang@nudt.edu.cn


import os,sys
rootpath = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(rootpath + '\\amplifiers')

import numpy as np
from storage import Store
import multiprocessing
from multiprocessing import Queue,Event
import threading
import platform
from threading import Lock
from copy import copy
import time
import os,signal
from copy import deepcopy

from amp_simulator import AmpSimulator
from amp_actichamp import AmpActichamp

if platform.system()=='Linux':
    from linux_clock import clock as sysclock
else:
    from time import clock as sysclock

class SIGPRO(threading.Thread):
    configs = {   'Experiment': 'EEG experiment',
                  'SubjectName': 'subject',
                  'Session':    1,
                  'Directory':  rootpath + '//data',
                  'Amplifier':  'simulator',  #simulator,actichamp,mindwave,xintuo
                  'Ampconfigs': {},
                  'Channellist':[1,2,3,4,5],
                  'SamplingRate':200,
                  'SaveData':   False}
    Trigger = {}

    def __init__(self,Q_g2s,Q_s2c,E_c2s):
        # Q_g2s: multiprocessing.Queue  gui -> sigpro
        # Q_s2c: multiprocessing.Queue  sigpro -> core
        # E_c2s: multiprocessing.Event  user cease signal
        self.Q_g2s = Q_g2s
        self.Q_s2c = Q_s2c
        self.E_c2s = E_c2s
        self.storageQ = Queue()
        self.amp = None
        self.lstcount = 0
        self.check = 0  #标记是否进行过参数检查
        self._lock = Lock()
        threading.Thread.__init__(self)
        self.setDaemon(True)    #子线程用于接受trigger 并且子线程随主线程一起结束
        
        self.gtris = []
    
    def write_log(self,m):
        print '[Sigpro][%.4f]%s'%(sysclock(),m)

    def run(self):  #子线程 接受trigger
        while True:
            gtri = self.Q_g2s.get()   #将接受到的tri放入列表等待数据包到达后写入trigger
            self._lock.acquire()    #gtri: clock,trigger event
            self.gtris.append(gtri)
            self._lock.release()
        print 'sig sub thre ended'

    def init_trigger_ary(self,num): #num包的数量
        tr = {}
        for tri in self.Trigger:    tr[tri]=self.Trigger[tri]*np.ones(self.p_once*num)
        return tr

    def definep(self,sig_ck,tri_ck):
        er = 0
        if sig_ck > tri_ck: #一个被错过的trigger
            p = 0                                   #仍然把这个trigger放在这个包的最开始
        else:
            p = int(self.p_once*(tri_ck - sig_ck)/0.05) #点位
            if p>self.p_once:
                # self.write_log("[warning] package late! Don't worry, we can handle it")
                er = 1
        return er,p

    def StartRun(self):
        self.p_once = self.configs['SamplingRate']/20

        ampname = self.configs['Amplifier']
        if ampname == 'simulator':
            self.amp = AmpSimulator(self.configs)
        elif ampname == 'actichamp':
            if not self.configs.has_key('addr'):raise IOError,'actichamp config error! address is not given!'
            self.amp = AmpActichamp(self.configs)
        elif ampname == 'mindwave':
            self.amp = AmpMindwave(self.configs)
        elif ampname == 'xintuo':
            self.amp = AmpXintuo(self.configs)
        else:
            raise IOError,'unsupported amplifier'

        self.sysclk = sysclock()
        self.start()

        #在网络传输中，常发生的问题是数据包延迟
        #在同机计算机采集信号时，容易发生由于进程间同步带来的trigger late
        #因此本程序将延迟一个数据包发送，即总是留一个数据包在手里并不发送给用户，以便应对trigger late
        
        w_sclks = []
        w_signals = []
        
        while True:
            if self.E_c2s.is_set():
                break
            print 'running...'
            sclk,signal = self.amp.read()   #等待信号，sclk是已经经过同步的，信号中带的时间戳是一次信号采集完成时记录的
            w_sclks = w_sclks + sclk
            w_signals = w_signals + signal
            
            sclks = w_sclks[:-1]    #留一个数据不处理
            signals = w_signals[:-1]
            
            w_sclks = w_sclks[-1:]
            w_signals = w_signals[-1:]

            if len(sclks)>0:    #第一次的时候不处理
                # 如果存在网络拥堵，那么在某一帧中可能受到多个信号包，和多个trigger
                sclks = np.array(sclks)-0.05    #信号采集起始时刻
                trigger_array = self.init_trigger_ary(len(sclks))
                signal_array = np.hstack(signals)
                
                while len(self.gtris)>0:    #遍历triggers
                    gclk,trigger = item = self.gtris.pop(0)
                    ind = np.where(sclks<=gclk)[0]
                    if ind.size == 0:
                        self.write_log('[warning] late trigger')
                        indx = 0     #说明trigger延迟了
                    else:                indx = ind[-1]
                    er,p = self.definep(sclks[indx],gclk)
                    if not er:  #正常写入
                        for key in trigger:
                            trigger_array[key][self.p_once*indx+p:] = trigger[key]
                            self.Trigger[key] = trigger[key]
                    else:   #异常，trigger超出了信号包时间域范围,应当打入下一个信号包
                        self.gtris.insert(0,item)           #将其放回去
                        # self.write_log("[warning] package late! Don't worry, we can handle it")
                        break

                if self.configs['SaveData']:self.storageQ.put([signal_array,trigger_array,0])
                self.Q_s2c.put((signal_array,trigger_array))
 
        self.storageQ.put([0,0,1])
        print 'sigproend=================='

def sig_process(config,Trigger,Q_g2s,Q_s2c,E_c2s):
    sp = SIGPRO(Q_g2s,Q_s2c,E_c2s)
    sp.configs = config #配置更新
    sp.Trigger = Trigger
    if config['SaveData']:  #建议先于父进程启动
        st = Store(config,sp.storageQ)
        pp = multiprocessing.Process(target=st.run)
        pp.start()
    sp.StartRun()
