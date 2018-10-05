#!/usr/bin/env python
#-*- coding:utf-8 -*-

#Copyright (C) 2018, Nudt, JingshengTang, All Rights Reserved
#Author: Jingsheng Tang
#Email: mrtang@nudt.edu.cn

import numpy as np
from multiprocessing import Queue,Event
import multiprocessing
from gui import gui_process
import time

if __name__ == '__main__':
    scrw = 600
    scrh = 500
    sti = {'screen':{'size':(600,500),'color':(0,0,0)},
           'cue':{'class':'Block','parm':{'size':(100,40),'position':(600/2,30),
                                          'anchor':'center','visible':True,'forecolor':(0,0,0),'text':'tangjign',
                                          'textsize':25,'textcolor':(0,0,255),'textanchor':'center'}}
           }
    xs = np.linspace(0,600,8)[1:-1]
    bw = 0.75*(xs[1]-xs[0])
    for i in xrange(6):
        sti['Flsh%d'%(i)] = {'class':'Block','parm':{'size':(bw,bw),'position':(xs[i],scrh/2),
                                      'anchor':'center','visible':True,'forecolor':(80,80,80),'text':'%d'%(i),
                                      'textsize':25,'bold':True,'textcolor':(0,0,255),'borderon':True,'bordercolor':(255,0,0,255)}}

    q = Queue()
    pp = multiprocessing.Process(target = gui_process,args=(sti,q,Event()))
    pp.start()
    while True:
        for i in xrange(6):
            q.put({'Flsh%i'%(i,):{'forecolor':(255,0,0)}})
            time.sleep(0.1)
            q.put({'Flsh%i'%(i,):{'forecolor':(80,80,80)}})
            time.sleep(0.1)

