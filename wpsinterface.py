# WPS - Interface 
from numpy import genfromtxt # To read files 
from numpy import array # To initialize arrays
from os import path,makedirs # To check file paths and create directories
from os import chdir # Change directories 
from os import remove # Remove a file 
from os import system # system level commands 
from sys import exit # Required to pass arguments 
from shutil import copy,move # copy and move files 
from processmanager import * # Run serial and parallel processes 
from subprocess import Popen # Running serial and parallel processes
from netCDF4 import Dataset # to read netCDF data 
class wpsinterface():
	def __init__(self,filename,qtmessage):
		print("Running WPS")
		self.qtmessage=qtmessage
		if(self.qtmessage=="yes"):
			pass
		else:
			# Step 1: Check if wps bin and geo paths exist and initialize the variables 
			wpsbinok,wpsgeook,caseok=self.checkwps(filename)
			if(wpsbinok and wpsgeook and caseok):
				print("Case check ok")
			else: 
				print(wpsbinok,wpsgeook,caseok)
				exit(-1)
			# Step 2: Create main case folder
			if(path.isdir(self.casepath)):
				pass
			else:
				makedirs(self.casepath)
			# Step 3: Create wps folder 
			self.casewpspath=self.casepath+"/wps"
			if(path.isdir(self.casewpspath)):
				pass
			else:
				makedirs(self.casewpspath)
			# Step 4: Download grib file to wps folder 
			self.gribok=False
			self.gribok=self.creategribcshfile()
			#Step 5: Run Geogrid 
			if(self.gribok):
				self.geogridok=False
				self.geogridok=self.creategeogrid()
			else:
				exit(-1)
			# Step 6: Link fnl file for ungribbing 
			if(self.geogridok):
				# Check if link_grib.csh file is there 
				chdir(self.casewpspath)
				if(path.isfile(self.wpsbinpath+"/link_grib.csh")):
					command=self.wpsbinpath+"/link_grib.csh "+self.casewpspath+"/fnl* > log.linking"
					system(command)
				else:
					print("Linking error. Either wps bin path is incorrect or link_grib.csh file is missing")
					exit(-1)
			else:
				print("Process geogrid did not complete")
				exit(-1)
			chdir(self.casepath)
			# Step 7: Run Ungrib
			chdir(self.casewpspath)
			self.ungribok=runserialprocess(self.wpsbinpath,"ungrib.exe")
			# Step 8: Run Metgrid 
			if(self.ungribok):
				codepath=path.dirname(path.realpath(__file__))
				copy(codepath+"/libs/wps/METGRID.TBL",self.casewpspath)
				self.metgridok=runserialprocess(self.wpsbinpath,"metgrid.exe")
			else:
				print("Process ungrib did not complete")
				exit(-1)
			chdir(self.casepath)
			system(" touch wrfinitialized.done")


	def checkwps(self,filename):
		# Minutes and second not supported now 
		filedata=genfromtxt(filename,delimiter=",",dtype="str")
		wpsbinok=False
		wpsgeook=False
		caseok=True
		for i in range(0,filedata.shape[0]):
			if(filedata[i,0]=="dirpath"):
				casedir=filedata[i,1]
			if(filedata[i,0]=="casename"):
				casename=filedata[i,1]
			if(filedata[i,0]=="wpsbinpath"):
				self.wpsbinpath=filedata[i,1]+str("/")
				if(path.isdir(self.wpsbinpath)):
					wpsbinok=True
			if(filedata[i,0]=="wpsgeopath"):
				self.wpsgeopath=filedata[i,1]+str("/")
				if(path.isdir(self.wpsgeopath)):
					wpsgeook=True
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
			if(filedata[i,0]=="location"):
				self.location=filedata[i,1]
			if(filedata[i,0]=="centlat"):
				self.centlat=float(filedata[i,1])
			if(filedata[i,0]=="centlon"):
				self.centlon=float(filedata[i,1])
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
		if(ehour==24):
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
		if(syear>=eyear and smonth==emonth and eday<sday):
			print("End day cannot be earlier than start day")
			caseok=False
		return wpsbinok,wpsgeook,caseok

	def creategribcshfile(self):
		chdir(self.casewpspath)
		# Convert to integer
		syear=int(self.startyear)
		eyear=int(self.endyear)
		smonth=int(self.startmonth)
		emonth=int(self.endmonth)
		sday=int(self.startday)
		eday=int(self.endday)
		shour=int(self.starthour)
		ehour=int(self.endhour)
		tyear=str(self.startyear)
		if(smonth<10):
			tmonth=str(0)+str(self.startmonth)
		else:
			tmonth=str(self.startmonth)
		if(sday<10):
			tday=str(0)+str(self.startday)
		else:
			tday=str(self.startday)
		if(shour<10):
			thour=str(0)+str(self.starthour)
		else:
			thour=str(self.starthour)
		gribfilename="fnl_"+str(tyear)+str(tmonth)+str(tday)+"_"+str(thour)+"_00.grib2"
		gribok=False
		# Check if grib file already exists 
		if(path.isfile(gribfilename) and path.isfile("log.gribfile")):
			#gribfilesize=path.getsize(gribfilename)/1e6
			#if(gribfilesize>14):
				#print("grib file already exists and is usable.")
				#gribok=True
			with open("log.gribfile") as f:
					if gribfilename in f.read():
						print("Grib file already exists and is usable")
						gribok=True
			if(gribok):
				pass
			else:
				print("Downloading file")
				target=open("testscript","w")
				target.write("#! /bin/csh -f \n")                                                                                          
				#target.write("set passwd = 'XXXXXXXXXX'\n")
				#target.write('set cert_opt = "--no-check-certificate"\n')
				#target.write('set cert_opt= " "\n')
				#target.write('set opts = "-N"\n')
				#target.write('wget $cert_opt -O auth_status.rda.ucar.edu --save-cookies auth.rda.ucar.edu.$$ --post-data="email=gopalanh@\
	#ihpc.a-star.edu.sg&passwd=$passwd&action=login" https://rda.ucar.edu/cgi-bin/login\n')
	# https://stratus.rda.ucar.edu/ds083.2/grib2/2023/2023.07/fnl_20230726_00_00.grib2
				#target.write('wget $cert_opt $opts --load-cookies auth.rda.ucar.edu.$$ http://stratus.rda.ucar.edu/ds083.2/grib2/%s/%s.%s/fnl_%s%s%s_%s_00.grib2\n'%(tyear,tyear,tmonth,tyear,tmonth,tday,thour))
				target.write('wget -N https://data.rda.ucar.edu/ds083.2/grib2/%s/%s.%s/fnl_%s%s%s_%s_00.grib2\n'%(tyear,tyear,tmonth,tyear,tmonth,tday,thour))
				#target.write('rm auth.rda.ucar.edu.$$ auth_status.rda.ucar.edu\n')
				target.close()
				#system(" (tcsh testscript) >& log.gribfile ")
				target=open("log.gribfile","w")
				p=Popen(["csh", "testscript"],stdout=target,stderr=target)
				p.wait()
				target.close()    
				#time.sleep(5)
				with open("log.gribfile") as f:
					if gribfilename in f.read(): 
						print("grib file is usable")
						gribok=True
		else:
			print("Downloading file")
			target=open("testscript","w")
			target.write("#! /bin/csh -f \n")                                                                                          
			#target.write("set passwd = 'XXXXXXXXXX'\n")
			#target.write('set cert_opt = "--no-check-certificate"\n')
			#target.write('set cert_opt= " "\n')
			#target.write('set opts = "-N"\n')
			#target.write('wget $cert_opt -O auth_status.rda.ucar.edu --save-cookies auth.rda.ucar.edu.$$ --post-data="email=gopalanh@\
#ihpc.a-star.edu.sg&passwd=$passwd&action=login" https://rda.ucar.edu/cgi-bin/login\n')
# https://stratus.rda.ucar.edu/ds083.2/grib2/2023/2023.07/fnl_20230726_00_00.grib2
			#target.write('wget $cert_opt $opts --load-cookies auth.rda.ucar.edu.$$ http://stratus.rda.ucar.edu/ds083.2/grib2/%s/%s.%s/fnl_%s%s%s_%s_00.grib2\n'%(tyear,tyear,tmonth,tyear,tmonth,tday,thour))
			target.write('wget -N https://data.rda.ucar.edu/ds083.2/grib2/%s/%s.%s/fnl_%s%s%s_%s_00.grib2\n'%(tyear,tyear,tmonth,tyear,tmonth,tday,thour))
			#target.write('rm auth.rda.ucar.edu.$$ auth_status.rda.ucar.edu\n')
			target.close()
			#system(" (tcsh testscript) >& log.gribfile ")
	# 		target=open("testscript","w")
	# 		target.write("#! /bin/csh -f \n")
	# 		target.write("set passwd = 'XXXXXXXXXX'\n")
	# 		target.write('set cert_opt = "--no-check-certificate"\n')
	# 		target.write('set opts = "-N"\n')
	# 		target.write('wget $cert_opt -O auth_status.rda.ucar.edu --save-cookies auth.rda.ucar.edu.$$ --post-data="email=gopalanh@\
	# ihpc.a-star.edu.sg&passwd=$passwd&action=login" https://rda.ucar.edu/cgi-bin/login\n')
	# 		target.write('wget $cert_opt $opts --load-cookies auth.rda.ucar.edu.$$ http://stratus.rda.ucar.edu/ds083.2/grib2/%s/%s.%s/fnl_%s%s%s_%s_00.grib2\n'%(tyear,tyear,tmonth,tyear,tmonth,tday,thour))
	# 		target.write('rm auth.rda.ucar.edu.$$ auth_status.rda.ucar.edu\n')
	# 		target.close()
			#system("touch log.gribfile")
			#system(" csh testscript >& log.gribfile")
			target=open("log.gribfile","w")
			p=Popen(["csh", "testscript"],stdout=target,stderr=target)
			p.wait()
			target.close()                    
			with open("log.gribfile") as f:
				if gribfilename in f.read():
					print("grib file is usable")
					gribok=True
		chdir(self.casepath)
		return gribok

	def creategeogrid(self):
		chdir(self.casewpspath)
		codepath=path.dirname(path.realpath(__file__))
		# Copy VTable 
		copy(codepath+"/libs/wps/Vtable",self.casewpspath)
		# Copy Geogrib handling table
		# A check will be added in future here 
		copy(codepath+"/libs/wps/GEOGRID.TBL",self.casewpspath)
		# Copy geogrid for world 
		copy(codepath+"/libs/wps/geo_em.d01.nc",self.casewpspath)
		# Create namelist.wps file 
		self.createwpsnamelist()
		# Check if geo files exist. If not run
		for i in range(1,6):
			if(path.isfile(self.casewpspath+"/geo_em.d0"+str(i)+".nc")):
				print("Found file "+"geo_em.d0"+str(i)+".nc")
				geogridok=True
			else:
				geogridok=False
		if(not geogridok):
			# Need to run geogrid. Not doing it for demo 
			#for i in range(1,5):
			#	copy(codepath+"/libs/Singapore/geo_em.d0"+str(i)+".nc",self.casewpspath)
			# Update Dummy geo file 
			self.updategeogrid()
			geogridok=True
		#if(flag==1):
		#	flag=self.runserialprocess("geogrid.exe")
		#else:
		#	flag=1
		return geogridok


	def updategeogrid(self):
		# 23/9/2020 - Added for changing lat and lon 
		chdir(self.casewpspath)
		fh = Dataset("geo_em.d01.nc")
		lats = fh.variables['XLAT_M'][:]
		lons = fh.variables['XLONG_M'][:]
		lat_1d=lats[0,:,1]
		lon_1d=lons[0,1,:]
		for i in range(0,len(lat_1d)):
			if(lat_1d[i]>self.centlat):
				center_lat_loc=i
				break
		for i in range(0,len(lon_1d)):
			if(lon_1d[i]>self.centlon):
				center_lon_loc=i
				break
		lonloc=array([40,40,40,40,40])
		lonloc = lonloc.astype(int) #changes to int
		latloc=array([40,40,40,40,40])
		latloc = latloc.astype(int) #changes to int
		lonloc[0]=center_lon_loc-19
		latloc[0]=center_lat_loc-19
		# Fix 2 Domain 
		lonloc,latloc=self.fixdomain(2,lonloc,latloc)
		system("rm geogrid.log")
		# Fix 3 Domain 
		lonloc,latloc=self.fixdomain(3,lonloc,latloc)
		system("rm geogrid.log")
		# Fix 4 Domain 
		lonloc,latloc=self.fixdomain(4,lonloc,latloc)
		system("rm geogrid.log")
		# Fix 5 Domain 
		lonloc,latloc=self.fixdomain(5,lonloc,latloc)
		system("rm geogrid.log")	
		#chdir(self.casepath)


	# Creating namelist.wps file 
	def createwpsnamelist(self):
		chdir(self.casewpspath)
		target=open("namelist.wps","w")
		target.write("&share\n")
		target.write(" wrf_core = 'ARW',\n")
		target.write("max_dom = 5,\n")
		if(self.startmonth<10):
			tmonth=str(0)+str(self.startmonth)
		else:
			tmonth=str(self.startmonth)
		if(self.startday<10):
			tday=str(0)+str(self.startday)
		else:
			tday=str(self.startday)
		if(self.starthour<10):
			thour=str(0)+str(self.starthour)
		else:
			thour=str(self.starthour)
		wpsdate=str(self.startyear)+"-"+str(tmonth)+"-"+str(tday)+"_"+str(thour)+":00:00"
		target.write("start_date ='%s','%s','%s','%s','%s'\n"%(wpsdate,wpsdate,wpsdate,wpsdate,wpsdate))
		target.write("end_date ='%s','%s','%s','%s','%s'\n"%(wpsdate,wpsdate,wpsdate,wpsdate,wpsdate))
		target.write("interval_seconds = 21600,\n")
		target.write("io_form_geogrid = 2,\n")
		target.write("opt_output_from_geogrid_path = './',\n")
		target.write(" debug_level = 0,\n")
		target.write("/ \n")
		target.write("&geogrid \n")
		target.write("parent_id         = 1,1,2,3,4,5 \n")
		target.write("parent_grid_ratio = 1,3,3,3,3,3 \n")
		target.write("i_parent_start    = 1,364,45,30,45,30 \n")
		target.write("j_parent_start    = 1,104,45,30,45,30 \n")
		target.write("e_we              = 487,121,121,121,121,121, \n")
		target.write("e_sn              = 244,121,121,121,121,121, \n")
		target.write("geog_data_res     = 'default+modis_15s','modis_15s','modis_15s','modis_15s','modis_15s','modis_15s','modis_15s' \n")
		target.write("map_proj =  'lat-lon', \n")
		target.write("stand_lon = -180.0, \n")
		target.write("pole_lat=90.0, \n")
		target.write("pole_lon=0.0,  \n")
		target.write("geog_data_path = '%s',\n"%(self.wpsgeopath))
		target.write("opt_geogrid_tbl_path = './', \n")
		target.write("/ \n")
		target.write("&ungrib \n")
		target.write("out_format = 'WPS', \n")
		target.write("prefix = 'FILE', \n")
		target.write("/ \n")
		target.write("&metgrid \n")
		target.write("fg_name = 'FILE', \n")
		target.write("io_form_metgrid = 2, \n")
		target.write("opt_output_from_metgrid_path = './', \n")
		target.write("opt_metgrid_tbl_path = './', \n")
		target.write("/ \n")
		target.close()
		chdir(self.casepath)
	
	# Check Domain 
	def fixdomain(self,domain,lonloc,latloc):
		located=False 
		newlat=latloc
		newlon=lonloc
		while(not located):
			self.modifywpsnamelist(domain,newlon,newlat)
			if(path.isfile("geo_em.d02.nc")):
				system("rm geo_em.d02.nc")
			if(path.isfile("geo_em.d03.nc")):
				system("rm geo_em.d03.nc")
			if(path.isfile("geo_em.d04.nc")):
				system("rm geo_em.d04.nc")
			if(path.isfile("geo_em.d05.nc")):
				system("rm geo_em.d05.nc")
			runspecialserialprocess(self.wpsbinpath,"geogrid.exe")
			fh = Dataset("geo_em.d0"+str(domain)+".nc")
			lats = fh.variables['XLAT_M'][:]
			lons = fh.variables['XLONG_M'][:]
			lat_1d=lats[0,:,1]
			lon_1d=lons[0,1,:]
			for i in range(0,len(lat_1d)):
				if(lat_1d[i]>self.centlat):
					center_lat_loc=i
					break
			for i in range(0,len(lon_1d)):
				if(lon_1d[i]>self.centlon):
					center_lon_loc=i
					break
			print(domain,center_lat_loc,center_lon_loc)
			if(center_lon_loc>=59 and center_lon_loc<=61 and center_lat_loc>=59 and center_lat_loc<=61):
				located=True
			else:
				if(center_lat_loc>61):
					newlat[domain-2]=newlat[domain-2]+1
					print("Lat increase")
				elif (center_lat_loc<59):
					newlat[domain-2]=newlat[domain-2]-1
					print("Lat decrease")
				else:
					print("Passing",newlat[domain-2])
				if(center_lon_loc>61):
					newlon[domain-2]=newlon[domain-2]+1
					print("Lon increase")
				elif (center_lon_loc<59):
					newlon[domain-2]=newlon[domain-2]-1
					print("Lon decrease")
				else:
					print("Passing",newlon[domain-2])
		return newlon,newlat
	
	# Create WPS file fixed around lat,lon of interest
	def modifywpsnamelist(self,domain,lonloc,latloc):
		startmonth=self.startmonth
		startday=self.startday
		starthour=self.starthour
		year=self.startyear
		wpsgeopath='/projects/hfm/hgopalan/WPS_GEOG/'
		target=open("namelist.wps","w")
		target.write("&share\n")
		target.write(" wrf_core = 'ARW',\n")
		target.write("max_dom = %d,\n"%(domain))
		if(startmonth<10):
			tmonth=str(0)+str(startmonth)
		else:
			tmonth=str(startmonth)
		if(startday<10):
			tday=str(0)+str(startday)
		else:
			tday=str(startday)
		if(starthour<10):
			thour=str(0)+str(starthour)
		else:
			thour=str(starthour)
		wpsdate=str(year)+"-"+str(tmonth)+"-"+str(tday)+"_"+str(thour)+":00:00"
		target.write("start_date ='%s','%s','%s','%s','%s'\n"%(wpsdate,wpsdate,wpsdate,wpsdate,wpsdate))
		target.write("end_date ='%s','%s','%s','%s','%s'\n"%(wpsdate,wpsdate,wpsdate,wpsdate,wpsdate))
		target.write("interval_seconds = 21600,\n")
		target.write("io_form_geogrid = 2,\n")
		target.write("opt_output_from_geogrid_path = './',\n")
		target.write(" debug_level = 0,\n")
		target.write("/ \n")
		target.write("&geogrid \n")
		target.write("parent_id         = 1,1,2,3,4 \n")
		target.write("parent_grid_ratio = 1,3,3,3,3 \n")
		target.write("i_parent_start    = 1,%d,%d,%d,%d,%d\n"%(lonloc[0],lonloc[1],lonloc[2],lonloc[3],lonloc[4]))
		target.write("j_parent_start    = 1,%d,%d,%d,%d,%d\n"%(latloc[0],latloc[1],latloc[2],latloc[3],latloc[4]))
		target.write("e_we              = 487,121,121,121,121 \n")
		target.write("e_sn              = 244,121,121,121,121 \n")
		target.write("geog_data_res     = 'default+modis_15s','modis_15s','modis_15s','modis_15s','modis_15s'\n")
		target.write("map_proj =  'lat-lon', \n")
		target.write("stand_lon = -180.0, \n")
		target.write("pole_lat=90.0, \n")
		target.write("pole_lon=0.0,  \n")
		target.write("geog_data_path = '%s',\n"%(wpsgeopath))
		target.write("opt_geogrid_tbl_path = './', \n")
		target.write("/ \n")
		target.write("&ungrib \n")
		target.write("out_format = 'WPS', \n")
		target.write("prefix = 'FILE', \n")
		target.write("/ \n")
		target.write("&metgrid \n")
		target.write("fg_name = 'FILE', \n")
		target.write("io_form_metgrid = 2, \n")
		target.write("opt_output_from_metgrid_path = './', \n")
		target.write("opt_metgrid_tbl_path = './', \n")
		target.write("/ \n")
		target.close()
		target=open("nestloc.info","w")
		target.write("%d,%d,%d,%d,%d\n"%(lonloc[0],lonloc[1],lonloc[2],lonloc[3],lonloc[4]))
		target.write("%d,%d,%d,%d,%d\n"%(latloc[0],latloc[1],latloc[2],latloc[3],latloc[4]))		
		target.close()
