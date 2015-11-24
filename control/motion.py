import cv2
import cv2.cv as cv
import numpy as np
import glob
import os
import math
# import picamera
from scipy import ndimage


# def overlayTest():
#    # takes an image
#    RPIcam = picamera.PiCamera()
#    RPIcam.resolution = (640, 480)  # set the camera resolution here
#    roi_ImgName = 'for_roi.jpg'
#    RPIcam.capture(roi_ImgName)
#    image_forROI = cv2.imread(roi_ImgName)
#
#    image_withROI = overlayROI(image_forROI, (20, 190), (620, 460))
#    ROI_overlay_Name = "image_withROI_arrayPassed.jpg"
#    cv2.imwrite(ROI_overlay_Name, image_withROI)
#
#    image_withROI = overlayROI('for_roi.jpg', (20, 190), (620, 460))
#    ROI_overlay_Name = "image_withROI_stringPassed.jpg"
#    cv2.imwrite(ROI_overlay_Name, image_withROI)
#
#    for file in glob.glob("./*for_roi*.jpg"):
#        cmd = 'sudo rm ' + file
#        os.system(cmd)
#
#    RPIcam.close()


def overlayROI(Image, pt1, pt2, colour=(0, 0, 255), weight=3):
    """
    This function creates a rectangle representing the ROI on an image.
    :param Image: Either a string containing the name of an image in the
    current working directory or an instance of a cv2 image.
    :param pt1: Point one of a rectangle represented by x,y coordinates.
    :param pt2: Point two of a rectangle represented by x,y coordinates.
    :param colour: The colour for the ROI overlay as a tuple with the format
    (B(lue), G(reen), R(ed))
    :param weight: The thickness of the rectangle.
    :return: A cv2 image with the ROI overlay superimposed on the image.
    """
    if isinstance(Image, str):
        roiView = cv2.imread(Image)
    else:
        roiView = Image
    cv2.rectangle(roiView, pt1, pt2, colour, weight)
    # ROI_overlay_Name = "image_withROI.jpg"
    # cv2.imwrite(ROI_overlay_Name, roiView)
    return roiView


def cleanFiles(a_file_list):
    """
    Deletes a list of files in the current working directory (or with a
    relative path to the file).
    :param a_file_list: A list() of strings containing files to be deleted.
    :return: NA
    """
    for entry in a_file_list:
        cmd = 'sudo rm ' + entry
        os.system(cmd)


def saveMotionDiffPair(aMotionImg, aDiffImg, aTimestamp, aTag):
    """
    Saves a reference picture and an accompanying difference picture to
    /saved_images/ in the current working directory.
    Reference name :'./saved_images/' + aTimestamp + aTag + '.jpg'
    Diff picture name: './saved_images/' + aTimestamp + aTag + 'diff.jpg'
    :param aMotionImg: Reference picture.
    :param aDiffImg: Difference picture.
    :param aTimestamp: Timestamp of picture as a string.
    :param aTag: Suffix added after timestamp before the .jpg or diff.jpg
     name of the file.
    :return: NA
    """
    motionImgName = './saved_images/' + aTimestamp + aTag + '.jpg'
    diffImgName = './saved_images/' + aTimestamp + aTag + 'diff.jpg'
    cv2.imwrite(motionImgName, aMotionImg)
    cv2.imwrite(diffImgName, aDiffImg)


def erodeThenDilate(aImg, aKernelSize, aIterationsErode, aIterationsDilate):
    """
    Will erode and then dilate an image a set number of times.
    :param aImg: The image to modify.
    :param aKernelSize: The kernel size used for operations.
    :param aIterationsErode: How many times to erode the image.
    :param aIterationsDilate: How many times to dilate the image.
    :return: Returns the modified image.
    """
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                       (aKernelSize, aKernelSize))
    erodedImg = cv2.erode(aImg, kernel, iterations=aIterationsErode)
    dilatedImg = cv2.dilate(erodedImg, kernel, iterations=aIterationsDilate)
    return dilatedImg


def dilateThenErode(aImg, aKernelSize, aIterationsDilate, aIterationsErode):
    """
    Will dilate and then erode an image a set number of times.
    :param aImg: The image to modify.
    :param aKernelSize: The kernel size used for operations.
    :param aIterationsDilate: How many times to dilate the image.
    :param aIterationsErode: How many times to erode the image.
    :return: Returns the modified image.
    """
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                       (aKernelSize, aKernelSize))
    dilatedImg = cv2.dilate(aImg, kernel, iterations=aIterationsDilate)
    erodedImg = cv2.erode(dilatedImg, kernel, iterations=aIterationsErode)
    return erodedImg


def closeImage(aImg, aKernelSize):
    """
    Will perform the cv2 close operation on an image with a supplied kernel
    size.
    :param aImg: The image to close.
    :param aKernelSize: The kernel size to use.
    :return: Returns the modified image.
    """
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                       (aKernelSize, aKernelSize))
    imgToClose = np.ndarray.copy(aImg)
    return cv2.morphologyEx(imgToClose, cv2.MORPH_CLOSE, kernel)


def openImage(aImg, aKernelSize):
    """
    Will perform the cv2 open operation on an image with a supplied kernel
    size.
    :param aImg: The image to open.
    :param aKernelSize: The kernel size to use.
    :return: Returns the modified image.
    """
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                       (aKernelSize, aKernelSize))
    imgToJoin = np.ndarray.copy(aImg)
    return cv2.morphologyEx(imgToJoin, cv2.MORPH_OPEN, kernel)


def xyFromROI(aROIPoints):
    """
    Takes a list of two ROI points and extracts the x,y pairs that makes up
    this ROI.
    :param aROIPoints: List of 2 tuples. x0, y0 = R[0], x1, y1 = R[1].
    :return: A tuple of 4 coordinates x0, y0, x1, y1.
    """
    pt1 = aROIPoints[0]
    pt2 = aROIPoints[1]
    x0, y0 = pt1
    x1, y1 = pt2
    return x0, y0, x1, y1


def removeSmallBlobs(aDiffImg, aMinArea):
    """
    Will remove the blobs that are smaller than the specified amount in an
    image.
    NOTE: SLOW! Do not use unless absolutely needed.
    TODO: Find a better algorithm.
    :param aDiffImg: The difference image to remove blobs from.
    :param aMinArea: The cut-off area for the blob in order to remove it.
    :return: A modified difference image with the smaller blobs removed.
    """
    # First let us get a list of all the blob areas in the picture
    blobs, numBlobs = getBlobs(aDiffImg)
    blobAreaList = getBlobAreaList(blobs, numBlobs)

    # Extract the labels we want to remove. The label is index+1.
    labelList = list()
    for index in range(len(blobAreaList)):
        if blobAreaList[index] < aMinArea:
            labelList.append(index+1)

    # Now we want to go through the blobs image where each position for each
    # blob is labelled and set all the positions that match an entry in
    # labelList to 0 in a copy of the original diff.
    areaRemovedDiff = np.ndarray.copy(aDiffImg)
    for row in range(len(blobs)):
        for column in range(len(blobs[row])):
            # print("In column: " + str(column))
            if blobs[row][column] in labelList:
                areaRemovedDiff[row][column] = 0
            # print("Value in A[" + str(row) + "][" + str(column) + ": " +
            #       str(aDiffImg[row][column]))

    return areaRemovedDiff


def getBlobs(aDiffImg):
    """
    Labels all blobs in an image and gives a count of how many there are.
    :param aDiffImg: A difference image to count blobs in.
    :return: A tuple (blobs, num_blobs) of an image with all blobs labelled and
    number of blobs found in the image.
    """
    # Get the blobs and number of blobs present in the diff image
    # Returned as (blobs, num_blobs)
    return ndimage.label(aDiffImg)


def getBlobStatistics(aDiffImg):
    """
    Give blob and contour data and statistics for a supplied difference image.
    :param aDiffImg: The difference image to analyse.
    :return: Tuple of blobs, number of blobs, contours and contour hierarchy.
    """
    # Avoid modifying original image, take a copy
    diffToAnalyse = np.ndarray.copy(aDiffImg)

    # Get the number of blobs present in the diff image
    blobs, num_blobs = getBlobs(aDiffImg)

    # Get the area of all blobs in picture
    contours, hierarchy = cv2.findContours(diffToAnalyse, cv.CV_RETR_LIST,
                                           cv.CV_CHAIN_APPROX_NONE)

    return blobs, num_blobs, contours, hierarchy


def getMaxAreaFromContours(aDiffContours):
    # Find the largest area present in the contours
    maxArea = 0
    area = 0
    for contour in aDiffContours:
        area = cv2.contourArea(contour)
        if area > maxArea:
            maxArea = area

    return maxArea


def getMaxAreaFromBlobs(aBlobAreaList):
    if len(aBlobAreaList) <= 0:
        maxArea = 0
    else:
        maxArea = max(aBlobAreaList)
    return maxArea


def getBlobAreaList(aBlobs, aBlobCount):
    blobList = [0]*aBlobCount
    for row in aBlobs:
        for entry in row:
            if entry > 0:
                blobList[entry-1] += 1

    return blobList


def evalMotionBlobCountMaxArea(aBlobCount, aArea, aBlobCountMax, aMaxArea):
    if (aBlobCount < aBlobCountMax) and (aArea > aMaxArea):
        verdict = True
        print('Motion detected in image.')

    else:
        verdict = False
        print('Motion not detected in image.')

    return verdict


def getCutoffObjectArea(aPixelArea, aMinObjectArea, aFOVVertical=54,
                        aFOVHorizontal=41, aDistance=30):
    FOVmetreSquare = 4.0 * (aDistance**2) * \
        math.tan(math.radians(aFOVVertical/2.0)) * \
        math.tan(math.radians(aFOVHorizontal/2.0))

    return (aMinObjectArea*aPixelArea)/(FOVmetreSquare)


def getPercentageCutoffObjectArea(aCutoffArea, aROIArea):
    return 100.0*aCutoffArea/aROIArea


def evalMotionPropotionalBlobArea(aBlobs, aBlobCount, aPercentage, aMaxBlobs,
                                  aMinTotArea=0):
    blobAreaList = getBlobAreaList(aBlobs, aBlobCount)
    totalArea = 0
    for entry in blobAreaList:
        totalArea += entry

    if (totalArea < aMinTotArea) or (totalArea == 0):
        return False

    else:
        areaCutoff = int((aPercentage/100.0)*float(totalArea))
        bigAreaCount = 0
        for area in sorted(blobAreaList, reverse=True):
            areaCutoff -= area
            bigAreaCount += 1
            if areaCutoff < 0:
                break
        if (bigAreaCount < aMaxBlobs) and (areaCutoff <= 0):
            return True
        else:
            return False


def getBrightness(aImage):
    return cv2.mean(aImage)


def simple2Diff(aRefImg, aMotionImg, aTimestamp, aROIPoints, aThreshold,
                aSaveImages=False):
    x0, y0, x1, y1 = xyFromROI(aROIPoints)

    ROI_P = aRefImg[y0:y1, x0:x1]
    ROI_C = aMotionImg[y0:y1, x0:x1]

    # The files below are never actually used for anything. If used for
    # something uncomment this section.
    """
    roipImgName = timestamp + 'roi_static.jpg'
    cv2.imwrite(roipImgName, ROI_P)
    roicImgName = timestamp + 'roi_motion.jpg'
    cv2.imwrite(roicImgName, ROI_C)
    # Clean up temporary files as we are now done with them
    # cleanFiles([roipImgName, roicImgName])
    """

    # Create difference images using the ROI images
    # ROI_P = cv2.cvtColor(ROI_P, cv2.COLOR_BGR2GRAY)
    # ROI_C = cv2.cvtColor(ROI_C, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(ROI_C, ROI_P)

    # Apply the threshold to get the sections that have the largest change in
    # intensity (?, correct term might be something else!)
    ret, diff_b = cv2.threshold(diff, int(aThreshold), 255, cv2.THRESH_BINARY)

    # Apply erosion and dilation to remove specs and smooth out the blobs in
    # the difference image
    diff_open = erodeThenDilate(diff_b, 3, 1, 1)
    # Keep an extra copy for saving later if told to by caller
    if aSaveImages:
        diff_saved = np.ndarray.copy(diff_open)

    # The file below are never actually used for anything. If used for
    # something uncomment this section.
    """
    # save the eroded/dilated image as difference
    imgName = aTimestamp + 'roi_diff.jpg'
    cv2.imwrite(imgName, diff_open)
    """

    return diff_open


def simple3Diff(aImgkMin2, aImgkMin1, aImgk, aTimestamp, aROIPoints,
                aThreshold, aSaveImages=False):
    """
    Algorithm described in:
    A real-time motion detection algorithm for traffic monitoring systems based
    on consecutive temporal difference
    Zhen Yu, Yanping Chen
    Dept. of Automation
    Xiamen University
    Xiamen, China
    Yuzhen20@xmu.edu.cn, chen_yanping1@163.com
    http://www.cs.ucr.edu/~ychen053/motion_detection.pdf
    Issue:
    Still not filling in the blobs completely.
    TODO: Attempt to do less dilation, try a couple of close then one or more
    joins in order to fill in the blobs properly
    """
    x0, y0, x1, y1 = xyFromROI(aROIPoints)

    ROIkMin2 = aImgkMin2[y0:y1, x0:x1]
    ROIkMin1 = aImgkMin1[y0:y1, x0:x1]
    ROIk = aImgk[y0:y1, x0:x1]

    # Create two sets of difference images, one from ROIkMin2, ROIkMin1 and one
    # from ROIkMin1 and ROI in order to compare the two diffs to evaluate which
    # region(s) are active/in motion in both of them.
    diffkMin1 = cv2.absdiff(ROIkMin2, ROIkMin1)
    diffk = cv2.absdiff(ROIkMin1, ROIk)

    # For each of the diff images we check each pixel and set it to 0 if below
    # a given threshold/intensity, else set it to 255
    # diffkMin1Return, diffkMin1 = cv2.threshold(diffkMin1, aThreshold, 255,
    #                                           cv2.THRESH_BINARY)
    # diffkReturn, diffk = cv2.threshold(diffk, aThreshold, 255,
    #                                   cv2.THRESH_BINARY)
    adaptiveThreshType = cv2.ADAPTIVE_THRESH_MEAN_C
    # adaptiveThreshType = cv2.ADAPTIVE_THRESH_GAUSSIAN_C
    adaptiveSize = 9
    diffkMin1 = cv2.adaptiveThreshold(diffkMin1, 255,
                                      adaptiveThreshType,
                                      cv2.THRESH_BINARY,
                                      adaptiveSize, adaptiveSize)
    diffk = cv2.adaptiveThreshold(diffk, 255,
                                  adaptiveThreshType,
                                  cv2.THRESH_BINARY,
                                  adaptiveSize, adaptiveSize)

    # Now find the union of the regions detected moving in both diff images,
    # this gives us the movement present in frame k-1.
    motionkMin1 = cv2.bitwise_and(diffkMin1, diffk)

    # Now we can find movement in frame k by subtracting diffk (containing
    # movement in k, k-1) from motionkMin1 (containing movement in frame k-1)
    motionk = cv2.absdiff(motionkMin1, diffk)

    # Remove specs that occur in the image before dilation
    # motionRemovedSpecs = removeSmallBlobs(motionk, 1)

    # Now dilate and erode the produced images to fill in blobs and eliminate
    # small blobs (specks)
    motion = dilateThenErode(motionk, 3, 3, 4)
    finalMotionDiff = closeImage(motion, 15)

    return finalMotionDiff


def blur3Diff(aImgkMin2, aImgkMin1, aImgk, aTimestamp, aROIPoints,
              aThreshold, aSaveImages=False):
    """
    Algorithm similar to simple3Diff() but with blurring of the diffs before
    comparisons.
    """
    x0, y0, x1, y1 = xyFromROI(aROIPoints)

    ROIkMin2 = aImgkMin2[y0:y1, x0:x1]
    ROIkMin1 = aImgkMin1[y0:y1, x0:x1]
    ROIk = aImgk[y0:y1, x0:x1]

    # Create two sets of difference images, one from ROIkMin2, ROIkMin1 and one
    # from ROIkMin1 and ROI in order to compare the two diffs to evaluate which
    # region(s) are active/in motion in both of them.
    diffkMin1 = cv2.absdiff(ROIkMin2, ROIkMin1)
    diffk = cv2.absdiff(ROIkMin1, ROIk)

    # For each of the diff images we check each pixel and set it to 0 if below
    # a given threshold/intensity, else set it to 255
    # diffkMin1Return, diffkMin1 = cv2.threshold(diffkMin1, aThreshold, 255,
    #                                           cv2.THRESH_BINARY)
    # diffkReturn, diffk = cv2.threshold(diffk, aThreshold, 255,
    #                                   cv2.THRESH_BINARY)
    adaptiveThreshType = cv2.ADAPTIVE_THRESH_MEAN_C
    # adaptiveThreshType = cv2.ADAPTIVE_THRESH_GAUSSIAN_C
    adaptiveSize = 9

    gaussStdDev = 10

    diffkMin1 = cv2.GaussianBlur(diffkMin1, (5, 5), gaussStdDev)
    diffkMin1 = cv2.adaptiveThreshold(diffkMin1, 255,
                                      adaptiveThreshType,
                                      cv2.THRESH_BINARY,
                                      adaptiveSize, adaptiveSize)

    diffk = cv2.GaussianBlur(diffk, (5, 5), gaussStdDev)
    diffk = cv2.adaptiveThreshold(diffk, 255,
                                  adaptiveThreshType,
                                  cv2.THRESH_BINARY,
                                  adaptiveSize, adaptiveSize)

    # Now find the union of the regions detected moving in both diff images,
    # this gives us the movement present in frame k-1.
    motionkMin1 = cv2.bitwise_and(diffkMin1, diffk)

    # Now we can find movement in frame k by subtracting diffk (containing
    # movement in k, k-1) from motionkMin1 (containing movement in frame k-1)
    motion = cv2.absdiff(motionkMin1, diffk)

    # Remove specs that occur in the image before dilation
    # motion = removeSmallBlobs(motion, 5)

    # Now dilate and erode the produced images to fill in blobs and eliminate
    # small blobs (specks)
    motion = dilateThenErode(motion, aKernelSize=3, aIterationsDilate=4,
                             aIterationsErode=2)

    # TODO Find a way to set this area as a function of... ROI? Look in to how
    # we can use the newly added getCutoffObjectArea() function to do this
    # NOTE: THE FUNCTION BELOW IS SLOW. AVOID IF POSSIBLE.
    # motion = removeSmallBlobs(motion, 200)

    motion = dilateThenErode(motion, aKernelSize=3, aIterationsDilate=4,
                             aIterationsErode=2)

    # motion = removeSmallBlobs(motion, 200)

    return motion
