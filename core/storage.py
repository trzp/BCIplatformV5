#!/usr/bin/env python
#-*- coding:utf-8 -*-

#Copyright (C) 2018, Nudt, JingshengTang, All Rights Reserved
#Author: Jingsheng Tang
#Email: mrtang@nudt.edu.cn


import os, time
import numpy as np
import scipy.io
import multiprocessing


class Storage(object):
    def __init__(self,configs):
        self.config = configs
        head = configs['SubjectName'] +'-s%02ir'%(configs['Session'])
        extension = '.mat'
        filenum = 0
        filename = head+'%03i'%(filenum)+extension
        newfilename = configs['Directory']+'//'+filename
        if not os.path.exists(configs['Directory']):
            os.makedirs(configs['Directory'])
        else:
            files = os.listdir(configs['Directory'])
            nums = [self.getnum(f,head,extension) for f in files if self.getnum(f,head,extension)>-1]
            if nums!=[]:    newfilename = configs['Directory']+'//'+head+'%03i'%(max(nums)+1)+extension
        self.data_file = newfilename

        self.buf = {}
        self.buf['Experiment']=configs['Experiment']
        self.buf['SubjectName']=configs['SubjectName']
        self.buf['Time']=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        self.buf['SamplingRate']=configs['SamplingRate']
        self.buf['Channellist']=configs['Channellist']

    def getnum(self,file,head,extension):
        hi = file.find(head)
        ei = file.find(extension)
        if hi==-1 or ei==-1:
            return -1
        else:
            try:
                num = int(file[hi+len(head):ei])
                return num
            except:
                return -1

    def savedata(self,eeg,trigger):#channels x points
        self.buf['EEG']=eeg
        self.buf['trigger']=trigger
        scipy.io.savemat(self.data_file,self.buf)
        time.sleep(0.001)

#独立进程用于每1秒保存一次数据
class Store():
    def __init__(self,configs,q):
        self.st = Storage(configs)#准备存储文件
        self.q = q

    def run(self):  #每收到10个数据保存一次
        count = 0
        eeg,trigger,flg = self.q.get()#[eeg(numpy array),trigger(dict)]
        while True:
            eg,tri,flg = self.q.get()
            if flg:
                break
            count += 1
            count %= 10
            eeg = np.hstack((eeg,eg))
            for k in tri:
                trigger[k]=np.hstack((trigger[k],tri[k]))
            if count == 1:
                self.st.savedata(eeg,trigger)
