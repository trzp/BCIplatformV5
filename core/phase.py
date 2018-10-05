#!/usr/bin/env python
#-*- coding:utf-8 -*-

#Copyright (C) 2018, Nudt, JingshengTang, All Rights Reserved
#Author: Jingsheng Tang
#Email: mrtang@nudt.edu.cn


import sys
import os
import platform
import time

self_name = 'Phase'

if platform.system()=='Linux':
    from linux_clock import clock as sysclock
else:
    from time import clock as sysclock

try:    __INF__ = float('inf')
except: __INF__ = 0xFFFF

def register_phase(arg):        
    PHASES = {}
    PHASES['start'] = {'next': '', 'duration': __INF__}
    PHASES['stop'] = {'next': '', 'duration': __INF__}
    for item in arg:
        if item.has_key('duration'):
            PHASES[item['name']]={'next':item['next'],'duration':item['duration']}
        else:
            PHASES[item['name']]={'next':'','duration':__INF__}
    return PHASES

def write_log(m):
    print '[%s][%3.4f]%s'%(self_name,sysclock(),m)

def phase_process(phase_list,Q_p2c,Q_c2p,E_g2p):
    #phase_list:
    #接受一个列表，每一个元素是一个字典，用来描述这个phase
    #e.g.
    # ph = [  {'name':'start','next':'prompt','duration':1},
             # {'name':'prompt','next':'on','duration':1},
         # ]
    #Q_p2c: multiprocessing.Queue  phase -> core
    #Q_c2p: multiprocessing.Queue  core -> phase
    #E_g2p: multiprocessing.Event  gui -> phase  user cease signal

    PHASES = register_phase(phase_list)
    time.sleep(5)
    current_phase = 'start' #phase必须从start开始
    Q_p2c.put(current_phase)
    _clk = sysclock()

    while True:
        clk = sysclock()

        if clk - _clk > PHASES[current_phase]['duration']:
            current_phase = PHASES[current_phase]['next']
            Q_p2c.put(current_phase)
            _clk = clk
        
        if not Q_c2p.empty():
            typ,p = Q_c2p.get()
            if typ == 'change' and PHASES.has_key(p):
                current_phase = p
                Q_p2c.put(current_phase)
            else:
                write_log(self_name,'[warning] change phase ?? <%s %s>'%(typ,p))

        if E_g2p.is_set():
            Q_p2c.put('stop')
            break

        if current_phase == 'stop': break
        time.sleep(0.005)
