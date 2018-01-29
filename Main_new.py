from tkinter import *
from tkinter import filedialog
import pymysql
from PIL import Image
import cv2
import numpy as np
import os
import DetectChars
import DetectPlates
import PossiblePlate
import time

# ##########################################################################
SCALAR_BLACK = (0.0, 0.0, 0.0)
SCALAR_WHITE = (255.0, 255.0, 255.0)
SCALAR_YELLOW = (0.0, 255.0, 255.0)
SCALAR_GREEN = (0.0, 255.0, 0.0)
SCALAR_RED = (0.0, 0.0, 255.0)

showSteps = False
root=Tk()
###################################################################################################
extracted_text=""
plate_no=""
owner_name=""
status=""
address=""

def main():

    print("choosen file = ")
    print(name)

    blnKNNTrainingSuccessful = DetectChars.loadKNNDataAndTrainKNN()

    if blnKNNTrainingSuccessful == False:
        print ("\nerror: KNN traning was not successful\n")
        return
    # end if
    if camera_pick=="true":
        imagename="test.jpg"
    else:
        imagename=name
    imgOriginalScene  = cv2.imread(imagename)

    if imgOriginalScene is None:
        print ("\nerror: image not read from file \n\n")
        os.system("pause")
        return
    # end if

    listOfPossiblePlates = DetectPlates.detectPlatesInScene(imgOriginalScene)

    listOfPossiblePlates = DetectChars.detectCharsInPlates(listOfPossiblePlates)

    #cv2.imshow("imgOriginalScene", imgOriginalScene)
    #cv2.imwrite("imgOriginalScene.png",imgOriginalScene)


    if len(listOfPossiblePlates) == 0:                          # if no plates were found
        print ("\nno license plates were detected\n")             # inform user no plates were found
    else:                                                       # else

                # sort the list of possible plates in DESCENDING order (most number of chars to least number of chars)
        listOfPossiblePlates.sort(key = lambda possiblePlate: len(possiblePlate.strChars), reverse = True)


        licPlate = listOfPossiblePlates[0]

        #cv2.imshow("imgPlate", licPlate.imgPlate)           # show crop of plate and threshold of plate
        cv2.imwrite("imgPlate.png",licPlate.imgPlate)

        #cv2.imshow("imgThresh", licPlate.imgThresh)
        cv2.imwrite("imgThresh.png",licPlate.imgThresh)

        if len(licPlate.strChars) == 0:                     # if no chars were found in the plate
            print ("\nno characters were detected\n\n")       # show message
            return                                          # and exit program
        # end if

        drawRedRectangleAroundPlate(imgOriginalScene, licPlate)             # draw red rectangle around plate

        global extracted_text
        extracted_text=licPlate.strChars
        print ("\nlicense plate read from image = " + licPlate.strChars + "\n")       # write license plate text to std out
        print ("----------------------------------------")


        writeLicensePlateCharsOnImage(imgOriginalScene, licPlate)           # write license plate text on the image

        #cv2.imshow("imgOriginalScene", imgOriginalScene)                # re-show scene image

        r = 300.0 / imgOriginalScene.shape[1]
        dim = (300, int(imgOriginalScene.shape[0] * r))

        # perform the actual resizing of the image and show it
        resized = cv2.resize(imgOriginalScene, dim, interpolation=cv2.INTER_AREA)


        cv2.imwrite("imgOriginalScene_with_Chars.png", resized)           # write image out to file


        #################################  Database work   ################
        db = pymysql.connect("localhost", "root", "", "testdb")
        cursor = db.cursor()
        sql = "SELECT * FROM plate_info"

        try:
            cursor.execute(sql)
            results = cursor.fetchall()
            #print(results)
        except:
            print("error from database")

        print("       INFORMATION FROM DATABSE")
        print("----------------------------------------")

        for i in range(0, 10):
            if results[i][0]==licPlate.strChars:
                print(results[i])
                global plate_no,owner_name,status,address
                plate_no=results[i][0]
                owner_name=results[i][1]
                status=results[i][2]
                address=results[i][3]


        db.close()
        ############################## db work end ######################################
    # end if else

    cv2.waitKey(0)

    return

# end main

###################################################################################################
def drawRedRectangleAroundPlate(imgOriginalScene, licPlate):

    p2fRectPoints = cv2.boxPoints(licPlate.rrLocationOfPlateInScene)            # get 4 vertices of rotated rect

    cv2.line(imgOriginalScene, tuple(p2fRectPoints[0]), tuple(p2fRectPoints[1]), SCALAR_RED, 2)         # draw 4 red lines
    cv2.line(imgOriginalScene, tuple(p2fRectPoints[1]), tuple(p2fRectPoints[2]), SCALAR_RED, 2)
    cv2.line(imgOriginalScene, tuple(p2fRectPoints[2]), tuple(p2fRectPoints[3]), SCALAR_RED, 2)
    cv2.line(imgOriginalScene, tuple(p2fRectPoints[3]), tuple(p2fRectPoints[0]), SCALAR_RED, 2)
# end function

###################################################################################################
def writeLicensePlateCharsOnImage(imgOriginalScene, licPlate):
    ptCenterOfTextAreaX = 0
    ptCenterOfTextAreaY = 0

    ptLowerLeftTextOriginX = 0
    ptLowerLeftTextOriginY = 0


    sceneHeight, sceneWidth, sceneNumChannels = imgOriginalScene.shape
    plateHeight, plateWidth, plateNumChannels = licPlate.imgPlate.shape

    intFontFace = cv2.FONT_HERSHEY_SIMPLEX                      # choose a plain jane font
    fltFontScale = float(plateHeight) / 30.0                    # base font scale on height of plate area
    intFontThickness = int(round(fltFontScale * 1.5))           # base font thickness on font scale

    textSize, baseline = cv2.getTextSize(licPlate.strChars, intFontFace, fltFontScale, intFontThickness)        # call getTextSize

            # unpack roatated rect into center point, width and height, and angle
    ( (intPlateCenterX, intPlateCenterY), (intPlateWidth, intPlateHeight), fltCorrectionAngleInDeg ) = licPlate.rrLocationOfPlateInScene

    intPlateCenterX = int(intPlateCenterX)              # make sure center is an integer
    intPlateCenterY = int(intPlateCenterY)

    ptCenterOfTextAreaX = int(intPlateCenterX)         # the horizontal location of the text area is the same as the plate

    if intPlateCenterY < (sceneHeight * 0.75):
        ptCenterOfTextAreaY = int(round(intPlateCenterY)) + int(round(plateHeight * 1.6))
    else:
        ptCenterOfTextAreaY = int(round(intPlateCenterY)) - int(round(plateHeight * 1.6))
    # end if

    textSizeWidth, textSizeHeight = textSize                # unpack text size width and height

    ptLowerLeftTextOriginX = int(ptCenterOfTextAreaX - (textSizeWidth / 2))           # calculate the lower left origin of the text area
    ptLowerLeftTextOriginY = int(ptCenterOfTextAreaY + (textSizeHeight / 2))          # based on the text area center, width, and height

            # write the text on the image
    cv2.putText(imgOriginalScene, licPlate.strChars, (ptLowerLeftTextOriginX, ptLowerLeftTextOriginY), intFontFace, fltFontScale, SCALAR_YELLOW, intFontThickness)
# end function



###################################################################################################



 #############gui-work############################

name=""
camera_pick="false"

def image_pick():

    root.filename = filedialog.askopenfilename(initialdir="C:/Users/Shubham Raj/PycharmProjects/anpr-assignment/Sample images", title="Select file",filetypes=(("png files", "*.png"), ("all files", "*.*")))
    global name
    name=root.filename

def c_pick():
    global camera_pick
    camera_pick="true"
    camera = cv2.VideoCapture(0)
    while True:
        return_value, image = camera.read()
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        cv2.imshow('CAMERA', gray)
        if cv2.waitKey(1) & 0xFF == ord('s'):
            cv2.imwrite('test.jpg', image)
            break
    camera.release()


root.title("PLATE-SELECTOR")
label1 = Label(root,text="TRACKon --> AUTOMATIC NUMBER PLATE RECOGNITION SYSTEM",fg="green",bg="black",height=4,width=100,font="bold 20")
button1 = Button(root,text="QUIT",fg="red",command=quit,width="10",height="3")

button2 = Button(root,text="PICK",command=image_pick,width="10",height="3")
c_button = Button(root,text="CAMERA",command=c_pick,width="10",height="3")


label2 = Label(root,text="Instructions",font="Verdana 12 bold underline")
label2_1 = Label(root,text="1-Click 'Pick' button to select an image",font="Verdana 10 italic")
label2_2 = Label(root,text="2-Now close this window by clicking the ( X ) sysmbol.",font="Verdana 10 italic")
label2_3 = Label(root,text="3-A window containing the information about vehicle will be obtained.",font="Verdana 10 italic")

img1 = PhotoImage(file="guiimage1.gif")
img2 = PhotoImage(file="guiimage2.gif")
img3 = PhotoImage(file="guiimage3.gif")

w1 = Label(root, compound=CENTER, image=img1,height="100")
w2 = Label(root, compound=CENTER, image=img2,width="600")
w3 = Label(root, compound=CENTER, image=img3,width="600",height="110")


label1.grid(row=0, column=0)
button2.grid(row=1, column=0)
c_button.grid(row=2,column=0)
button1.grid(row=3, column=0)

label2.grid(row=4,column=0)

label2_1.grid(row=5,column=0)
label2_2.grid(row=6,column=0)
label2_3.grid(row=7,column=0)

w1.grid(row=8,column=0)
w2.grid(row=9,column=0)
w3.grid(row=10,column=0)

root.mainloop()
main()
    ###############gui-end############################
######## new gui #######
root1=Tk()

root1.title("RESULT")
label3 = Label(root1,text="TRACKon --> AUTOMATIC NUMBER PLATE RECOGNITION SYSTEM",fg="green",bg="black",height=4,width=100,font="bold 20")
label3.pack()
#button3 = Button(root1,text="SHOW TEXT",command=show_text)
#button3.grid(row=1, column=0)



def counter_label(label):
    #global counter
    label.config(text=extracted_text)

def counter_label1(label_2):
    label_2.config(text=owner_name+"  -  "+address)

def counter_label2(label_5):
    label_5.config(text=status)



def save_command():
    text_file = open("Output.txt","w")
    text_file.write("PLATE NUMBER  ---->  "+extracted_text+"\n")
    text_file.write("OWNER  ----------->  "+owner_name+"\n")
    text_file.write("ADDRESS ---------->  " + address + "\n")
    text_file.write("STATUS  ---------->  "+status)
    text_file.close()
    exit(0)


label_1=Label(root1,text="RECOGNISED TEXT")
label_1.pack()


label = Label(root1, fg="red",bg="skyblue",font="10",width="100",height="3")
label.pack()
counter_label(label)

label_6=Label(root1,text="INFORMATION FROM DATABASE",fg="white",bg="grey",width="100",height="2",font="bold 15")
label_6.pack()

label_3=Label(root1,text="OWNER & Address")
label_3.pack()

label_2 = Label(root1, fg="red",bg="skyblue",font="10",width="100",height="2")
label_2.pack()
counter_label1(label_2)

label_4=Label(root1,text="STATUS")
label_4.pack()

label_5 = Label(root1, fg="red",bg="skyblue",font="10",width="100",height="2")
label_5.pack()
counter_label2(label_5)

#########   imaging work   ########
im1 = Image.open('imgOriginalScene_with_chars.png')
im1 .save('imgOriginalScene_with_chars.gif')

im2 = Image.open('imgPlate.png')
im2 .save('imgPlate.gif')

im3 = Image.open('imgThresh.png')
im3 .save('imgThresh.gif')

#########   imaging work end   ######

im_1 = PhotoImage(file="imgOriginalScene_with_chars.gif")
im_2 = PhotoImage(file="imgPlate.gif")
im_3 = PhotoImage(file="imgThresh.gif")

w_1 = Label(root1, compound=CENTER, image=im_1,height="100")
w_2 = Label(root1, compound=CENTER, image=im_2,width="600")
w_3 = Label(root1, compound=CENTER, image=im_3,width="600",height="110")
save_button = Button(root1,text="SAVE & EXIT",command=save_command,width="10",height="3")

w_1.pack()
w_2.pack()
w_3.pack()
save_button.pack()

root1.mainloop()

######### new gui end  #####












