import glob # File manipulation
from os import path,chdir # path and directory checking
from numpy import genfromtxt # To read files 
from os import path,makedirs,system # To check file paths and create directories
from shutil import copy,move # copy and move files 
from netCDF4 import Dataset # interface to netCDF
import time 
from processmanager import * # Run serial and parallel processes 

class wrfinterface():
	def __init__(self,filename,qtmessage):
		print("Running WRF")
		self.qtmessage=qtmessage
		if(self.qtmessage=="yes"):
			pass
		else:
			codepath=path.dirname(path.realpath(__file__))
			# Step 1: Check if wrf bin paths exist and initialize the variables 
			wrfbinok,caseok=self.checkwrf(filename)
			if(wrfbinok and caseok):
				print("Case check ok")
			else: 
				print(wrfbinok,caseok)
				exit(-1)
			# Step 2: Check main case folder and wps folder
			if(path.isdir(self.casepath) and path.isdir(self.casepath+"/wps") ):
				chdir(self.casepath)
				if(path.isfile("wrfinitialized.done")):
					pass
				else:
					print("WPS not completed")
					exit(-1)
			else:
				print("System not properly initialized")
				exit(-1)
			self.casewpspath=self.casepath+"/wps"
			self.casewrfpath=self.casepath+"/wrf"
			# Step 3 Create WRF domains 
			self.wrfdomains = []
			for i in range(0,5):
				self.wrfdomains.append(self.casewrfpath+"/run"+str(i)) 
				if(path.isdir(self.wrfdomains[i])):
					pass
				else:
					makedirs(self.wrfdomains[i])
			# Step 4 Copy metgrid output
			chdir(self.casewpspath)
			listing=glob.glob("met*.nc")
			print(listing)
			chdir(self.casewrfpath)
			for i in range(0,5):
				chdir(self.wrfdomains[i])
				for j in range(0,len(listing)):
					if(path.isfile(listing[j])):
						pass
					else:
						copy(self.casewpspath+"/"+listing[j],self.wrfdomains[i])
			# Step 5: Copy WRf run-time files 
			chdir(self.casewrfpath)
			if(path.isfile("runfiles.copyok")):
				print("Runfile copy check")
				pass
			else:
				listing=glob.glob(codepath+"/libs/wrf/runfiles/*")
				for i in range(0,5):
					for j in range(0,len(listing)):
						copy(listing[j],self.wrfdomains[i])
			# Marking that files have been copied 
			system("touch runfiles.copyok")
			# Step 6: Copy customized namelist.input files 
			# Check if already copied 
			if(path.isfile(self.casewrfpath+"/yearset.ok")):
				pass
			else:
				for i in range(0,5):
					listing=glob.glob(codepath+"/libs/wrf/run"+str(i)+"/*")
					for j in range(0,len(listing)):
						copy(listing[j],self.wrfdomains[i])
			# Step 7: Adjust case dates and time 
			self.adjustdateandtime()
			# Step 8: Run WRF - Global 
			flag=self.runparentdomain()
			# Step 9: Run child domains
			for i in range(1,5):
				if(flag):
					flag=self.runchilddomain(i)
				else:
					print("Run failed for child domain ",i)
					exit(-1)
			
	def checkwrf(self,filename):
		# Minutes and second not supported now 
		filedata=genfromtxt(filename,delimiter=",",dtype="str")
		wpsbinok=False
		wpsgeook=False
		wrfbinok=False
		caseok=True
		self.verticalLevels=48
		for i in range(0,filedata.shape[0]):
			if(filedata[i,0]=="dirpath"):
				casedir=filedata[i,1]
			if(filedata[i,0]=="casename"):
				casename=filedata[i,1]
			if(filedata[i,0]=="wrfbinpath"):
				self.wrfbinpath=filedata[i,1]+str("/")
				if(path.isdir(self.wrfbinpath)):
					wrfbinok=True
			if(filedata[i,0]=="startyear"):
				self.startyear=int(filedata[i,1])
			if(filedata[i,0]=="endyear"):
				self.endyear=int(filedata[i,1])				
			if(filedata[i,0]=="startmonth"):
				self.startmonth=int(filedata[i,1])
			if(filedata[i,0]=="endmonth"):
				self.endmonth=int(filedata[i,1])
			if(filedata[i,0]=="startday"):
				self.startday=int(filedata[i,1])
			if(filedata[i,0]=="endday"):
				self.endday=int(filedata[i,1])
			if(filedata[i,0]=="starthour"):
				self.starthour=int(filedata[i,1])
			if(filedata[i,0]=="endhour"):
				self.endhour=int(filedata[i,1])
			#Added for new physics 
			if(filedata[i,0]=="blphysics"):
				self.blphysics=int(filedata[i,1])
			if(filedata[i,0]=="macrocloudphysics"):
				self.macrocloudphysics=int(filedata[i,1])
			if(filedata[i,0]=="microcloudphysics"):
				self.microcloudphysics=int(filedata[i,1])
			if(filedata[i,0]=="longwavephysics"):
				self.longwavephysics=int(filedata[i,1])
			if(filedata[i,0]=="shortwavephysics"):
				self.shortwavephysics=int(filedata[i,1])
			if(filedata[i,0]=="verticalLevels"):
				self.verticalLevels=int(filedata[i,1])								
		# Convert to integer
		syear=int(self.startyear)
		eyear=int(self.endyear)		
		smonth=int(self.startmonth)
		emonth=int(self.endmonth)
		sday=int(self.startday)
		eday=int(self.endday)
		shour=int(self.starthour)
		ehour=int(self.endhour)
		# If end hour is 24 then need to change few things 
		print(self.endhour)
		if(ehour==24):
			print("Fixing end hour")
			self.endhour="0"
			self.endday=str(int(self.endday)+1)
		# Checking is incomplete. Need to be made comprehensive in future. 
		self.casepath=casedir+"/"+casename
		if(syear<2000):
			print("Interface works only for 2000 and later")
			caseok=False
		if(syear>=eyear and emonth<smonth):
			print("End month cannot be earlier than start month")
			caseok=False
		if(syear>=eyear and  smonth==emonth and eday<sday):
			print("End day cannot be earlier than start day")
			caseok=False
		return wrfbinok,caseok

	def adjustdateandtime(self):
		chdir(self.casepath)
		# Convert to integer
		syear=int(self.startyear)
		smonth=int(self.startmonth)
		emonth=int(self.endmonth)
		sday=int(self.startday)
		eday=int(self.endday)
		shour=int(self.starthour)
		ehour=int(self.endhour)
		if(path.isfile(self.casewrfpath+"/yearset.ok")):
			pass
		else:
			# Modify namelist to match year, month, day and time 
			if(smonth<10):
				smonth=str(0)+str(self.startmonth)
			else:
				smonth=str(self.startmonth)
			if(emonth<10):
				emonth=str(0)+str(self.endmonth)
			else:
				emonth=str(self.endmonth)
			if(sday<10):
				sday=str(0)+str(self.startday)
			else:
				sday=str(self.startday)
			if(eday<10):
				eday=str(0)+str(self.endday)
			else:
				eday=str(self.endday)
			if(shour<10):
				shour=str(0)+str(self.starthour)
			else:
				shour=str(self.starthour)
			if(ehour<10):
				ehour=str(0)+str(self.endhour)
			else:
				ehour=str(self.endhour)
			chdir(self.casewrfpath)
			# Met grid levels change with year. So have to fix them according to grib data
			listing=glob.glob(self.casewpspath+"/met_em.d02*")
			metdata=Dataset(listing[0])
			metUU=metdata.variables["UU"]
			nml=str(metUU.shape[1])
			from datetime import date
			startdate=date(int(self.startyear),int(self.startmonth),int(self.startday))
			enddate=date(int(self.endyear),int(self.endmonth),int(self.endday))
			totaldays=(enddate-startdate)
			runhours=totaldays.days*24
			# Remove the starthours greater than zero 
			runhours=runhours-int(self.starthour)+int(self.endhour)
			data=genfromtxt(self.casewpspath+"/nestloc.info",delimiter=",",dtype=int)
			lonloc=data[0,:]
			latloc=data[1,:]
			print("Run hours:",runhours)
			target=open("wrfreplace.sh","w")
			target.write('sed -i "s/runhours/%s/g" run*/namelist.input* \n'%(runhours))
			target.write('sed -i "s/eyr/%s/g" run*/namelist.input* \n'%(self.endyear))						
			target.write('sed -i "s/yr/%s/g" run*/namelist.input* \n'%(self.startyear))
			target.write('sed -i "s/smth/%s/g" run*/namelist.input* \n'%(smonth))
			target.write('sed -i "s/emth/%s/g" run*/namelist.input* \n'%(emonth))
			target.write('sed -i "s/first/%s/g" run*/namelist.input* \n'%(sday))
			target.write('sed -i "s/last/%s/g" run*/namelist.input* \n'%(eday))
			target.write('sed -i "s/begintime/%s/g" run*/namelist.input* \n'%(shour))
			target.write('sed -i "s/endtime/%s/g" run*/namelist.input* \n'%(ehour))
			target.write('sed -i "s/nml/%s/g" run*/namelist.input* \n'%(nml))
			target.write('sed -i "s/blphysics/%s/g" run*/namelist.input* \n'%(self.blphysics))
			target.write('sed -i "s/macrocloudphysics/%s/g" run*/namelist.input* \n'%(self.macrocloudphysics))
			target.write('sed -i "s/microcloudphysics/%s/g" run*/namelist.input* \n'%(self.microcloudphysics))
			target.write('sed -i "s/longwavephysics/%s/g" run*/namelist.input* \n'%(self.longwavephysics))			
			target.write('sed -i "s/shortwavephysics/%s/g" run*/namelist.input* \n'%(self.shortwavephysics))
			target.write('sed -i "s/verticalLevels/%s/g" run*/namelist.input* \n'%(self.verticalLevels))
			if(self.blphysics==12):
				stringToInclude='"s/sf_sfclay_physics        = 12,12,/sf_sfclay_physics        = 1,1,/g"'
				target.write('sed -i '+stringToInclude+' run*/namelist.input* \n')
				stringToInclude='"s/sf_sfclay_physics        = 12,/sf_sfclay_physics        = 1,/g"'
				target.write('sed -i '+stringToInclude+'  run*/namelist.input* \n')
			elif(self.blphysics==8):
				stringToInclude='"s/sf_sfclay_physics        = 8,8,/sf_sfclay_physics        = 1,1,/g"'
				target.write('sed -i '+stringToInclude+' run*/namelist.input* \n')
				stringToInclude='"s/sf_sfclay_physics        = 8,/sf_sfclay_physics        = 1,/g"' 
				target.write('sed -i '+stringToInclude+'  run*/namelist.input* \n')
			elif(self.blphysics==11):
				stringToInclude='"s/sf_sfclay_physics        = 11,11,/sf_sfclay_physics        = 1,1,/g"'
				target.write('sed -i '+stringToInclude+' run*/namelist.input* \n')
				stringToInclude='"s/sf_sfclay_physics        = 11,/sf_sfclay_physics        = 1,/g"'
				target.write('sed -i '+stringToInclude+'  run*/namelist.input* \n')
			# Write case specific changes 
			target.write('sed -i "s/1,nestlocx,/1,%d,/g" run1/namelist.input* \n'%(lonloc[0]))
			target.write('sed -i "s/1,nestlocy,/1,%d,/g" run1/namelist.input* \n'%(latloc[0]))
			target.write('sed -i "s/1,nestlocx,/1,%d,/g" run2/namelist.input* \n'%(lonloc[1]))
			target.write('sed -i "s/1,nestlocy,/1,%d,/g" run2/namelist.input* \n'%(latloc[1]))
			target.write('sed -i "s/1,nestlocx,/1,%d,/g" run3/namelist.input* \n'%(lonloc[2]))
			target.write('sed -i "s/1,nestlocy,/1,%d,/g" run3/namelist.input* \n'%(latloc[2]))
			target.write('sed -i "s/1,nestlocx,/1,%d,/g" run4/namelist.input* \n'%(lonloc[3]))
			target.write('sed -i "s/1,nestlocy,/1,%d,/g" run4/namelist.input* \n'%(latloc[3]))
			target.write('sed -i "s/1,nestlocx,/1,%d,/g" run5/namelist.input* \n'%(lonloc[4]))
			target.write('sed -i "s/1,nestlocy,/1,%d,/g" run5/namelist.input* \n'%(latloc[4]))
			target.write("touch yearset.ok")
			target.close()
			system("bash wrfreplace.sh > log.wrfreplace")
			time.sleep(5)

	def runparentdomain(self):
		# Run Real
		chdir(self.wrfdomains[0])
		flag=False
		processname="real.exe"
		flag=self.checkprocesscompletion(processname)
		if(flag):
			pass
		else:
			flag=runparallelprocess(self.wrfbinpath,"real.exe")
		if(flag):
			processname="wrf.exe"
			flag=False
			flag=self.checkprocesscompletion(processname)
			if(flag):
				pass
			else:
				flag=runparallelprocess(self.wrfbinpath,"wrf.exe")
		else:
			print("WRF initialization failed. Not running.")
		chdir(self.casepath)
		return flag

	def checkprocesscompletion(self,processname):
		if(path.isfile("rsl.error.0000")):
			if(processname=="real.exe"):
				with open("rsl.error.0000") as f:
					if 'SUCCESS COMPLETE REAL_EM INIT' in f.read():
						print("Succesful parallel run of ",processname)
						flag=True
						return flag
				with open("rsl.error.0000") as f:
					if 'SUCCESS COMPLETE WRF' in f.read():
						print("Succesful parallel run of ",processname)
						flag=True
						return flag
				with open("rsl.error.0000") as f:
					if 'SUCCESS COMPLETE NDOWN_EM INIT' in f.read():
						print("Succesful parallel run of ",processname)
						flag=True
						return flag
			if(processname=="ndown.exe"):
				with open("rsl.error.0000") as f:
					if 'SUCCESS COMPLETE WRF' in f.read():
						print("Succesful parallel run of ",processname)
						flag=True
						return flag
				with open("rsl.error.0000") as f:
					if 'SUCCESS COMPLETE NDOWN_EM INIT' in f.read():
						print("Succesful parallel run of ",processname)
						flag=True
						return flag
			if(processname=="wrf.exe"):
				with open("rsl.error.0000") as f:
					if 'SUCCESS COMPLETE WRF' in f.read():
						print("Succesful parallel run of ",processname)
						flag=True
						return flag

	def runchilddomain(self,childnumber):
		print("Running child domain",childnumber)
		chdir(self.wrfdomains[childnumber])
		# Have to fix met files for children > 1 
		if(childnumber>1):
			listing1=glob.glob(self.wrfdomains[childnumber]+"/met_em.d0"+str(childnumber)+"*")
			listing2=glob.glob(self.wrfdomains[childnumber]+"/met_em.d01*")
			copy(listing1[0],listing2[0])
			listing1=glob.glob(self.wrfdomains[childnumber]+"/met_em.d0"+str(childnumber+1)+"*")
			listing2=glob.glob(self.wrfdomains[childnumber]+"/met_em.d02*")
			copy(listing1[0],listing2[0])
		flag=False
		# Check if real.exe has been run before 
		copy("namelist.input.real","namelist.input")
		processname="real.exe"
		flag=self.checkprocesscompletion(processname)
		if(flag):
			pass
		else:
			flag=runparallelprocess(self.wrfbinpath,processname)
		if(flag):
			processname="ndown.exe"
			flag=False
			flag=self.checkprocesscompletion(processname)
			if(flag):
				pass
			else:
				# ndown
				copy("wrfinput_d02","wrfndi_d02")
				listing=glob.glob(self.wrfdomains[childnumber-1]+"/wrfout*")
				if(len(listing)>0):
					import os
					copy(listing[0],os.getcwd())
				copy("namelist.input.ndown","namelist.input")
				flag=runparallelprocess(self.wrfbinpath,processname)
		# WRF 
		if(flag):
			processname="wrf.exe"
			flag=False
			flag=self.checkprocesscompletion(processname)
			if(flag):
				pass
			else:
				copy("wrfinput_d02","wrfinput_d01")
				copy("wrfbdy_d02","wrfbdy_d01")
				copy("namelist.input.wrf","namelist.input")
				listing=glob.glob(self.wrfdomains[childnumber]+"/met_em.d02*")
				metdata=Dataset(listing[0])
				metLUIndex=metdata.variables["LU_INDEX"]
				inputdata=Dataset("wrfinput_d01",'r+')
				inputLUIndex=inputdata.variables["LU_INDEX"]
				inputLUIndex[:,:,:]=metLUIndex[:,:,:]
				inputdata.close()
				flag=runparallelprocess(self.wrfbinpath,processname)
				if(flag):
					print("Completed child domain",childnumber)
				else:
					print("Process failed for child:",childnumber," further simulations cannot be run")
		return flag
