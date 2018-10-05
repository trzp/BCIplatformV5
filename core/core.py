#!/usr/bin/env python
#-*- coding:utf-8 -*-

#Copyright (C) 2018, Nudt, JingshengTang, All Rights Reserved
#Author: Jingsheng Tang
#Email: mrtang@nudt.edu.cn


import os,sys
file_dir = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(file_dir+'//GuiMachine')

import numpy as np

import multiprocessing
from multiprocessing import Queue
from multiprocessing import Event
from phase import *
from gui import gui_process
from sigproV2 import sig_process
import random
import threading
from copy import deepcopy

try:    __INF__ = float('inf')
except: __INF__ = 0xFFFF

import platform

if platform.system()=='Linux':
    from linux_clock import clock as sysclock
else:
    from time import clock as sysclock


class core(threading.Thread):
    Q_p2c = Queue()   #phase -> core
    Q_c2p = Queue()   #core -> phase
    Q_c2g = Queue()   #core -> gui
    Q_s2c = Queue()   #sigpro -> core
    Q_g2s = Queue()   #gui -> sigpro
    E_c2s = Event()   #end -> sigpro
    E_g2p = Event()

    PHASES = []     #两个专有的成员
    stimuli = {}
    configs = {}
    Trigger = {}
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)
    
    #在子类中覆盖实现的
    def Initialize(self):#在子类中实现
        pass

    def Process(self,flg,(eeg,tri)):#在子类中实现
        pass

    def Transition(self,phase): #在子类中实现
        pass

    def change_phase(self,phase):
        self.Q_c2p.put(['change',phase])
    
    def write_log(self,m):
        print '[Core][%.4f]%s'%(sysclock(),m)

    def GuiUpdate(self,sti,trigger):
        self.Q_c2g.put([sti,trigger])
        
    #不可更改的方法
    def mainloop(self): #主线程接受phase驱动整个程
        self.write_log('[info] program started!')
        while True:
            ph = self.Q_p2c.get()
            self.Transition(ph)
            #结束信号：来自phase的结束，和gui用户的结束
            #gui用户结束信号由E_g2p发送给phase强制跳转到stop，stop全局信号统一由phase发出
            if ph == 'stop':
                self.Q_c2g.put('_q_u_i_t_') #结束gui
                self.E_c2s.set()            #结束sigpro
                break
        self.write_log('[info] process killed!')
        time.sleep(1)

    def run(self):  #子线程接受信号做处理
        sigf = False
        sig = None
        trig = None
        clk = sysclock()
        tt = {}
        for key in self.Trigger:   tt[key] = []
        
        while True: #确保大约0.1ms的执行interval,因此，可能存在没有数据返回
            if sysclock() - clk > 0:
                clk += 0.1
                if not self.Q_s2c.empty():
                    tts = deepcopy(tt)
                    ss = []
                    while not self.Q_s2c.empty():
                        s,t = self.Q_s2c.get()
                        ss.append(s)
                        for key in tts:
                            tts[key].append(t[key])

                    sig = np.hstack(ss)
                    for key in tts:
                        tts[key] = np.hstack(tts[key])
                    self.Process(1,(sig,tts))
                else:
                    self.Process(0,(0,0))
            time.sleep(0.01)
            
            # s,t = self.Q_s2c.get()
            # self.Process(1,(s,t))
        print 'main subthre'

    def StartRun(self): #mainloop
        self.Initialize()
        p1 = multiprocessing.Process(target=gui_process,args=(self.stimuli,self.Q_c2g,self.E_g2p,self.Q_g2s))
        p2 = multiprocessing.Process(target=phase_process,args=(self.PHASES,self.Q_p2c,self.Q_c2p,self.E_g2p))
        p3 = multiprocessing.Process(target=sig_process,args=(self.configs,self.Trigger,self.Q_g2s,self.Q_s2c,self.E_c2s))
        p3.start()
        p2.start()
        p1.start()
        self.start()
        self.mainloop()
