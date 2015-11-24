import cv2
import numpy
import os 
import glob
import ntpath
from backSub import *
from ConfigParser import SafeConfigParser


filepath = "./tl3Pictures/" # where the input files are
pathRGB = ".diff/"   # where the result is saved

extension = "*.jpg"   # only jpg files considered
batchCount = 0
backSubInstance = backSub()


if not os.path.exists(filepath + pathRGB):
	os.makedirs(filepath+pathRGB)  #create the result folder if it 
								   # is not there    

backSubInstance.setConfig('sample.cfg')   # load the backSub parameters 
								  # from the configuration file	

for filename in glob.glob(filepath + extension): 
	#print(filename) #full file name and path
	pathAndFile = os.path.splitext(filename)[0]
	#print(pathAndFile)	#file name and path without extension 
	latestFilename = ntpath.basename(pathAndFile)
	#print(latestFilename) #only file name

	image = cv2.imread(filepath + latestFilename + ".jpg",\
		cv2.CV_LOAD_IMAGE_COLOR) #read the image from the source
	print(latestFilename)
	diffImage = backSubInstance.getDiff(image) # get the difference image

	resultFileName =  filepath + pathRGB + latestFilename + "motion"+ \
	 str(batchCount) + ".jpg" #contruct the path where to save diffImage
	cv2.imwrite(resultFileName, diffImage) # write the image to the
	 										# destination
	batchCount +=1                         
