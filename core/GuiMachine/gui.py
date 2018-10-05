#!/usr/bin/env python
#-*- coding:utf-8 -*-

#Copyright (C) 2018, Nudt, JingshengTang, All Rights Reserved
#Author: Jingsheng Tang
#Email: mrtang@nudt.edu.cn

# This gui program employs the vertical synchronization mode on the basis of using the directx
# graphic driver. It makes the program update the drawing synchornously with the monitor, thus
# to accurately contorl the stimulus graphics. It is similar to the sychtoolbox of Matlab. On
# this basis, the stimulus trigger event is also set synchronously with the actual drawing.

# Since the vertical synchronization mode is used, the graphic user interface is fullscreen.

import pygame
from pygame.locals import *
from block import Block
from sinblock import sinBlock
from mblock import mBlock
from imagebox import Imagebox
from multiprocessing import Queue,Event
import multiprocessing
import threading
import time,math
import os,platform
import numpy as np

if platform.system() == 'Windows':
    try:
        os.putenv('SDL_VIDEODRIVER','directx')
        os.environ['SDL_VIDEODRIVER'] = 'directx'
    except: raise KeyError,'add an environment variable "SDL_VIDEODRIVER" with value of "directx" into the computer'
    from winclock import global_clock as sysclock
elif platform.system() == 'Linux':
    from linux_clock import linux_clock as sysclock
else:
    raise IOError,'unrecognized system platform'
    
OS = platform.system()

class GUImachine(threading.Thread):
    stimuli = {}
    __release_ID_list = []

    def __init__(self,stims,Q_c2g,E_g2p,Q_g2s):
        """
        stims:  dict to define a stimulus.
                eg. stims = {'cue':{'class':'Block','parm':{'size':(100,40),'position':(0,0)}}}
        Q_c2g: multiprocessing.Queue, used for accepting stimulus control command from core process
        E_g2p: multiprocessing.Event, used for sending user termination event to the phase process
        Q_g2s: multiprocessing.Queue, used for sending accurate trigger to sigpro process
        """
        super(GUImachine,self).__init__()
        pygame.init()
        self.Q_c2g = Q_c2g
        self.E_g2p = E_g2p
        self.Q_g2s = Q_g2s
        self.trigger_on = False
        self.trigger_event = {}
        self.stp = False
        self.lock = threading.Lock()
        if stims['screen']['type'].lower() == 'fullscreen':
            self.screen = pygame.display.set_mode((0,0),FULLSCREEN | DOUBLEBUF | HWSURFACE,32)
            self.vsync = True
        else:
            if stims['screen'].has_key('frameless'):
                if stims['screen'].has_key('frameless'):
                    self.screen = pygame.display.set_mode(stims['screen']['size'],pygame.NOFRAME)
                else:
                    self.screen = pygame.display.set_mode(stims['screen']['size'])
            else:
                self.screen = pygame.display.set_mode(stims['screen']['size'])
            self.vsync = False
        if OS != 'Windows': self.vsync = False
        self.screen_color = stims['screen']['color']
        self.screen.fill(self.screen_color)
        pygame.display.set_caption('BCI GUI')
        del stims['screen']
        self.setDaemon(True)
        self.ask_4_update_gui = False       #线程接收到刷新请求后，进行绘图准备，并通知主进程刷新
        self.update_in_this_frame = False   #主进程在一帧真实的刷新帧中确定能够进行刷新
        
        self.__update_per_frame_list = []
        #register stimulis
        for ID in stims:
            element = stims[ID]
            if element['class'] == 'Block': self.stimuli[ID] = Block(self.screen,**element['parm'])
            elif element['class'] == 'Imagebox':self.stimuli[ID] = Imagebox(self.screen,**element['parm'])
            elif element['class'] == 'sinBlock':
                self.stimuli[ID] = sinBlock(self.screen,**element['parm'])
                self.__update_per_frame_list.append(self.stimuli[ID])
            elif element['class'] == 'mBlock':
                self.stimuli[ID] = mBlock(self.screen,**element['parm'])
                self.__update_per_frame_list.append(self.stimuli[ID])
            else:   pass

    def run(self):  #subthread to accept the stimulus change
        # arg = self.Q_c2g.get()
        # arg:
        #     1. '_q_u_i_t_': program terminate
        #     2. [stimulus setting, trigger]
        while True:
            arg = self.Q_c2g.get()
            if arg == '_q_u_i_t_':
                self.stp = True
                break
            
            stimulus_arg,self.trigger_event = arg  #trigger is a dict
            
            self.lock.acquire()
            [self.stimuli[id].reset(**stimulus_arg[id]) for id in stimulus_arg.keys()]
            self.ask_4_update_gui = True  #请求刷新
            self.lock.release()

    def StartRun(self):
        clock = pygame.time.Clock()
        END = 0
        while True:
            self.screen.fill(self.screen_color)
            [sti.update_per_frame() for sti in self.__update_per_frame_list]
            #self.lock.acquire()
            if self.ask_4_update_gui:
                self.update_in_this_frame = True #将在这一帧刷新
                self.ask_4_update_gui = False
            stis = sorted(self.stimuli.items(),key=lambda k:k[1].layer)
            for s in stis:  s[1].show()
            #self.lock.acquire()
            pygame.display.flip() #该帧刷新完毕
            
            if not self.vsync:  clock.tick(60)

            if self.update_in_this_frame:   #更新trigger，记录下此时的clock,因此，trigger的记录是伴随着真实的显示器刷新的
                self.Q_g2s.put([sysclock(),self.trigger_event])
                self.update_in_this_frame = False

            evs = pygame.event.get()
            for e in evs:
                if e.type == QUIT:
                    END=1
                elif e.type == KEYDOWN:
                    if e.key == K_ESCAPE: END=1
            if END:break
            if self.stp:    break

        pygame.quit()
        if END: self.E_g2p.set()  #通知phase进程，用户结束
        for ID in self.__release_ID_list:   del self.stimuli[ID]

def gui_process(sti,Q_c2g,E_g2p,Q_g2s):
    g = GUImachine(sti,Q_c2g,E_g2p,Q_g2s)
    g.start()
    g.StartRun()
    
def init_screen_pos(x,y,scrw,scrh):
    xx = x - scrw/2
    yy = y - scrh/2
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (xx,yy)

def switch():
    stimuli = {}
    stimuli['screen'] = {'color':(0,0,0),'type':'normal','size':(600,100),'frameless':True}
    stimuli['cue'] = {'class':'sinBlock','parm':{'size':(600,100),'position':(300,50),
                      'anchor':'center','visible':True,'forecolor0':(0,0,0),'forecolor1':(255,255,255),
                      'on':True,'frequency':1,'init_phase':0,'duration':10,'text':'Next  Frame','textsize':50}}
    Q_c2g = Queue()
    E_g2p = Event()
    Q_g2s = Queue()
    init_screen_pos(700,600,800,150)
    gui_process(stimuli,Q_c2g,E_g2p,Q_g2s)


def test1():
    seq1 = [1,1,0,0,1,1,0,1,0,0,1,0,0,0,0,1,0,1,0,1,1,1,0,1,1,0,0,0,1,1,1]
    seq2 = [1,1,1,1,0,0,1,1,0,1,0,0,1,0,0,0,0,1,0,1,0,1,1,1,0,1,1,0,0,0,1]
    seq3 = [1,1,0,0,1,0,1,0,0,1,1]
    
    scrw = 1000
    scrh = 800
    stimuli = {}
    stimuli['screen'] = {'color':(0,0,0),'type':'normal','size':(800,800)}
    stimuli['cue'] = {'class':'sinBlock','parm':{'size':(300,300),'position':(100,100),
                      'anchor':'center','visible':True,'forecolor0':(0,0,0),'forecolor1':(255,255,255),
                      'on':False,'frequency':11,'init_phase':0,'duration':10,'text':'K'}}
    stimuli['cue1'] = {'class':'sinBlock','parm':{'size':(300,300),'position':(500,100),
                  'anchor':'center','visible':True,'forecolor0':(0,0,0),'forecolor1':(255,255,255),
                  'on':False,'frequency':10,'init_phase':0,'duration':10}}
    
    stimuli['cue2'] = {'class':'mBlock','parm':{'size':(300,300),'position':(500,400),
                  'anchor':'center','visible':True,'forecolor':(255,255,255),'m_sequence':seq3,'repetition':1,
                  'on':False,'borderon':True,'bordercolor':(255,255,255),'text':'tang','textanchor':'center'}}
    
    Q_c2g = Queue()
    E_g2p = Event()
    Q_g2s = Queue()
    
    # gui_process(stimuli,Q_c2g,E_g2p,Q_g2s)
    
    p = multiprocessing.Process(target = gui_process,args = (stimuli,Q_c2g,E_g2p,Q_g2s))
    p.start()
    a = 1
    while True:
        s = raw_input('')
        a *= -1
        if a<0:
            Q_c2g.put([{'cue':{'on':False},'cue1':{'on':False},'cue2':{'on':True}},{'trigger':1}])
        else:
            Q_c2g.put([{'cue':{'on':False},'cue1':{'on':False},'cue2':{'on':False}},{'trigger':1}])
            
            
if __name__ == '__main__':
    switch()