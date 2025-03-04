#It takes from input the RUN number

import os
import sys
import argparse
from argparse import RawTextHelpFormatter
from datetime import datetime

def ReadCfg(cfgFile) :
    Runs = []
    Levels = []
    with open(cfgFile,"r") as file:
        next(file)
        for line in file :
            elements = line.split()
            Runs.append(elements[0])
            Levels.append([elements[1],elements[2]])
    return Runs,Levels
    

prs = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)

group = prs.add_mutually_exclusive_group()

group.add_argument("-run",nargs="+", help="Name of the run")
group.add_argument("-cfgFile",help="Path of the configuration file")
prs.add_argument("-gain",type=float, help="Gain to be applied",default=None)
prs.add_argument("-volume",type=float, help="Volume of the LS",default=100)

args = prs.parse_args()

if not (args.run or args.cfgFile) :
    prs.error("One of -cfgFile or -run must be provided")

cwd=os.getcwd()

now = datetime.now()
now_str = now.strftime("%Y%m%d_%H%M%S")
autolauncher = open(cwd+"/launch/Launch"+now_str+".sh","w")

if (args.gain) :
    gain_str = " -gain " + str(args.gain)
else :
    gain_str = ""

if (args.run) :
    runs = args.run
if (args.cfgFile) :
    runs, levels = ReadCfg(args.cfgFile)

for i,name in enumerate(runs) :
    file_name_pattern = f"RUN{name}_"
    folder_path = "/junofs/users/gferrante/BiPo/root/Complete_runs/"

    found_file = None
    for file in os.listdir(folder_path):
        if file.startswith(file_name_pattern) and file.endswith(".root"):
            found_file = file
            break

    if (found_file == None) : 
        print(f"ERROR: RUN{name} not found ")
        break
    else : infile = folder_path+found_file

    if (args.cfgFile) :
        level_str = f" -volume {levels[i][0]} {levels[i][1]}"
    else : level_str = f" -volume {args.volume}"

    sh_file=cwd+"/sh/BiPoAnalysis_RUN"+name+".sh"
    log_file=cwd+"/log/RUN"+name+".log"
    err_file=cwd+"/err/RUN"+name+".err"
    out_file=cwd+"/out/RUN"+name+".out"
    to_launch=cwd+"/BiPo.py"

    autolauncher.write("hep_sub -g juno -mem 4000 -wt mid -o "+out_file+" -e "+err_file+" "+sh_file+"\n" )

    of=open(sh_file,"w")
    of.write('#!/bin/bash\n')
    of.write('import time\n')
    of.write("source /cvmfs/juno.ihep.ac.cn/el9_amd64_gcc11/Release/J25.1.6/setup.sh\n")
    of.write("python " + to_launch + " -input " + infile + " -outDir "+cwd+"/Results -stepTime 1" + gain_str + level_str )
    of.close()

    os.chmod(sh_file,0o755)

    print(f"Run {name} ready for launch")

autolauncher.close()

os.chmod(cwd+"/launch/Launch"+now_str+".sh",0o755)

