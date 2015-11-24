
from ConfigParser import SafeConfigParser
import picamera
import os

class captureRefImage():

    def __init__(self, aConfigFilePath):
    
        self.refImage = None
        self.refImagePath = "./frameSetup/"
        
        if not os.path.exists(self.refImagePath):
            os.makedirs(self.refImagePath)
        
        self.resolutionX = 640
        self.resolutionY = 480
        
        self.parser = SafeConfigParser()
        self.setConfig(aConfigFilePath)
        
        self.resolution = (self.resolutionX, self.resolutionY)
        self.cam = picamera.PiCamera()
        self.cam.resolution = self.resolution
        
        
    def captureReferenceImage(self):
        fileName = "ROIReferenceImage.jpg"
        savePath = os.path.join(self.refImagePath, fileName)
        self.cam.capture(savePath)
        printStatement = "ROI reference image has been captured at resolution " + str(self.resolutionX) + "," + str(self.resolutionY) + ")"
        print(printStatement)
   
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
            print(aOption + " in " + aSection + " was not found. Using" +
                  " default value.")
            param = aParam

        return param   
   
    def setConfig(self, aConfig):

        if self.parser.read(aConfig):
            self.resolutionX = self.setParam(self.resolutionX,
                                             'int',
                                             'Controller',
                                             'resolutionX')
            self.resolutionY = self.setParam(self.resolutionY,
                                             'int',
                                             'Controller',
                                             'resolutionY')            

refImage = captureRefImage("sample.cfg")
refImage.captureReferenceImage()