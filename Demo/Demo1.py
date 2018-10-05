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


class BCImain(core):
    def __init__(self):
        super(BCImain,self).__init__()
    
    def Initialize(self):
        self.PHASES = [  {'name':'start','next':'prompt','duration':1},
                         {'name':'prompt','next':'on','duration':2},
                         {'name':'on','next':'off','duration':0.15},
                         {'name':'off','next':'on','duration':0.1},
                         {'name':'result','next':'prompt','duration':2},
                         {'name':'stop'}
                      ]

        self.configs = {  'Experiment': 'EEG experiment',
                          'SubjectName': 'subject',
                          'Session':    1,
                          'Directory':  rootpath + '//data',
                          'Amplifier':  'actichamp',#'simulator',
                          'Channellist': range(6),
                          'SamplingRate':200,
                          'SaveData':   1,
                          'addr':('127.0.0.1',9000)}

        self.Trigger = {'state':-1,'code':-1}

        scrw = 800
        scrh = 200

        self.stimuli['screen'] = {'size':(scrw,scrh),'color':(0,0,0),'type':'normal'}
        self.stimuli['cue'] = {'class':'Block','parm':{'size':(100,40),'position':(scrw/2,30),
                                          'anchor':'center','visible':True,'forecolor':(0,0,0),'text':'',
                                          'textsize':25,'textcolor':(0,0,255),'textanchor':'center'}}

        xs = np.linspace(0,scrw,8)[1:-1]
        bw = 0.75*(xs[1]-xs[0])
        for i in xrange(6):
            self.stimuli['Flsh%d'%(i)] = {'class':'Block','parm':{'size':(bw,bw),'position':(xs[i],scrh/2),
                                          'anchor':'center','visible':True,'forecolor':(80,80,80),'text':'%d'%(i),
                                          'textsize':25,'bold':True,'textcolor':(0,0,255)}}
        self.code = -1
        self.tasklist = range(6)
        random.shuffle(self.tasklist)
    
    def Transition(self,phase):
        # self.write_log('[info] get phase: %s'%(phase))
        if phase == 'prompt':
            if len(self.tasklist)==0:
                self.change_phase('stop')
                return

            task = self.tasklist.pop()

            self.GuiUpdate({'cue':{'visible':True,'text':'task %s'%(task,)}},{'state':0,'code':-1})
            self.ary = range(6)
            random.shuffle(self.ary)

        elif phase == 'on':
            if len(self.ary)==0:
                self.change_phase('result')
                return

            self.code = self.ary.pop()
            self.GuiUpdate({'Flsh%i'%(self.code,):{'forecolor':(255,255,255)}},{'code':self.code})

        elif phase == 'off':
            self.GuiUpdate({'Flsh%i'%(self.code,):{'forecolor':(80,80,80)}},{'code':-1})

        elif phase == 'result':
            self.GuiUpdate({'cue':{'text':'result --'}},{'state':1,'code':-1})
    
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

