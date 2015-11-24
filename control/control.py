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
import serial
from smssend import TextMessage
#import smsrecv


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
        self.motionSequenceDelay = 2.0
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
        # TM: path to the queue folder
        self.queuePath = "./queue/"
        # The name if the most recently captured timelaps image
        self.timelapseLatestImage = "timelapse.jpg"
        #IR: Folder to save the true sequences
        self.miniSequencePath = "./miniSequence/"
        # Threshold (0-255) for the scene brightness when the IR led is
        # switched on
        self.brightnessThreshold = 25
        # Timeout (seconds) for when the brightness in the scene needs to be
        # re-evaluated
        self.brightnessTimeout = 60.0
        # The resolution of the camera
        self.resolutionX = 640
        self.resolutionY = 480
        # Flag to produce debug output to the terminal while running
        self.debug = aDebugFlag
        self.FOVMaxDistance = 20
        self.FOVMinAreaDetected = 1
        self.FOVVertical = 54
        self.FOVHorizontal = 41
        # IR: Defines downsampling level
        self.downLevel = 0
        # TM: ROI
        self.ROI = None
        #TM: enable/disable SMS feature
        self.sendSMS = False
        # TM: SMS recipient
        self.textMessageRecipient = None

        # TM: queue implementation
        self.processingImage = False
        self.imgSetsInQ = 0
        self.queueIndex = 0
        self.currentImageSetToProcess = 0
        self.numberOfImgSetsProcessed = 0
        self.lastBackgroundRefrestTime = 0
        self.backgroundRefreshWaitTime = 60.0 #60.0 * 5
        self.previousMotionImgTime = 0
        self.timeToWaitForNextMotionImg = 10.0
        self._savingImageSequence = False
        
        self.sequenceTimeStampList = list()
        self.imageBrightnessList = list()
        self.PIRLastCountList = list()
        

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
        # TM; queue folder
        if not self._directoryExists(self.queuePath):
            self._createDirectory(self.queuePath)
        # IR: true sequence folder
        if not self._directoryExists(self.miniSequencePath):
            self._createDirectory(self.miniSequencePath)

        # Timelapse setup
        self.timelapseInterval = (self.timelapseIntervalH * 60.0 * 60.0 +
                                  self.timelapseIntervalM * 60.0 +
                                  self.timelapseIntervalS)
        self.timelapseLastTime = 0.0

        # Brightness measurements setup
        self.brightnessLastTime = 0.0
        self.brightness = 0

        # Inputs/outputs
        sensor.initGPIO()
        self.PIR = sensor.PIR(sensor.PIR_PIN, sensor.GPIO.PUD_DOWN)
        self.PIRLastCount = 0
        self.DHTType = Adafruit_DHT.DHT22
        self.DHTPin = 23
        #TM: Queue implementation
        self.PIR.enableInterrupt(self._takeImageCallbackPIR)
        self.PIRTriggered = False
        self.enableCallbackPIR = False 

        # Camera setup
        self.resolution = (self.resolutionX, self.resolutionY)
        self.cam = picamera.PiCamera()
        self.cam.resolution = self.resolution
        # TODO(geir): Create a function to switch off camera LED in sensor.py
        sensor.GPIO.output(sensor.CAM_LED, False)

        # Difference image area that is considered too small to evaluate the
        # movement in the scene as true
        self.motionMinArea = \
            motion.getCutoffObjectArea(self.resolutionX * self.resolutionY,
                                       self.FOVMinAreaDetected,
                                       self.FOVVertical,
                                       self.FOVHorizontal,
                                       self.FOVMaxDistance)

        # IR: downsampling
        self.originalResolutionX = self.resolutionX
        self.originalResolutionY = self.resolutionY
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

        # TMorton
        # Added processing time data
        self.processingEndTime = 0
        self.processingStartTime = 0
        motionDataDescription = ["AliveCount",
                                 "Timestamp",
                                 "Brightness",
                                 "Threshold",  # Do we need this?
                                 "BlobCount",
                                 "MaxBlobSize",
                                 "Verdict",
                                 "ProcessingTime"]
        motionDataFilePath = os.path.join(self.logFilePath, "motiondata.csv")
        self.motionDataRecorder = DataWriter(motionDataFilePath,
                                             motionDataDescription)
        self.motionAliveCount = 1
           
        # Image processor(s)
        self.processor = ThreeBlur()
        self.strProcessor = "ThreeBlur"
        #self.processor = backSub()
        #self.strProcessor = "backSub"
        self.processor.setConfig(aConfigFilePath)
        # do this if backSub
        self._doBackgroundRefresh()
        #Overwrites the ROI image from the processor object
        #if the ROI is downsampled (if the ROI is used)
        self.downSampleROI('ROI.jpg', self.downLevel) 
        
        #Send starting SMS
        if self.textMessageRecipient is not None:
            self.sms = TextMessage()
            self.trueMotionCount = 0
            self.lastTextMessageSendTime = time.time()

            self.sms.connectPhone()
            self.sms.setRecipient(str(self.textMessageRecipient))
            self.sms.setContent("FoxBox On")
            self.sms.sendMessage()
            self.sms.disconnectPhone()

    def run(self):
        self.enableCallbackPIR = True
        while True: 
            if self.textMessageRecipient is not None:
                self._sendTextMessage()
                
            if self._timeForTimelapse():
                self.enableCallbackPIR = False
                while self._savingImageSequence == True:
                    pass
                self._doTimelapse()
                self.enableCallbackPIR = True
            
            if self._timeForHourlyData():
                self.enableCallbackPIR = False
                while self._savingImageSequence == True:
                    pass 
                self._doHourlyData()
                self.enableCallbackPIR = True
            
            if self.PIRTriggered == False:
                self.enableCallbackPIR = False
                while self._savingImageSequence == True:
                    pass
                self._doBackgroundRefresh()
                self.enableCallbackPIR = True
      
            self._processImagesFromQ()
               
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
    def _doBackgroundRefresh(self):
        if self.strProcessor == "backSub":
            tempFilePath = os.path.join(self.tempFilePath,
                                        self.timelapseLatestImage)
            backgroundCurrentTime = time.time()
            if (backgroundCurrentTime - self.lastBackgroundRefrestTime) > self.backgroundRefreshWaitTime:
                self.lastBackgroundRefrestTime = backgroundCurrentTime
                if self.debug:
                    print("Refreshing background")
                if self._getCurrentBrightness() < self.brightnessThreshold:
                    sensor.activateIRLED()
                self.cam.capture(tempFilePath)

                # IR: Downsample background image
                self.backgroundDownSample(self.downLevel)

                sensor.deactivateIRLED()

            # IR: Reset variables to defaults
            self.resolutionX = self.originalResolutionX
            self.resolutionY = self.originalResolutionY
            self.motionMinArea = self.defaultMotionMinArea

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
        #DHTData = Adafruit_DHT.read(self.DHTType, self.DHTPin)

        if DHTData[0] is None:
            print "Humidity is None"
            humidity = 0
        else:
            humidity = round(DHTData[0], 2)
        if DHTData[1] is None:
            print "temperature is None"
            temperature = 0
        else:
            temperature = round(DHTData[1], 2)

        dataList = [self.hourlyAliveCount, timestamp, brightness, temperature,
                    humidity]
        self.hourlyDataRecorder.writeData(dataList)
        self.hourlyAliveCount += 1
        if self.debug:
            print("Got hourly data: ")
            print(dataList)
    
    # T Morton: SMS
    def _sendTextMessage(self):
    
        currentTime = time.time()
        if (currentTime - self.lastTextMessageSendTime) > (60*30):
            self.lastTextMessageSendTime = currentTime
            self.sms.connectPhone()
            self.sms.setRecipient(str(self.textMessageRecipient))
            self.sms.setContent("FoxBox Hourly Motion Report. Number of True Detections: " + str(self.trueMotionCount))
            self.sms.sendMessage()
            self.sms.disconnectPhone()
            print "message sent successfully"
            self.trueMotionCount = 0
    
    def _takeImageCallbackPIR(self, channel):
        #print("Interrupt Triggered")
        self.PIRTriggered = True
        if self.enableCallbackPIR == True:
            currentTime = time.time()
            if (currentTime - self.previousMotionImgTime) > self.timeToWaitForNextMotionImg:
                self.previousMotionImgTime = currentTime
                print("Saving image sequence to queue")
                self._saveImageSequenceToQ(
                    self.motionSequenceCount, self.motionSequenceDelay)
                    
        self.PIRTriggered = False

    
    def _getQueueFilename(self, aQueueIndex):
        if aQueueIndex < 10:
            rQueueIndex = '000' + str(aQueueIndex)
        elif aQueueIndex > 9 & aQueueIndex < 100:
            rQueueIndex = '00' + str(aQueueIndex)
        elif aQueueIndex > 99 & aQueueIndex < 1000:
            rQueueIndex = '0' + strre(aQueueIndex)

        return rQueueIndex

    def _saveImageSequenceToQ(self, aCount, aDeltaTime):
        
        #TM: Boolean indicates that images are being saved (used by run loop)
        self._savingImageSequence = True
        
        if self._getCurrentBrightness() < self.brightnessThreshold:
            sensor.activateIRLED()
        queueFilename = self._getQueueFilename(self.queueIndex)
        captureCount = 0
        sequenceTimeStamp = time.strftime("%Y%m%d-%H%M%S")   
        while(captureCount < aCount):
            imgPath = self.queuePath + queueFilename + \
                "_" + str(captureCount) + ".jpg"
            pictureCurrentTime = time.time()
            self.cam.capture(imgPath)
            afterPictureCurrentTime = time.time() 
            PictureDeltaTime=afterPictureCurrentTime-pictureCurrentTime
            #print PictureDeltaTime
            if(PictureDeltaTime<aDeltaTime):
                time.sleep(aDeltaTime-PictureDeltaTime)
            captureCount += 1
        #TM: records time image taken   
        self.sequenceTimeStampList.append(sequenceTimeStamp)
        
        #TM: records brightness at time image taken
        imageBrightness = self._getCurrentBrightness()
        self.imageBrightnessList.append(imageBrightness)
    
        # Increments the index used for filename convention
        ##CircularQ
        if self.queueIndex < 999:
            self.queueIndex += 1
        else:
            self.queueIndex = 0
        # Increments the actual number of image sets in the queue
        self.imgSetsInQ += 1
        sensor.deactivateIRLED()
        
        self._savingImageSequence = False
    
    def _loadImageSequenceFromQ(self, aImgSequence):
        imgList = list()
        
        #IR: Saving the full size images
        fullSizeImgList = list()
        
        queueFilename = self._getQueueFilename(aImgSequence)
        sequence = queueFilename + '_?'
        for filename in sorted(glob.glob(self.queuePath + sequence + "*.jpg")):
            PathAndFile = os.path.splitext(filename)[0]
            latestFilename = ntpath.basename(PathAndFile)

            # IR: Downsample images and append to list
            self.resolutionX = self.originalResolutionX
            self.resolutionY = self.originalResolutionY
            
            img = cv2.imread(
                self.queuePath + latestFilename + ".jpg", cv2.CV_LOAD_IMAGE_COLOR)
            
            #IR:  Saving the full size images
            fullSizeImgList.append(img)                
            
            if(self.downLevel > 0):
                img = self.imageDownsampling(img, self.downLevel)

            imgList.append(img)

        #IR: Return both the full size and downsampled lists
        return imgList, fullSizeImgList

    def _processImagesFromQ(self):
        if self.imgSetsInQ > 0:
            self.processingImage = True
            self._doMotionDetectionFromQ(self.currentImageSetToProcess)
            self.processingImage = False
            self._deleteProcessedImgsFromQ(self.currentImageSetToProcess)
            
            ##CircularQ
            if self.currentImageSetToProcess < 999:
                self.currentImageSetToProcess += 1
            else:
                self.currentImageSetToProcess = 0
            ##
        elif os.listdir(self.queuePath) == []:
            self.queueIndex = 0
            self.currentImageSetToProcess = 0
            self.sequenceTimeStampList = list()
            self.imageBrightnessList = list()
            self.PIRLastCountList = list()

    def _deleteProcessedImgsFromQ(self, aImgSequence):
        queueFilename = self._getQueueFilename(aImgSequence)
        filenameSearch = queueFilename + '_?'
        for filename in glob.glob(self.queuePath + filenameSearch + ".jpg"):
            # Calling os.system breaks the parallel thread.
            #cmd = 'sudo rm ' + filename
            # os.system(cmd)
            os.remove(filename)
        self.imgSetsInQ -= 1

    def _doMotionDetectionFromQ(self, aImageSet):

        if self.debug:
            print("Performing motion detection")

        self.processingStartTime = time.time()
        
        #IR: 
        self.changeDownsamplingLevel()
        imgList, fullSizeImgList = self._loadImageSequenceFromQ(aImageSet)
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

        self.processingEndTime = time.time()

        aliveCount = self.motionAliveCount
        #TM : get timestamp from list for when image was taken
        timestamp = self.sequenceTimeStampList[aImageSet]
        #timestamp = time.strftime("%Y%m%d-%H%M%S")
        #TM : get brightness from list for when image was taken
        brightness = self.imageBrightnessList[aImageSet]
        #brightness = self._getCurrentBrightness()
        threshold = 0  # TODO(geir): Need it?
        
        blobCount = largestAreaBlobCount
        maxBlobSize = largestBlobArea
        verdict = motion.evalMotionPropotionalBlobArea(largestAreaBlobs,
                                                       largestAreaBlobCount,
                                                       self.motionAreaPercent,
                                                       self.motionMaxBlobs,
                                                       self.motionMinArea)
                                                       
        # TMorton: SMS
        #if self.sendSMS == True:
        if self.textMessageRecipient is not None:
            if verdict == True:
                self.trueMotionCount+=1
                
        # TM: records the time it takes to process an image
        processingTime = round(
            self.processingEndTime - self.processingStartTime)

        # Save statistics in CSV
        dataList = [aliveCount, timestamp, brightness, threshold,
                    blobCount, maxBlobSize, verdict, processingTime]
        self.motionDataRecorder.writeData(dataList)
        imageName = timestamp + ".jpg"
        diffName = timestamp + "-" + str(verdict) + "-diff.jpg"
        imagePath = os.path.join(self.motionFilePath, imageName)
        diffPath = os.path.join(self.motionFilePath, diffName)
        cv2.imwrite(imagePath, imgList[largestAreaIndex])
        cv2.imwrite(diffPath, diffList[largestAreaIndex])
        
        #IR: Save true image sequence to miniSequence Folder
        # at the original size of the images
        if verdict == True:
            for listIndex in range(len(fullSizeImgList)):
                imgName = timestamp + "-" + str(listIndex) + ".jpg"
                imgFullPath = os.path.join(self.miniSequencePath,imgName)
                cv2.imwrite(imgFullPath,fullSizeImgList[listIndex])        
        
        self.motionAliveCount += 1
        if self.debug:
            print("Got motion data: ")
            print(dataList)

        # TM: Keeps track of the number of image sets that have been processed
        self.numberOfImgSetsProcessed += 1

        # IR: Reset variables to defaults
        self.resolutionX = self.originalResolutionX
        self.resolutionY = self.originalResolutionY
        self.motionMinArea = self.defaultMotionMinArea

    # IR: downsampling function
    def imageDownsampling(self, aImage, aDownLevel):
        # aImage= the input array image
        # downLevel = how many levels of sampling
        # perform the downsampling

        tempImg = aImage
        for n in range(aDownLevel):
            imgDownsampled = cv2.pyrDown(tempImg)
            #print 'downsampling'
            tempImg = imgDownsampled

        # change the global resolution parameters of the image
        self.resolutionX = self.resolutionX / (2 ** aDownLevel)
        self.resolutionY = self.resolutionY / (2 ** aDownLevel)
        # recalculate the motion min area with the new resolution
        self.motionMinArea = \
            motion.getCutoffObjectArea(self.resolutionX * self.resolutionY,
                                       self.FOVMinAreaDetected,
                                       self.FOVVertical,
                                       self.FOVHorizontal,
                                       self.FOVMaxDistance)
        return tempImg

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
            # TM: loads queue path
            self.queuePath = self.setParam(self.queuePath,
                                           'str',
                                           'General',
                                           'queuePath') 
            # IR: loads miniSequence path (where true images are saved)
            self.miniSequencePath = self.setParam(self.miniSequencePath,
                                                   'str',
                                                   'General',
                                                   'miniSequencePath')
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
            # TM: added for down-sampling
            self.downLevel = self.setParam(self.downLevel,
                                           'int',
                                           'Controller',
                                           'downLevel')
            # TM: added for queue
            self.backgroundRefreshWaitTime = self.setParam(self.backgroundRefreshWaitTime,
                                                           'float',
                                                           'Controller',
                                                           'backgroundRefreshWaitTime')
            # TM: added for queue
            self.timeToWaitForNextMotionImg = self.setParam(self.timeToWaitForNextMotionImg,
                                                            'float',
                                                            'Controller',
                                                            'timeToWaitForNextMotionImg')
            #TM: Added for ROI down-sampling
            self.ROI = self.setParam(self.ROI, 'str', 'General', 'ROI')
            #TM: Added for SMS feature
            #self.sendSMS = self.setParam(self.sendSMS, 'bool', 'General', 'sendSMS')
            #TM: SMS recipient
            self.textMessageRecipient = self.setParam(self.textMessageRecipient, 'str', 'General', 'textMessageRecipient')
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
        
    # IR: ROI downsampling function
    def downSampleROI(self, aROIimageName, aDownLevel):
        #read the ROI image to an array
        #perform downsampling on the image
        #send the downsampled ROI to the processor object
        #this way the original ROI can be downsampled as many times
        #at different levels
        if self.ROI is not None:
            imgROI = cv2.imread(aROIimageName, 0)
            #TM: Saving a copy of original ROI might be needed in the future
            
            for n in range(aDownLevel):
                downsampledROI = cv2.pyrDown(imgROI)
                imgROI = downsampledROI
                print 'ROI downsampling'
            #remove the blur regions between from the ROI downsampled image
            retval, imgROI = cv2.threshold(imgROI, 127, 255, cv2.THRESH_BINARY) 
            self.processor.loadROIfromControl(imgROI)
    
    def backgroundDownSample(self,aDownLevel):
        if self.strProcessor == "backSub":
            backgroundPath = os.path.join(self.tempFilePath,
                                        self.timelapseLatestImage)
            backgroundImg = cv2.imread(backgroundPath, cv2.CV_LOAD_IMAGE_COLOR)

            for n in range(aDownLevel):
                downsampledBackground = cv2.pyrDown(backgroundImg)
                backgroundImg = downsampledBackground
                print 'backgound downsampling'

            self.processor.loadBackgroundFromControl(backgroundImg)
        
    #IR : two levels of downsampling including ROI     
    def changeDownsamplingLevel(self):
        #checks the number of image sets in the Q
        #if the number is above the threshold 
        #increases the downsampling level to reduce the queue length 

        #maximum time to wait in the cue
        cueThreshold = 5 # assumed max number of images in Q 
        upperCueThreshold = 8
        lowerCueThreshold = 1
        #if self.downLevel == 0 and self.imgSetsInQ > cueThreshold:
        if self.downLevel == 0 and self.imgSetsInQ > cueThreshold and self.imgSetsInQ < upperCueThreshold:
            self.downLevel +=1
            self.downSampleROI("ROI.jpg", self.downLevel)
            self.backgroundDownSample(self.downLevel)

        elif self.downLevel == 1 and self.imgSetsInQ <= lowerCueThreshold:
            self.downLevel -= 1
            self.downSampleROI("ROI.jpg", self.downLevel)
            self.backgroundDownSample(self.downLevel)

        elif self.downLevel < 2 and self.imgSetsInQ >= upperCueThreshold:
            #self.downLevel +=1
            self.downLevel = 2
            self.downSampleROI("ROI.jpg", self.downLevel)
            self.backgroundDownSample(self.downLevel)

        elif self.downLevel == 2 and self.imgSetsInQ < cueThreshold:
            self.downLevel -= 1 
            self.downSampleROI("ROI.jpg", self.downLevel)
            self.backgroundDownSample(self.downLevel)
        else:  
            pass