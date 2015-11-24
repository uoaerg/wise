import cv2
import cv2.cv as cv
import numpy as np
import os
import glob
import ntpath
from backSub import *
from ConfigParser import SafeConfigParser

filepath = "./inoffice/"
pathBGR = "./diff/"
#filepath = "./smallOffice/"
#pathBGR = "./diffBGR/"
extension = "*.jpg"
batchCount = 0
back_sub = backSub()

#roiMask = cv2.imread("./inoffice/" + "officeMask.jpg", cv2.CV_LOAD_IMAGE_COLOR)
#back_sub.ROI = roiMask

if not os.path.exists(filepath + pathBGR):
     os.makedirs(filepath + pathBGR)

back_sub.setConfig('sample.cfg')   
  
for filename in glob.glob(filepath+extension):
        PathAndFile = os.path.splitext(filename)[0]
        latestFilename = ntpath.basename(PathAndFile)    
        
        image = cv2.imread(filepath + latestFilename + ".jpg", cv2.CV_LOAD_IMAGE_COLOR)
        print(latestFilename)
        diffImage = back_sub.getDiff(image)
        
        Filename = filepath + pathBGR + \
        latestFilename + 'motion' + str(batchCount) + '.jpg' 
        cv2.imwrite(Filename, diffImage)
        batchCount += 1
