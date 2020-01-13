import numpy as np
import cv2
from networktables import NetworkTables
import logging

logging.basicConfig(level=logging.DEBUG)



cap = cv2.VideoCapture(1) #Sets up the webcam for for the video stream

#IP address for network tables Roborio should be "10.25.82.2"
ip = "10.25.82.2"

NetworkTables.initialize(server=ip)
NetworkTables.flush()
nt = NetworkTables.getTable("ColorWheel")

#size for the square region of intrest where the color will be determined
roi_size = 10


######################################
#          CALIBRATION AREA          #
######################################
#Use this area to callibrate your colors

blue = np.array([240, 150, 38])
green = np.array([112, 140, 56])
red = np.array([34, 53, 235])
yellow = np.array([37, 178, 211])


########################################
########################################

#Sets the initial number of color changes to when it first sees the first color it will be zero
number_of_color_changes = -1
old_color = 'None'


#Video Loop during each loop a single frame from the camera will be processed
while 1:
    #Get an image from webcam stream
    ret, img = cap.read() 
    
    #Get dimensions of the image
    dimensions = img.shape
    height = img.shape[0]
    width = img.shape[1]
    channels = img.shape[2]


    
    #specifies location of the region of interest
    roi = img[height//2-roi_size//2:height//2+roi_size//2, width//2-roi_size//2:width//2+roi_size//2]

    #determines the average color of the region of interest
    average = roi.mean(axis=0).mean(axis=0)
    #changes the average color from a array of floats to an array of intergers
    average = average.astype(int)
    
    #makes variables for each color component of the ROI
    average_blue = int(average[0])
    average_green = int(average[1])
    average_red = int(average[2])
    

    #deremine absolute value of the error of the calibrated color versus the average color of the ROI
    #this will find the error of each componant
    blue_error = np.absolute(average-blue)
    green_error = np.absolute(average-green)
    red_error = np.absolute(average-red)
    yellow_error = np.absolute(average-yellow)
    
    #this summs up the error of eac color component
    blue_sum = np.sum(blue_error)
    green_sum = np.sum(green_error)
    red_sum = np.sum(red_error)
    yellow_sum = np.sum(yellow_error)
    
    #This creates a dictionary of the color error sum with its corresponding color
    color_error = {'Blue':blue_sum, 'Green':green_sum, 'Red':red_sum, 'Yellow':yellow_sum}

    #This returns the color with the minimum error and calculates a confidence
    color_guess = min(color_error, key=color_error.get)
    confidence = int(100-(color_error.get(color_guess))/765*100)

    #Adds text to the picture with the color guess and the confidence
    cv2.putText(img, color_guess + " " + str(confidence) +"%", (50, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    #if the color changes it adds to the counter
    if color_guess != old_color:
        number_of_color_changes = number_of_color_changes + 1

    #adds color change counter to picture
    cv2.putText(img, str(number_of_color_changes), (200, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    



    
    #adds a rectangle showing the ROI on the man image
    cv2.rectangle(img,(width//2-roi_size//2, height//2-roi_size//2), (width//2+roi_size//2, height//2+roi_size//2), (255,255,255), 2)
    #adds a rectangle with the average color of the ROI in the upper left side of the image
    cv2.rectangle(img,(0,0), (50,50), (average_blue, average_green, average_red),-1)


    # print('Average:           : ',average)
    # print('Color Guess        : ',color_guess)
    # print('Confidence         : ',confidence)
    

    

    #Sends value to network tables
    nt.putString("Color", color_guess)
    nt.putNumber("Color Confidence", confidence)
    nt.putString("Average Color", str(average))
    
 


    #updates old color
    old_color = color_guess
    
    #Shows Image on video feed
    cv2.imshow('img',img)
    
    #Allows to exit with 'esc' key
    k = cv2.waitKey(30) & 0xff
    if k == 27:
        break

cap.release()
cv2.destroyAllWindows()
