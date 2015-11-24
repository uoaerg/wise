from ThreeBlur import ThreeBlur
from backSub import backSub
from DataWriter import DataWriter
from ConfigParser import SafeConfigParser
import Adafruit_DHT
import os
import glob
import ntpath
import picamera
import sensor
import time
import motion
import cv2
import numpy


class Controller():

    def __init__(self, aConfigFilePath, aDebugFlag=False):
        # Config parameters default values
        # Timelapse interval hours, minutes and seconds used to calculate the
        # interval in seconds
        self.timelapseIntervalH = 1.0
        self.timelapseIntervalM = 0.0
        self.timelapseIntervalS = 0.0
        # Number of images to take when motion is detected by the PIR
        self.motionSequenceCount = 5
        # Number of images that are used by a motion detection algorithm before
        # up-to-date results are indicated by the produced difference image
        self.motionSequencePreload = 2
        # Delay between each image taken when triggered by the PIR
        self.motionSequenceDelay = 1.0
        # Percentage difference image area that needs to be covered by a
        # minimum number of blobs in order to evaluate that motion is happening
        self.motionAreaPercent = 60
        self.motionMaxBlobs = 10
        # Where timelapse images are saved
        self.timelapseFilePath = "./timelapse/"
        # Where motion images/diffs are saved
        self.motionFilePath = "./motion/"
        # Where temporary files are put, for example to get the current
        # brightness in the scene
        self.tempFilePath = "./temp/"
        # Path where hourly and motion logs are placed
        self.logFilePath = "./logs/"
        # The name if the most recently captured timelaps image
        self.timelapseLatestImage = "timelapse.jpg"
        # Threshold (0-255) for the scene brightness when the IR led is
        # switched on
        self.brightnessThreshold = 25
        # Timeout (seconds) for when the brightness in the scene needs to be
        # re-evaluated
        self.brightnessTimeout = 60.0
        # The resolution of the camera
        self.originalResolutionX = 640
        self.originalResolutionY = 480
        self.resolutionX = self.originalResolutionX
        self.resolutionY = self.originalResolutionY
        # Flag to produce debug output to the terminal while running
        self.debug = aDebugFlag
        self.FOVMaxDistance = 20
        self.FOVMinAreaDetected = 1
        self.FOVVertical = 54
        self.FOVHorizontal = 41

        # Radu:  define the downsampling level
        self.downLevel = 0

        # T Morton: adds a path to a folder for the image processing queue
        self.queuePath = "./queue/"
        if not self._directoryExists(self.queuePath):
            self._createDirectory(self.queuePath)

        # Load config file parameters to override the default values
        self.parser = SafeConfigParser()
        self.setConfig(aConfigFilePath)

        # Paths setup, create the paths if they do not exist
        if not self._directoryExists(self.tempFilePath):
            self._createDirectory(self.tempFilePath)
        if not self._directoryExists(self.motionFilePath):
            self._createDirectory(self.motionFilePath)
        if not self._directoryExists(self.logFilePath):
            self._createDirectory(self.logFilePath)
        if not self._directoryExists(self.timelapseFilePath):
            self._createDirectory(self.timelapseFilePath)

        # Timelapse setup
        self.timelapseInterval = (self.timelapseIntervalH * 60.0 * 60.0 +
                                  self.timelapseIntervalM * 60.0 +
                                  self.timelapseIntervalS)
        self.timelapseLastTime = 0.0

        # background refresh setup
        self.firstImage = True
        self.backgroundRefreshDelay = False
        self.backgroundRefreshDelayTime = 60 * 10
        self.previousTime = 0.0
        self.delayCount = 0
        self.delayCountMax = 2

        # Brightness measurements setup
        self.brightnessLastTime = 0.0
        self.brightness = 0

        # Inputs/outputs
        sensor.initGPIO()
        self.PIR = sensor.PIR(sensor.PIR_PIN, sensor.GPIO.PUD_DOWN)

        # T Morton: queue implementation

        self.processingImage = False
        self.imgSetsInQ = 0
        self.queueIndex = 0
        self.currentImageSetToProcess = 0
        self.numberOfImgSetsProcessed = 0
        self.PIR.enableInterrupt(self._takeImageCallbackPIR)
        self.PIRCount = 0
        self.previousTimeForImg = 0
        self.timeToWait = 10

        self.PIRLastCount = 0
        self.DHTType = Adafruit_DHT.DHT22
        self.DHTPin = 23

        # Camera setup
        
        self.resolution = (self.resolutionX, self.resolutionY)
        self.cam = picamera.PiCamera()
        self.cam.resolution = self.resolution
        # TODO(geir): Create a function to switch off camera LED in sensor.py
        sensor.GPIO.output(sensor.CAM_LED, False)

        #if (self.downLevel > 0):
            #self.resolutionX = self.resolutionX / (2 ** self.downLevel )
            #self.resolutionY = self.resolutionY / (2 ** self.downLevel)
        
        # Difference image area that is considered too small to evaluate the
        # movement in the scene as true
        self.motionMinArea = \
            motion.getCutoffObjectArea(self.resolutionX * self.resolutionY,
                                       self.FOVMinAreaDetected,
                                       self.FOVVertical,
                                       self.FOVHorizontal,
                                       self.FOVMaxDistance)
        self.defaultMotionMinArea = self.motionMinArea
        # TODO(geir): Consider wrapping the below in a helper function to
        # reduce init clutter
        # Data logging setup
        hourlyDataDescription = ["AliveCount",
                                 "Timestamp",
                                 "Brightness",
                                 "ExternalTemp",
                                 "Humidity"]
        hourlyDataFilePath = os.path.join(self.logFilePath, "hourlydata.csv")
        self.hourlyDataRecorder = DataWriter(hourlyDataFilePath,
                                             hourlyDataDescription)
        self.hourlyLastTime = 0.0
        self.hourlyAliveCount = 1
        motionDataDescription = ["AliveCount",
                                 "Timestamp",
                                 "ImageName",
                                 "Brightness",
                                 "Threshold",  # Do we need this?
                                 "PIRCount",
                                 "BlobCount",
                                 "MaxBlobSize",
                                 "Verdict"]
        motionDataFilePath = os.path.join(self.logFilePath, "motiondata.csv")
        self.motionDataRecorder = DataWriter(motionDataFilePath,
                                             motionDataDescription)
        self.motionAliveCount = 1

        #ROI image downsampling 
        if self.downLevel > 0:
            self.ROIdownsampling('ROI.jpg', self.downLevel) 

        # Image processor(s)
        self.processor = ThreeBlur()
        #self.processor = backSub()
        self.processor.setConfig(aConfigFilePath)

        

        # TODO(geir): Arrange for a system that can use multiple algorithms
        """
        self.processors = list()
        threeblur = ThreeBlur()
        threeblur.setConfig(aConfig)
        self.processors.append(threeblur)
        """

    def run(self):
        while True:
            if self._timeForTimelapse():
                self._doTimelapse()
                self._doBackgroundRefresh()
            if self.backgroundRefreshDelay == True:
                self._tryBackgroundRefreshAgain()
            if self._timeForHourlyData():
                self._doHourlyData()
            if self._PIRActivated():
                self._saveMotionWhenNotProcessing()
            self._processImagesFromQ()
        # NOTE(geir): Should set up schedulers instead of the above.
        # Look in to thread locking, mutex, atomic code segments, schedulers.
        # The locking is required since the activities share resources (mainly
        # the camera but also member variables such as self.brightness etc...)

        # Sleeping for a bit in order to consume all available CPU cycles
        time.sleep(1)

    def _timeForTimelapse(self):
        currentTime = time.time()
        if (currentTime - self.timelapseLastTime) > self.timelapseInterval:
            self.timelapseLastTime = currentTime
            return True
        else:
            return False

    def _doTimelapse(self):

        if self.debug:
            print("Performing timelapse")

        fileName = time.strftime("%Y%m%d-%H%M%S.jpg")
        savePath = os.path.join(self.timelapseFilePath, fileName)
        # tempFilePath = os.path.join(self.tempFilePath,
        #                            self.timelapseLatestImage)
        if self._getCurrentBrightness() < self.brightnessThreshold:
            sensor.activateIRLED()
        self.cam.capture(savePath)
        # TODO(geir): Evaluate if we should apply a visual indication of the
        # current ROI in the image before saving it?

        # Ensure LED is off
        sensor.deactivateIRLED()

    # T Morton
    # IR: changed to allow downsampling 30/07/15
    def _doBackgroundRefresh(self):
        tempFilePath = os.path.join(self.tempFilePath,
                                    self.timelapseLatestImage)
        if self._getCurrentBrightness() < self.brightnessThreshold:
            sensor.activateIRLED() 
        if (self.firstImage == False):
            if(self.PIRCount == 0):
                self.cam.capture(tempFilePath)
                if self.downLevel > 0:
                    img = cv2.imread(tempFilePath)
                    downsampledBackground = self.imageDownsampling(img, self.downLevel)
                    cv2.imwrite(tempFilePath,downsampledBackground)
                self.backgroundRefreshDelay = False
            else:
                self.backgroundRefreshDelay = True
        else:
            self.cam.capture(tempFilePath)
            if self.downLevel > 0:
                    img = cv2.imread(tempFilePath)
                    downsampledBackground = self.imageDownsampling(img, self.downLevel)
                    cv2.imwrite(tempFilePath,downsampledBackground)
            
            self.firstImage == False
        #IR: restore the resolution global variables
        if ((self.resolutionX != self.originalResolutionX) or (self.resolutionY != self.originalResolutionY)):
            self.resolutionX = self.originalResolutionX
            self.resolutionY = self.originalResolutionY
        self.motionMinArea = self.defaultMotionMinArea

    # T Morton
    # IR: changed to allow downsampling 30/07/15
    def _tryBackgroundRefreshAgain(self):
        currentTime = time.time()
        if (currentTime - self.previousTime) > self.backgroundRefreshDelayTime:
            self.previousTime = currentTime
            if self.delayCount <= self.delayCountMax:
                if(self.PIRCount == 0):
                    self.cam.capture(tempFilePath)
                    if self.downLevel > 0:
                        img = cv2.imread(tempFilePath)
                        downsampledBackground = self.imageDownsampling(img, self.downLevel)
                        cv2.imwrite(tempFilePath,downsampledBackground)
                    self.backgroundRefreshDelay = False
                    self.delayCount = 0
                else:
                    self.backgroundRefreshDelay = True
                    self.delayCount += 1
            else:
                self.backgroundRefreshDelay = False
                self.delayCount = 0
        #IR: restore the resolution global variables
        if ((self.resolutionX != self.originalResolutionX) or (self.resolutionY != self.originalResolutionY)):
            self.resolutionX = self.originalResolutionX
            self.resolutionY= self.originalResolutionY

    def _timeForHourlyData(self):
        currentTime = time.time()
        if (currentTime - self.hourlyLastTime) > 3600.0:
            self.hourlyLastTime = currentTime
            return True
        else:
            return False

    def _doHourlyData(self):
        if self.debug:
            print("Performing hourly data")
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        brightness = self._getCurrentBrightness()
        DHTData = Adafruit_DHT.read_retry(self.DHTType, self.DHTPin)
        humidity = round(DHTData[0], 2)
        temperature = round(DHTData[1], 2)
        dataList = [self.hourlyAliveCount, timestamp, brightness, temperature,
                    humidity]
        self.hourlyDataRecorder.writeData(dataList)
        self.hourlyAliveCount += 1
        if self.debug:
            print("Got hourly data: ")
            print(dataList)

    # T Morton
    def _PIRActivated(self):
        if self.PIRCount > 0:
            if self.debug:
                print("PIR Triggered")
            self.PIRCount = 0
            return True
        else:
            return False

    def _saveMotionWhenNotProcessing(self):
        if self.processingImage == False:
            if self.debug:
                print("    No current image processing")            
            currentTime = time.time()
            if (currentTime - self.previousTimeForImg) > self.timeToWait:
                self.previousTimeForImg = currentTime
                if self.debug:
                    print("    Saving image sequence to queue")
                self._saveImageSequenceToQ(self.motionSequenceCount, self.motionSequenceDelay)
        else:
            if self.debug:
                print("    Images are being processed")

    # T Morton
    # Interrupt function: counts PIR activations
    # Records an image set periodically if PIR is activated
    def _takeImageCallbackPIR(self, channel):
        self.PIRCount = self.PIRCount + 1
        if self.processingImage == True:
            currentTime = time.time()
            if (currentTime - self.previousTimeForImg) > self.timeToWait:
                self.previousTimeForImg = currentTime
                if self.debug:
                    print("Saving image sequence to queue")
                self._saveImageSequenceToQ(
                    self.motionSequenceCount, self.motionSequenceDelay)

    def _getQueueFilename(self, aQueueIndex):
        if aQueueIndex < 10:
           rQueueIndex = '00' + str(aQueueIndex) 
        elif aQueueIndex > 9 & aQueueIndex < 100:
           rQueueIndex = '0' + str(aQueueIndex)
        
        return rQueueIndex   
                    
    # T Morton
    def _saveImageSequenceToQ(self, aCount, aDeltaTime):
        if self._getCurrentBrightness() < self.brightnessThreshold:
            sensor.activateIRLED() 
        queueFilename = self._getQueueFilename(self.queueIndex)
        captureCount = 0
        while(captureCount < aCount):
            imgPath = self.queuePath + queueFilename + \
                "_" + str(captureCount) + ".jpg"
            self.cam.capture(imgPath)
            captureCount += 1
            time.sleep(aDeltaTime)
        # Increments the index used for filename convention
        self.queueIndex += 1
        # Increments the actual number of image sets in the queue
        self.imgSetsInQ += 1
        sensor.deactivateIRLED()

    # T Morton load a specific image sequence
    # does not check if the sequence exists
    def _loadImageSequenceFromQ(self, aImgSequence):
        imgList = list()
        queueFilename = self._getQueueFilename(aImgSequence)
        sequence = queueFilename + '_?'
        for filename in glob.glob(self.queuePath + sequence + "*.jpg"):
            PathAndFile = os.path.splitext(filename)[0]
            latestFilename = ntpath.basename(PathAndFile)
            # for threebluur resolution
            self.resolutionX = self.originalResolutionX
            self.resolutionY = self.originalResolutionY
            img =self.imageDownsampling (cv2.imread(
                self.queuePath + latestFilename + ".jpg", cv2.CV_LOAD_IMAGE_COLOR), self.downLevel)
            imgList.append(img)
        return imgList

    # T Morton
    def _processImagesFromQ(self):
        if self.imgSetsInQ > 0:
            if(self.numberOfImgSetsProcessed < self.imgSetsInQ):
                self.processingImage = True
                self._doMotionDetectionFromQ(self.currentImageSetToProcess)
                #self._deleteProcessedImgsFromQ(self.currentImageSetToProcess)
                self.currentImageSetToProcess += 1
            else:
                self.processingImage = False
    
    def _deleteProcessedImgsFromQ(self, aImgSequence):
        queueFilename = self._getQueueFilename(aImgSequence)
        filenameSearch = queueFilename + '_?'
        for filename in glob.glob(self.queuePath + filenameSearch + ".jpg"):
            cmd = 'sudo rm ' + filename
            os.system(cmd)
        self.imgSetsInQ -= 1
            
    # T Morton
    # Loads an image set and processes it
    #IR: changed to perform downsampling
    def _doMotionDetectionFromQ(self, aImageSet):

        if self.debug:
            print("Performing motion detection")

        imgList = self._loadImageSequenceFromQ(aImageSet)
        diffList = self._getDiffSequence(imgList)

        if self.motionSequencePreload <= 0:
            startIndex = 0
        else:
            startIndex = self.motionSequencePreload - 1
            largestAreaIndex = None
            largestAreaBlobs = None
            largestAreaBlobCount = None
            largestArea = -1.0
            for diffIndex in xrange(startIndex, self.motionSequenceCount):
                blobData = motion.getBlobs(diffList[diffIndex])
                blobs = blobData[0]
                num_blobs = blobData[1]
                blobAreaList = motion.getBlobAreaList(blobs, num_blobs)
                largestBlobArea = motion.getMaxAreaFromBlobs(blobAreaList)
                if largestBlobArea > largestArea:
                    largestArea = largestBlobArea
                    largestAreaIndex = diffIndex
                    largestAreaBlobs = blobs
                    largestAreaBlobCount = num_blobs

        aliveCount = self.motionAliveCount
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        brightness = self._getCurrentBrightness()
        threshold = 0  # TODO(geir): Need it
        PIRCount = self.PIRLastCount
        blobCount = largestAreaBlobCount
        maxBlobSize = largestBlobArea
        verdict = motion.evalMotionPropotionalBlobArea(largestAreaBlobs,
                                                       largestAreaBlobCount,
                                                       self.motionAreaPercent,
                                                       self.motionMaxBlobs,
                                                       self.motionMinArea
        # Save statistics in CSV)
        dataList = [aliveCount, timestamp, brightness, threshold, PIRCount, blobCount, maxBlobSize, verdict]
        self.motionDataRecorder.writeData(dataList)
        imageName = timestamp + ".jpg"
        diffName = timestamp + "-" + str(verdict) + "-diff.jpg"
        imagePath = os.path.join(self.motionFilePath, imageName)
        diffPath = os.path.join(self.motionFilePath, diffName)
        cv2.imwrite(imagePath, imgList[largestAreaIndex])
        cv2.imwrite(diffPath, diffList[largestAreaIndex])
        self.motionAliveCount += 1
        if self.debug:
            print("Got motion data: ")
            print(dataList)

        # TM: Keeps track of the number of image sets that have been processed
        self.numberOfImgSetsProcessed += 1

        if ((self.resolutionX != self.originalResolutionX) or (self.resolutionY != self.originalResolutionY)):
            self.resolutionX = self.originalResolutionX
            self.resolutionY= self.originalResolutionY
        self.motionMinArea = self.defaultMotionMinArea

    def _getCurrentBrightness(self):
        currentTime = time.time()
        if (currentTime - self.brightnessLastTime) > self.brightnessTimeout:
            self.brightnessLastTime = currentTime
            imagePath = os.path.join(self.tempFilePath, "brightness.jpg")
            self.cam.capture(imagePath)
            image = cv2.imread(imagePath, 0)
            brightness = motion.getBrightness(image)
            self.brightness = round(brightness[0], 2)
        #if self.debug:
        #    print("Got brightness: " + str(self.brightness))
        return self.brightness

    def _getDiffSequence(self, aImgList):
        diffList = list()
        for image in aImgList:
            diff = self.processor.getDiff(image)
            diffList.append(diff)
        return diffList

    def _directoryExists(self, aDirectory):
        return os.path.exists(aDirectory)

    def _createDirectory(self, aDirectory):
        os.makedirs(aDirectory)

    def setConfig(self, aConfig):

        if self.parser.read(aConfig):
            # General variables
            self.timelapseFilePath = self.setParam(self.timelapseFilePath,
                                                   'str',
                                                   'General',
                                                   'timelapseFilePath')
            self.motionFilePath = self.setParam(self.motionFilePath,
                                                'str',
                                                'General',
                                                'motionFilePath')

            self.tempFilePath = self.setParam(self.tempFilePath,
                                              'str',
                                              'General',
                                              'tempFilePath')

            self.logFilePath = self.setParam(self.logFilePath,
                                             'str',
                                             'General',
                                             'logFilePath')
            self.timelapseLatestImage = self.setParam(self.logFilePath,
                                                      'str',
                                                      'General',
                                                      'timelapseLatestImage')

            # Controller variables
            self.timelapseIntervalH = self.setParam(self.timelapseIntervalH,
                                                    'float',
                                                    'Controller',
                                                    'timelapseIntervalH')
            self.timelapseIntervalM = self.setParam(self.timelapseIntervalM,
                                                    'float',
                                                    'Controller',
                                                    'timelapseIntervalM')
            self.timelapseIntervalS = self.setParam(self.timelapseIntervalS,
                                                    'float',
                                                    'Controller',
                                                    'timelapseIntervalS')
            self.motionSequenceCount = self.setParam(self.motionSequenceCount,
                                                     'int',
                                                     'Controller',
                                                     'motionSequenceCount')
            self.motionSequencePreload = \
                self.setParam(self.motionSequencePreload,
                              'int',
                              'Controller',
                              'motionSequencePreload')
            self.motionSequenceDelay = self.setParam(self.motionSequenceDelay,
                                                     'float',
                                                     'Controller',
                                                     'motionSequenceDelay')

            self.motionAreaPercent = self.setParam(self.motionAreaPercent,
                                                   'int',
                                                   'Controller',
                                                   'motionAreaPercent')
            self.motionMaxBlobs = self.setParam(self.motionMaxBlobs,
                                                'int',
                                                'Controller',
                                                'motionMaxBlobs')

            self.brightnessThreshold = self.setParam(self.brightnessThreshold,
                                                     'int',
                                                     'Controller',
                                                     'brightnessThreshold')
            self.brightnessTimeout = self.setParam(self.brightnessTimeout,
                                                   'float',
                                                   'Controller',
                                                   'brightnessTimeout')
            self.resolutionX = self.setParam(self.resolutionX,
                                             'int',
                                             'Controller',
                                             'resolutionX')
            self.resolutionY = self.setParam(self.resolutionY,
                                             'int',
                                             'Controller',
                                             'resolutionY')
            self.FOVMaxDistance = self.setParam(self.FOVMaxDistance,
                                                'int',
                                                'Controller',
                                                'FOVMaxDistance')
            self.FOVMinAreaDetected = self.setParam(self.FOVMinAreaDetected,
                                                    'int',
                                                    'Controller',
                                                    'FOVMinAreaDetected')
            self.FOVVertical = self.setParam(self.FOVVertical,
                                             'int',
                                             'Controller',
                                             'FOVVertical')
            self.FOVHorizontal = self.setParam(self.FOVHorizontal,
                                               'int',
                                               'Controller',
                                               'FOVHorizontal')
            self.downLevel = self.setParam(self.downLevel, 
                                            'int',
                                            'Controller',
                                            'downLevel')
            self.debug = self.setParam(self.debug,
                                       'bool',
                                       'Controller',
                                       'debug')


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

    #IR: downsampling function    
    def imageDownsampling(self, aImage, aDownLevel):
        # aImage= the input array image
        #downLevel = how many levels of sampling 
        #perform the downsampling 
        tempImg = aImage
        for n in range(aDownLevel):
            imgDownsampled = cv2.pyrDown(tempImg)
            print 'downsampling'
            tempImg = imgDownsampled

        #change the global resolution parameters of the image
        if (aDownLevel > 0):
            self.resolutionX = self.resolutionX / (2 ** aDownLevel )
            self.resolutionY = self.resolutionY / (2 ** aDownLevel) 
            #recalculate the motion min area with the new resolution
            self.motionMinArea = \
                motion.getCutoffObjectArea(self.resolutionX * self.resolutionY,
                                       self.FOVMinAreaDetected,
                                       self.FOVVertical,
                                       self.FOVHorizontal,
                                       self.FOVMaxDistance)
        print self.resolutionX, self.resolutionY
        return tempImg

    # IR: ROI downsampling function // 31/07/15
    # use this function in the constructor
    def ROIdownsampling(self, aROIimageName, aDownLevel):
        #read the ROI image to an array
        #perform downsampling on the image
        #save the ROI image downsampled 

        ROIimg = cv2.imread(aROIimageName,cv2.CV_LOAD_IMAGE_COLOR)

        tempImg =  ROIimg
        for n in range(aDownLevel):
            downsampledROI = cv2.pyrDown(tempImg)
            tempImg = downsampledROI
        print 'ROI downsampling'

        #remove the blur regions between from the ROI downsampled
        #image

        retval, dst = cv2.threshold(tempImg, 127, 255, cv2.THRESH_BINARY) 
        #save the image to file 
        cv2.imwrite(aROIimageName,dst)


