#!/usr/bin/env python
#-*- coding:utf-8 -*-

#Copyright (C) 2018, Nudt, JingshengTang, All Rights Reserved
#Author: Jingsheng Tang
#Email: mrtang@nudt.edu.cn

import os,sys
rootpath = os.path.split(os.path.realpath(__file__))[0]
rootpath1 = os.path.split(rootpath)[0]
sys.path.append(rootpath1+'//core')

from core import core

import numpy as np
import random
import multiprocessing

import win32api


class BCImain(core):
    def __init__(self):
        super(BCImain,self).__init__()
    
    def Initialize(self):
        self.PHASES = [  {'name':'start','next':'prompt','duration':2},
                         {'name':'prompt','next':'on','duration':1},
                         {'name':'on','next':'result','duration':8},
                         {'name':'result','next':'prompt','duration':2},
                         {'name':'stop'}
                      ]

        self.configs = {  'Experiment': 'Sin wave ssvep experiment',
                          'SubjectName': 'LKJ-sinssvep',
                          'Session':    1,
                          'Directory':  rootpath + '//data//lkj',
                          'Amplifier':  'actichamp',#'simulator',
                          'Channellist': range(4),
                          'SamplingRate':1000,
                          'SaveData':   1,
                          'addr':('127.0.0.1',9000)}
        
        self.ssvep_f = 8

        self.Trigger = {'trial':0,'frequency':self.ssvep_f}

        scrw = win32api.GetSystemMetrics(0)
        scrh = win32api.GetSystemMetrics(1)

        self.stimuli['screen'] = {'size':(scrw,scrh),'color':(0,0,0),'type':'fullscreen'}
        self.stimuli['cue1'] = {'class':'sinBlock','parm':{'size':(150,150),'position':(scrw/2,scrh/2),
                                          'anchor':'center','visible':True,'on':False,'forecolor0':(0,0,0),
                                          'forecolor1':(255,255,255),'frequency':self.ssvep_f,'duration':9999,
                                          }}
        
        self.trial = 0
    
    def Transition(self,phase):
        if phase == 'start':
            self.GuiUpdate({'cue1':{'visible':True}},{'trial':0,'frequency':self.ssvep_f})

        elif phase == 'on':
            self.trial += 1
            self.GuiUpdate({'cue1':{'on':True}},{'trial':self.trial})

        elif phase == 'result':
            self.GuiUpdate({'cue1':{'on':False}},{'trial':0})
            if self.trial == 10:
                self.change_phase('stop')
    
    def Process(self,flg,(signal,tri)):  #res来自信号处理模块的结果
        # print flg
        # if flg:
            # print signal.shape
        pass
        
def main():
    bm = BCImain()
    bm.StartRun()

if __name__ == '__main__':
    main()

