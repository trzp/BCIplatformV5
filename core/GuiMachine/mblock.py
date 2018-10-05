#!/usr/bin/env python
#-*- coding:utf-8 -*-

#Copyright (C) 2018, Nudt, JingshengTang, All Rights Reserved
#Author: Jingsheng Tang
#Email: mrtang@nudt.edu.cn

import pygame
from pygame_anchors import *
import os
from copy import deepcopy


class mBlock(object):
    '''
    used for generate m-sequence stimulus. i.e. vary at each frame accodring to the sequence.
    all the stimulus type with behavior control at each frame should regesit with a key of "perframe"
    '''
    size = (5,5)
    position = (0,0)
    anchor = 'center'
    forecolor = (255,255,255,255)

    borderon = False
    borderwidth = 1
    bordercolor = (0,0,0,0)

    textcolor = (0,255,255,0)
    textfont = 'arial'
    textanchor = 'center'
    textsize = 10
    textbold = False
    text = ''
    
    perframe = True #should be check at each frame
    
    _sequence = []
    repetition = 1

    layer = 0
    visible = False #设两个开光 此开关用户可见
    on = False
    __draw = True   #用于控制m码
            
    parmkeys = ['size','position','anchor','borderon','borderwidth','bordercolor',
                'forecolor','textcolor','textfont','textanchor','textsize','textbold',
                'text','layer','visible','m_sequence','repetition','on']
    sur = None

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
                if len(self._sequence)==0:
                    self.__draw = False
                else:
                    m = self._sequence.pop(0)
                    if self.repetition == 0:    #无限循环
                        self._sequence.append(m)
                    if m:   self.__draw = True
                    else:   self.__draw = False
            else:
                self.__draw = False
            self.update()

    def update(self):
        if self.__draw:
            self.sur = pygame.Surface(self.size)
            self.sur.fill(self.forecolor)
        else:
            self.sur = None

    def reset(self,**argw):
        self.update_parm(**argw)
        self.blitp = self.blitpborder = blit_pos1(self.size,self.position,self.anchor)
        if argw.has_key('on'):   #启动
            if argw['on'] == True:
                self._sequence = deepcopy(self.m_sequence)
                if self.repetition > 0:
                    self._sequence *= self.repetition

    def show(self):
        if self.visible:
            if self.sur!=None:  self.root.blit(self.sur,self.blitp)
            if self.borderon:   pygame.draw.rect(self.root,self.bordercolor,pygame.Rect(self.blitpborder,self.size),self.borderwidth)
            if self.text != '':
                txt = self.font_object.render(self.text,1,self.textcolor)
                p0 = getcorner(self.size,self.textanchor)
                p = blit_pos(txt,p0,self.textanchor)
                pp = [x[0]+x[1] for x in zip(self.blitp,p)]
                self.root.blit(txt,pp)

