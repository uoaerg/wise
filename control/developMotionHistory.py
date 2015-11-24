from Benchmarks.ImageCycler import ImageCycler
from Benchmarks.ImageCycler import Timer
import cv2
import cv2.cv as cv
import numpy as np
import motion

cycler = ImageCycler("./Benchmarks/dataset2014/dataset",
                     "./Benchmarks/dataset2014/results", aPreloadImages=2,
                     aNumberToProcess=0)

# TODO: Set up a minimal working motion history example
historyMaxCount = 0.02
imageCounter = 0.0
imageCountIncrement = 0.01
lastImage = None
lastlastImage = None
adaptiveThresholdType = cv2.ADAPTIVE_THRESH_GAUSSIAN_C
motionHistory = np.zeros((1, 1), dtype=np.float32)
imgROI = None

# Timers
totalTime = Timer()
catTime = Timer()
setTime = Timer()
# Counters
totalCount = 0
catCount = 0
setCount = 0

def getHistoryDiff(image):
    # TODO: Implement the history gradient
    global lastImage
    global lastlastImage
    global imageCounter
    global motionHistory
    global historyMaxCount
    global imgROI
    image = cv2.cvtColor(image, cv.CV_BGR2GRAY)
    image = cv2.bitwise_and(image, imgROI)
    dimensions = image.shape
    height, width = dimensions
    ROI = [(0, 0), (width, height)]
    diffImg = motion.blur3Diff(lastlastImage, lastImage, image, "fakestamp", ROI, 24)
    imageCounter += imageCountIncrement
    # Update the motion history with the new diff
    cv2.updateMotionHistory(diffImg, motionHistory, imageCounter, historyMaxCount)
    # Save the current image as last image
    lastlastImage = lastImage
    lastImage = image
    # Scale the motion history image
    motionDiff = np.zeros((height, width), dtype=np.uint8)
    # Scale the image according to the age of the motions in the image.
    # motionHistory[x,y] = timestamp if diff[x,y] != 0
    #                    = *timestamp if *timestamp - t > dt
    #                    = 0 otherwise
    subValue = (float(imageCounter) - float(historyMaxCount))
    clippedDiff = np.clip((motionHistory - subValue) / float(historyMaxCount),
                          0, 1)
    scaledDiff = np.uint8(clippedDiff*255)
    return scaledDiff

print(cycler.categories)
categoriesLeft = cycler.nextCategory()
while(categoriesLeft):
    print(cycler.currentCategory)
    setsLeft = cycler.nextSet()
    while setsLeft:
        print(cycler.currentSet)
        imgStatus = cycler.nextImage()
        imagesLeft, img = imgStatus[0], imgStatus[1]
        # TODO: Get image height and width here
        dimensions = img.shape
        height, width, depth = dimensions
        # TODO: Set up a new motion detector history
        motionHistory = np.zeros((height, width), dtype=np.float32)
        # TODO: Get the ROI for the current set
        imgROI = cycler.getCurrentROI()
        # print(imgROI)
        # TODO: Preload the first two images and apply the ROI
        lastlastImage = cv2.cvtColor(img, cv.CV_BGR2GRAY)
        lastlastImage = cv2.bitwise_and(lastlastImage, imgROI)
        imgStatus = cycler.nextImage()
        imagesLeft, img = imgStatus[0], imgStatus[1]
        lastImage = cv2.cvtColor(img, cv.CV_BGR2GRAY)
        lastImage = cv2.bitwise_and(lastImage, imgROI)
        imgStatus = cycler.nextImage()
        imagesLeft, img = imgStatus[0], imgStatus[1]
        while imagesLeft:
            # Code to process images here
            diffImg = getHistoryDiff(img)
            # Make all nonzero values 255!
            ret, diffImg = cv2.threshold(diffImg, 1, 255, cv2.THRESH_BINARY)
            # Code to save images here, using cycler
            cycler.saveDiff(diffImg)
            # Get next set of images
            imgStatus = cycler.nextImage()
            imagesLeft, img = imgStatus[0], imgStatus[1]
            setCount += 1


        # Code to clean up image processor here such as resetting background
        # subtractor or cleaning up temporary files
        catCount += setCount
        print(str(setCount) + " images processed in " +
              str(setTime.getAndReset()) + " seconds")
        setCount = 0

        # Check if there are more sets to process in the current category
        setsLeft = cycler.nextSet()

    # There might be items to clean up at this point but that should've been
    # handeled by the sets loop
    totalCount += catCount
    print(str(catCount) + " images processed in " +
          str(catTime.getAndReset()) + " seconds")
    catCount = 0

    # Check if there are more categories to traverse.
    categoriesLeft = cycler.nextCategory()

print(str(totalCount) + " images processed in " +
      str(totalTime.getDeltaTime()) + " seconds")
