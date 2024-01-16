'''
!---------------------------------------------------------------------------!
! IHPC Solar Forecaster                                                     !
!---------------------------------------------------------------------------!
! A GUI and batch mode tool for setting up global WRF simulations. The WRF  !
! and WPS system are assumed to be installed and properly compiled. The WPS !
! geography data should also have been downloaded.                          !
! This is a very preliminary version of the system and can be buggy.        !                 
!---------------------------------------------------------------------------!

'''
# Libraries to load 
#!/usr/bin/python3
import argparse # For parsing batch mode arguments 
from wpsinterface import wpsinterface # Interface to WPS preprocessing system
from wrfinterface import wrfinterface # Interface to WRF 
from numpy import genfromtxt # To read files 
from os import path # To check file paths 
from PyQt5.QtWidgets import QApplication # If GUI is called 
from sys import argv,exit # Required to pass arguments 

# Generate Case Folder 
def generatecase(filename):
	filedata=genfromtxt(filename,delimiter=",",dtype="str")
	dirok=False
	casenameok=False
	for i in range(0,filedata.shape[0]):
		if(filedata[i,0]=="dirpath"):
			if(path.isdir(filedata[i,1])):
				dirok=True
		if(filedata[i,0]=="casename"):
			casenameok=True
	return dirok,casenameok


# Main Window 
if __name__ == '__main__':
	if len(argv)>1:
		for i in range(1,len(argv)):
			print(argv[i])
			if(path.isfile(argv[i])):
				# Setup the case folders 
				dirok,casenameok=generatecase(argv[i])
				# If directory exists and there is a casename 
				if(dirok and casenameok):
					# Running WPS preprocessor 
					wpscall=wpsinterface(argv[i],"no")
					print(wpscall.metgridok)
					# Run WRF 
					if(wpscall.metgridok):
						wrfcall=wrfinterface(argv[i],"no")
				else:
					print("Directory is missing or casename not provided. Please modify input datafile.")
					exit(-1)			
	# parser = argparse.ArgumentParser()
	# # Argument to start batch mode
	# parser.add_argument('-batch',action="store_true",help="Batch mode for solar forecaster")
	# # Data file to read from batch mode 
	# parser.add_argument('batchfile',type=str,nargs='?', default='wrfdata', const='wrfdata')
	# a = parser.parse_args()
	# if a.batch:
		# if(path.isfile(a.batchfile)):
			# # Setup the case folders 
			# dirok,casenameok=generatecase(a.batchfile)
			# # If directory exists and there is a casename 
			# if(dirok and casenameok):
				# # Running WPS preprocessor 
				# wpscall=wpsinterface(a.batchfile,"no")
				# print(wpscall.metgridok)
				# # Run WRF 
				# if(wpscall.metgridok):
					# wrfcall=wrfinterface(a.batchfile,"no")
			# else:
				# print("Directory is missing or casename not provided. Please modify input datafile.")
				# exit(-1)
		# else:
			# print("No batchfile found. Exiting...")
	else:
		print("Need batch file(s) with user settings")
			
'''
	else:
		app = QApplication(argv)
		fontsize = "15px"
		app.setStyleSheet("QWidget { font-size:" + fontsize + "; } QLineEdit { font: bold; } QComboBox { font-size: 12px; }")   
		ex = IHPCSolarForecast()
		exit(app.exec_())
'''
