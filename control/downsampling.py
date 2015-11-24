import cv2
import os 
import control

con = control.Controller("sample.cfg", "False")

def imageDownsampling(aImage, downLevel):
	# aImage= the input array image
	#downLevel = how many levels of sampling 
	
	#read the image to an array
	#img = cv2.imread(aImage, cv2.CV_LOAD_IMAGE_COLOR)
	
	#perform the downsampling 
	tempImg = aImage
	for n in xrange(downLevel):
		imgDownsampled = cv2.pyrDown(tempImg)
		tempImg = imgDownsampled

	#save the downsampled image with the same name 
	#in a different forder
	#savePath = os.path.join("./downsampled", aImage)
	#cv2.imwrite(savePath, tempImg)
	
	#change the global resolution parameters of the image
	if (downLevel > 0):
		con.resolutionX = con.resolutionX / (2 ** downLevel)
		con.resolutionY = con.resolutionY / (2 ** downLevel)
	#print con.resolutionX, con.resolutionY
	return tempImg


def main():
	imageDownsampling('22-07-15--10-38-02.jpg', 3 )

if __name__ == '__main__':
	main()




