from os import path
import time 
from subprocess import Popen
# Serial Process 
def runserialprocess(bindir,processname,flags='None'):
	# Check if we finished it before 
	if(path.isfile(processname[:-4]+".log")):
		with open(processname[:-4]+".log") as f:
			if 'Successful completion of program '+processname in f.read():
				print("Succesful run of ",processname)
				flag=True
				return flag
	# Running using subprocess
	print("Running serial process:",processname)
	if(flags=='None'):
		runcommand="nohup "+bindir+"/"+processname
		proc=Popen(runcommand,stdout=open("/dev/null",'w'),stderr=open("/dev/null",'w'),shell=True)
	else:
		runcommand="nohup "+bindir+"/"+processname+" "+flags
		proc=Popen(runcommand,stdout=open("/dev/null",'w'),stderr=open("/dev/null",'w'),shell=True)
	comeout=True
	time.sleep(5)
	starttime=time.time()
	while(comeout):
		procrun = proc.poll()
		if(procrun==None):
			comeout=True
		else:
			comeout=False
	with open(processname[:-4]+".log") as f:
		if 'Successful completion of program '+processname in f.read():
			print("Succesful run of ",processname)
			flag=True
		else:
			flag=False
	return flag

# Serial Process 
def runparallelprocess(bindir,processname,flags='None'):
	print("Running parallel process:",processname)
	if(flags=='None'):
		runcommand="nohup mpirun -np 8 "+bindir+"/"+processname
		proc=Popen(runcommand,stdout=open("/dev/null",'w'),stderr=open("/dev/null",'w'),shell=True)
	else:
		runcommand="nohup mpirun -np 8 "+bindir+"/"+processname+" "+flags
		proc=Popen(runcommand,stdout=open("/dev/null",'w'),stderr=open("/dev/null",'w'),shell=True)
	comeout=True
	time.sleep(5)
	starttime=time.time()
	while(comeout):
		procrun = proc.poll()
		if(procrun==None):
			comeout=True
		else:
			comeout=False
		with open("rsl.error.0000") as f:
			if(processname=="real.exe" or processname=="ndown.exe" or processname=="wrf.exe"):
				if 'FATAL CALLED' in f.read():
					print("Code crashed in parallel run of ",processname)
					flag=False
					comeout=False
	with open("rsl.error.0000") as f:
		if(processname=="real.exe"  or processname=="ndown.exe" or processname=="wrf.exe"):
			if 'SUCCESS COMPLETE' in f.read():
				print("Succesful parallel run of ",processname)
				flag=True
			else:
				print("Process ",processname," failed. Please check rsl.error.0000 file")
				flag=False
	return flag

def runspecialserialprocess(bindir,processname,flags='None'):
	# Check if we finished it before 
	# Running using subprocess
	print("Running serial process:",processname)
	if(flags=='None'):
		runcommand="nohup "+bindir+"/"+processname
		proc=Popen(runcommand,stdout=open("/dev/null",'w'),stderr=open("/dev/null",'w'),shell=True)
	else:
		runcommand="nohup "+bindir+"/"+processname+" "+flags
		proc=Popen(runcommand,stdout=open("/dev/null",'w'),stderr=open("/dev/null",'w'),shell=True)
	comeout=True
	time.sleep(5)
	starttime=time.time()
	while(comeout):
		procrun = proc.poll()
		if(procrun==None):
			comeout=True
		else:
			comeout=False
	with open(processname[:-4]+".log") as f:
		if 'Successful completion of program '+processname in f.read():
			#print("Succesful run of ",processname)
			flag=True
	return flag
