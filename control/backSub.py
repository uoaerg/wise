import os
import motion
import cv2
from ConfigParser import SafeConfigParser
import cv2.cv as cv


class backSub():

    def __init__(self):

        self.ROI = None
        self.splitColours = False
        self.kernelSize = 20
        self.history = 0
        self.gausMix = 5
        self.backRatio = 0.7
        self.noise = 1.5

        self.backgroundSubtractor = list()
        self.parser = SafeConfigParser()

        self.path = None
        self.imgName = None
        self.imageROI = None
        self.backgroundImg = None

    def setConfig(self, aConfig):

        if self.parser.read(aConfig):
            self.ROI = self.setParam(self.ROI, 'str', 'General', 'ROI')

            self.path = self.parser.get('General', 'tempFilePath')
            self.imgName = self.parser.get('General', 'timelapseLatestImage')

            self.splitColours = self.setParam(self.splitColours, 'bool',
                                              'backSub', 'splitColours')
            self.kernelSize = self.setParam(self.kernelSize, 'int', 'backSub',
                                            'kernelSize')
            self.history = self.setParam(self.history, 'int', 'backSub',
                                         'history')
            self.gausMix = self.setParam(self.gausMix, 'int', 'backSub',
                                         'gausMix')
            self.backRatio = self.setParam(self.backRatio, 'float', 'backSub',
                                           'backRatio')
            self.noise = self.setParam(self.noise, 'float', 'backSub', 'noise')

            if(self.ROI is not None):
                self.imageROI = cv2.imread("ROI.jpg", 0)

            self.backgroundImg = cv2.imread(
                os.path.join(self.path, self.imgName), cv2.CV_LOAD_IMAGE_COLOR)


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

        #backgroundImg = cv2.imread(
            #os.path.join(self.path, self.imgName), cv2.CV_LOAD_IMAGE_COLOR)

        #maskedBackground = self.applyROI(backgroundImg)
        #maskImg = self.applyROI(aImage)
        imgList = list()
        if self.splitColours is True:
            #imgList = self.convertColorSpaceAndSplt(maskedBackground)
            imgList = self.convertColorSpaceAndSplt(self.backgroundImg)
            diffList = self.getDiffImageList(imgList)
            #imgList = self.convertColorSpaceAndSplt(maskImg)
            imgList = self.convertColorSpaceAndSplt(aImage)
            diffList = self.getDiffImageList(imgList)
        else:
            #imgList = [maskedBackground]
            imgList = [self.backgroundImg]
            diffList = self.getDiffImageList(imgList)
            #imgList = [maskImg]
            imgList = [aImage]
            diffList = self.getDiffImageList(imgList)

        diffImg = self.combineDiffImageList(diffList)
        self.refreshBackSub()
        diffImg = self.applyROI(diffImg)
        return diffImg
    
    def applyROI(self, aImage):
        if(self.ROI is not None):
            maskedImage = cv2.bitwise_and(aImage, self.imageROI)
        else:
            maskedImage = aImage
        return maskedImage

    def convertColorSpaceAndSplt(self, aImage):

        #image = cv2.cvtColor(image, cv2.COLOR_BGR2YCR_CB)
        #image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        imageList = list()
        imageList.append(cv2.split(aImage)[0])
        imageList.append(cv2.split(aImage)[1])
        imageList.append(cv2.split(aImage)[2])

        return imageList

    def getDiffImageList(self, aImageList):

        listLength = len(aImageList)

        while(len(self.backgroundSubtractor) != listLength):
            self.backgroundSubtractor.append(cv2.BackgroundSubtractorMOG())

        diffImageList = list()
        for index in range(listLength):
            foregroundMask = \
                self.backgroundSubtractor[index].apply(aImageList[index],
                                                       learningRate=0.0001)
            diffImageList.append(motion.closeImage(foregroundMask,
                                                   self.kernelSize))

        return diffImageList

    def combineDiffImageList(self, aDiffImgList):
        diffImage = reduce(cv2.bitwise_or, aDiffImgList)
        return diffImage

    def refreshBackSub(self):
        emptyList = list()
        self.backgroundSubtractor = emptyList

    def loadROIfromControl(self, aRoiDownsampled):
        self.imageROI = aRoiDownsampled

    def loadBackgroundFromControl(self, aBackgroundImg):
        self.backgroundImg = aBackgroundImg


    




