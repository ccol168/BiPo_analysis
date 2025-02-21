import os
import argparse
import re

def find_files_with_string(directory, search_string):
    matching_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if search_string in file:
                matching_files.append(os.path.join(root, file))
    return matching_files

def extract_name(filename):
    match = re.search(r'rawfile_(\w+)\.list', filename)
    return match.group(1) if match else None

parser = argparse.ArgumentParser(description="Launch a run from esd files, list in this dir")
parser.add_argument("-RunName", help="Name of the run",required=True)
parser.add_argument("-launch",help="Launch the jobs immediately",action="store_true")

args = parser.parse_args()

directory = "/junofs/users/gferrante/BiPo/list/"

names_string = find_files_with_string(directory,"RUN" + args.RunName)
names_corr_string = find_files_with_string("/junofs/users/gferrante/BiPo/list_rtraw/","RUN" + args.RunName)

if(args.launch==False) :
    c_launch_file = open("/junofs/users/gferrante/BiPo/c_launch/Launch_RUN" + args.RunName + ".sh","w")

for listname,listname_rtraw in zip(names_string,names_corr_string) :
    RunID = extract_name(listname)
    os.system("python Read_esd.py -inList " + listname + " -corrList "+ listname_rtraw + " -RunID " + RunID )
    print("python Read_esd.py -inList " + listname +  " -corrList "+ listname_rtraw + " -RunID " + RunID )
    if (args.launch) :
      os.system("hep_sub -g juno -wt mid -o /junofs/users/gferrante/BiPo/out/"+RunID+".out -e /junofs/users/gferrante/BiPo/err/"+RunID+".err /junofs/users/gferrante/BiPo/sh/"+RunID+".sh")
    else :
        c_launch_file.write("hep_sub -g juno -wt mid -o /junofs/users/gferrante/BiPo/out/"+RunID+".out -e /junofs/users/gferrante/BiPo/err/"+RunID+".err /junofs/users/gferrante/BiPo/sh/"+RunID+".sh\n")
      
if (args.launch == False) :
    os.chmod("/junofs/users/gferrante/BiPo/c_launch/Launch_RUN" + args.RunName + ".sh", 0o775)