import sys
import os
import Sniper
import argparse
import numpy as np

prs = argparse.ArgumentParser()
prs.add_argument('-input-list', '--input', help='Input list of esd files')
prs.add_argument('-output', '--output', help='output file')
prs.add_argument('-corr-list', '--corr', help='Input list of rtraw files', default=None)

args = prs.parse_args()
cwd=os.getcwd()

outfilename = args.output
listname = args.input
corrlist = args.corr

Sniper.loadDll("/junofs/users/gferrante/BiPo/Run_analyzer/Run_reader_cxx.so")
#Sniper.loadDll("libSimEvent.so")

task = Sniper.Task("task")
task.setLogLevel(1)

alg = task.createAlg("Run_reader")

import BufferMemMgr
bufMgr = task.createSvc("BufferMemMgr")

import RootWriter
task.property("svcs").append("RootWriter")
rw = task.find("RootWriter")
rw.property("Output").set({"tree":outfilename})

import RootIOSvc
import RootIOTools
riSvc = task.createSvc("RootInputSvc/InputSvc")
inputFileNumpy = np.loadtxt(listname,usecols=(0),unpack=True,dtype=str)
inputFileList = inputFileNumpy.tolist()
riSvc.property("InputFile").set(inputFileList)

if (corrlist != None):
    corrFileNumpy = np.loadtxt(corrlist,usecols=(0),unpack=True,dtype=str)
    corrFileList = corrFileNumpy.tolist()
    riSvc.property("InputCorrelationFile").set(corrFileList)

task.setEvtMax(-1)
task.show()
task.run()
