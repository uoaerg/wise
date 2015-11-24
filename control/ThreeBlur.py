from ConfigParser import SafeConfigParser
import motion
import cv2
import cv2.cv as cv
import numpy as np


class ThreeBlur():

    def __init__(self):
        # Required to parse the config file
        self.parser = SafeConfigParser()
        # Config parameters
        self.ROI = None

        self.adaptiveThresholdType = cv2.ADAPTIVE_THRESH_MEAN_C
        self.adaptiveThresholdSize = 9
        self.adaptiveThresholdConstant = 4
        self.gaussBlurStdDev = 10
        self.gaussBlurSizeX = 5
        self.gaussBlurSizeY = 5
        self.dilateErodeKernelSize = 3
        self.dilateIterations = 3
        self.erodeIterations = 1
        self.ROIImage = None
        #IR: reseting imgKmin1 and diffK
        self.imageCount = 0
        self.motionSequenceCount = 5

        # Internal variables
        self.gaussBlurSize = (self.gaussBlurSizeX, self.gaussBlurSizeY)
        self.imgKMin2 = None
        self.imgKMin1 = None
        self.imgK = None
        self.diffKMin1 = None
        self.diffK = None
        self.motionKMin1 = None
        self.motionK = None
        
        

    def setConfig(self, aConfig):
        if self.parser.read(aConfig):

            # General
            self.ROI = \
                self.setParam(self.ROI,
                              'str',
                              'General',
                              'ROI')
            # ThreeBlur specific
            self.adaptiveThresholdType = \
                self.setParam(self.adaptiveThresholdType, 'int',
                              'ThreeBlur',
                              'adaptiveThresholdType')
            self.adaptiveThresholdSize = \
                self.setParam(self.adaptiveThresholdSize,
                              'int',
                              'ThreeBlur',
                              'adaptiveThresholdSize')
            self.adaptiveThresholdConstant = \
                self.setParam(self.adaptiveThresholdConstant,
                              'int',
                              'ThreeBlur',
                              'adaptiveThresholdConstant')
            self.gaussBlurStdDev = \
                self.setParam(self.gaussBlurStdDev,
                              'int',
                              'ThreeBlur',
                              'gaussBlurStdDev')
            self.gaussBlurSizeX = \
                self.setParam(self.gaussBlurSizeX,
                              'int',
                              'ThreeBlur',
                              'gaussBlurSizeX')
            self.gaussBlurSizeY = \
                self.setParam(self.gaussBlurSizeY,
                              'int',
                              'ThreeBlur',
                              'gaussBlurSizeY')
            self.dilateErodeKernelSize = \
                self.setParam(self.dilateErodeKernelSize,
                              'int',
                              'ThreeBlur',
                              'dilateErodeKernelSize')
            self.dilateIterations = \
                self.setParam(self.dilateIterations,
                              'int',
                              'ThreeBlur',
                              'dilateIterations')
            self.erodeIterations = \
                self.setParam(self.erodeIterations,
                              'int',
                              'ThreeBlur',
                              'erodeIterations')
            self.motionSequenceCount = self.setParam(self.motionSequenceCount,
                                                     'int',
                                                     'Controller',
                                                     'motionSequenceCount')

            if self.ROI is not None:
                self.ROIImage = cv2.imread(self.ROI, 0)

    def setParam(self, aParam, aParamType, aSection, aOption):
        param = None
        if self.parser.has_option(aSection, aOption):
            if aParamType == 'int':
                param = self.parser.getint(aSection, aOption)
            elif aParamType == 'float':
                param = self.parser.getfloat(aSection, aOption)
            elif aParamType == 'bool':
                param = self.parser.getboolean(aSection, aOption)
            elif aParamType == 'str':
                param = self.parser.get(aSection, aOption)
        if param is None:
            param = aParam

        return param

    def getDiff(self, aImage):

        # Copy the image to avoid modifying it
        self.imgK = np.ndarray.copy(aImage)
        #print 'in getDiff'
        # Convert it to greyscale if depth is 3
        dimension = self.imgK.shape
        if len(dimension) == 3:
            self.imgK = cv2.cvtColor(self.imgK, cv.CV_BGR2GRAY)

        # Get the difference image for imgK and imgKMin1
        if self.imgKMin1 is not None:
            self.diffK = cv2.absdiff(self.imgK, self.imgKMin1)
        else:
            self.diffK = cv2.absdiff(self.imgK, self.imgK)

        # Apply blur to smooth out small specks in the image
        self.diffK = cv2.GaussianBlur(self.diffK, self.gaussBlurSize,
                                      self.gaussBlurStdDev)

        # Apply adaptive threshold to mark blobs in the image
        # TODO(geir): Find out what the C constant should be, or if it should
        # be zero. Ask Fabio since he might know more about the specifics since
        # this is dealing with image processing.
        # Doc:
        # http://docs.opencv.org/modules/imgproc/doc/miscellaneous_transformations.html#adaptivethreshold
        # NOTE(geir): The C constant can NOT be zero. This causes a lot of
        # noise in the image, which we do not want.
        self.diffK = cv2.adaptiveThreshold(self.diffK, 255,
                                           self.adaptiveThresholdType,
                                           cv2.THRESH_BINARY_INV,
                                           self.adaptiveThresholdSize,
                                           self.adaptiveThresholdConstant)

        # Find the intersection of movement in current and previous difference
        # image to provide the movement in frame k-1
        if self.diffKMin1 is not None:
            self.motionKMin1 = cv2.bitwise_and(self.diffK, self.diffKMin1)
        else:
            self.motionKMin1 = cv2.bitwise_and(self.diffK, self.diffK)

        # Now we can find movement in frame k by subtracting diffk (movement in
        # k, k-1) from motionkMin1 (movement in frame k-1)
        self.motionK = cv2.absdiff(self.diffK, self.motionKMin1)

        # Now expand the areas of detected motion
        self.motionK = motion.dilateThenErode(self.motionK,
                                              self.dilateErodeKernelSize,
                                              self.dilateIterations,
                                              self.erodeIterations)

        # Update variables for next call to function
        self.imgKMin1 = self.imgK
        self.diffKMin1 = self.diffK

        #IR: Reset the previous images when a 
        #sequence of images is finished processing
        self.imageCount += 1
        if self.imageCount >= self.motionSequenceCount:
          self.resetPreviousDiff()
          self.imageCount = 0

        # Apply the ROI to exclude unwanted data
        self.motionK = self.applyROI(self.motionK)
        
        return self.motionK

    def applyROI(self, aImage):
        if(self.ROI is not None):          
          #self.ROIImage = cv2.cvtColor(self.ROIImage, cv.CV_BGR2GRAY)
          maskedImage = cv2.bitwise_and(aImage, self.ROIImage)
        else:
            maskedImage = aImage
        return maskedImage
    #find a way to put it in the diff func
    def resetPreviousDiff(self):
        #print 'deleting diffKMin1 ,imgKMin1'
        self.imgKMin1 = None  
        self.diffKMin1 = None

    def loadROIfromControl(self, aRoiDownsampled):
      self.ROIImage = aRoiDownsampled
    def loadBackgroundFromControl(self, aBackgroundImg):
        self.backgroundImg = aBackgroundImg


    
