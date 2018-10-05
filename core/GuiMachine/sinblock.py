#!/usr/bin/env python
#-*- coding:utf-8 -*-

#Copyright (C) 2018, Nudt, JingshengTang, All Rights Reserved
#Author: Jingsheng Tang
#Email: mrtang@nudt.edu.cn

import pygame
from pygame_anchors import *
import os
import time
import math


class sinBlock(object):
    '''
    used for generate sin type stimulus. i.e. the gray vary at each frame accodring to the sequence.
    '''
    size = (5,5)
    position = (0,0)
    anchor = 'center'
    forecolor0 = (0,0,0)
    forecolor1 = (255,255,255)

    bordercolor = (0,0,0,0)

    textcolor = (0,255,255,0)
    textfont = 'arial'
    textanchor = 'center'
    textsize = 10
    textbold = False
    text = ''
    
    frequency = 10
    init_phase = 0
    duration = 5
    start = False
    __fcolor = None

    layer = 0
    visible = False
    on = False

    
    coef = np.array([0,0,0])
            
    parmkeys = ['size','position','anchor','on',
                'forecolor0','forecolor1','textcolor','textfont','textanchor','textsize','textbold',
                'text','layer','visible','frequency','init_phase','duration','start']
    sur = None
    
    clk = time.clock()

    def __init__(self,root,**argw):
        pygame.font.init()
        self.root = root

        self.reset(**argw)
        if not os.path.isfile(self.textfont): self.textfont = pygame.font.match_font(self.textfont)
        self.font_object = pygame.font.Font(self.textfont,self.textsize)
        self.font_object.set_bold(self.textbold)


    def update_parm(self,**argw):
        for item in argw:   exec('self.%s = argw[item]'%(item))
        
    def update_per_frame(self):
        if self.visible:
            if self.on:
                tt = time.clock()
                if tt - self.clk > self.duration:
                    self.on = False
                    return
                t = tt-self.clk
                f = (math.sin(2*math.pi*self.frequency*t + self.init_phase - 0.5*math.pi)+1)*0.5   #0-1
                self.__fcolor = self.coef * f + self.forecolor0
            else:
                self.__fcolor = self.forecolor0
            self.update()

    def reset(self,**argw): #接受主控的控制
        self.update_parm(**argw)
        self.blitp = self.blitpborder = blit_pos1(self.size,self.position,self.anchor)
        self.coef = np.array(self.forecolor1)-np.array(self.forecolor0)
        self.__fcolor = self.forecolor0
        self.bordercolor = (self.forecolor0+0.5*self.coef).astype(np.int32)
        if argw.has_key('on'):   #启动
            if argw['on'] == True:
                self.clk = time.clock()

    def update(self):
        self.sur = pygame.Surface(self.size)
        self.sur.fill(self.__fcolor)

        if self.text != '':
            txt = self.font_object.render(self.text,1,self.textcolor)
            p0 = getcorner(self.sur.get_size(),self.textanchor)
            p = blit_pos(txt,p0,self.textanchor)
            self.sur.blit(txt,p)

    def show(self):
        if self.visible:
            if self.sur!=None:  self.root.blit(self.sur,self.blitp)
            pygame.draw.rect(self.root,self.bordercolor,pygame.Rect(self.blitpborder,self.size),1)

