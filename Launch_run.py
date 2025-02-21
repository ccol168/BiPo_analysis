#It takes from input the RUN number

import os
import sys
import argparse
from argparse import RawTextHelpFormatter
from datetime import datetime

prs = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)

prs.add_argument("name",nargs="+", help="Name of the run")

args = prs.parse_args()
cwd=os.getcwd()

now = datetime.now()
now_str = now.strftime("%Y%m%d_%H%M%S")
autolauncher = open(cwd+"/launch/Launch"+now_str+".sh","w")

for name in args.name :
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
    of.write("python " + to_launch + " -input " + infile + " -outDir "+cwd+"/Results -volume 100 -stepTime 1" )
    of.close()

    os.chmod(sh_file,0o755)

    print(f"Run {name} ready for launch")

autolauncher.close()

os.chmod(cwd+"/launch/Launch"+now_str+".sh",0o755)

