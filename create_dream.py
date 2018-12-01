import json
import subprocess
import os
import cv2 as cv
from PIL import Image #Image from PIL
import glob

def get_related_words(word):
    subprocess.call(["node", "google_trends.js", word])
    with open("google_trends.json", "r") as f:
        data = json.load(f)
    data = data["default"]["rankedList"][1]["rankedKeyword"]
    words = []
    for d in data:
     word = d["topic"]["title"]
     words.append(word)

    return words

def get_images(word, folder):
    if not os.path.exists(folder):
        os.mkdir(folder)

    subprocess.call(["python3", "download.py", "-s", word, "-d", folder, "-n", "20"])


def imgCrop(image, cropBox, boxScale=1):
    # Crop a PIL image with the provided box [x(left), y(upper), w(width), h(height)]

    # Calculate scale factors
    xDelta=max(cropBox[2]*(boxScale-1),0)
    yDelta=max(cropBox[3]*(boxScale-1),0)

    # Convert cv box to PIL box [left, upper, right, lower]
    PIL_box=[cropBox[0]-xDelta, cropBox[1]-yDelta, cropBox[0]+cropBox[2]+xDelta, cropBox[1]+cropBox[3]+yDelta]

    return image.crop(PIL_box)

def faceCrop(imagePattern,boxScale=1):
    # Select one of the haarcascade files:
    #   haarcascade_frontalface_alt.xml  <-- Best one?
    #   haarcascade_frontalface_alt2.xml
    #   haarcascade_frontalface_alt_tree.xml
    #   haarcascade_frontalface_default.xml
    #   haarcascade_profileface.xml
    face_cascade = cv.CascadeClassifier('haarcascade_frontalface_default.xml')

    imgList=glob.glob(imagePattern)
    if len(imgList)<=0:
        print('No Images Found')
        return

    for img in imgList:
        pil_im=Image.open(img)
        cv_im = cv.imread(img)
        gray = cv.cvtColor(cv_im, cv.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        for i, (x,y,w,h) in enumerate(faces):
            croppedImage=imgCrop(pil_im, (x,y,w,h),boxScale=boxScale)
            fname,ext=os.path.splitext(img)
            croppedImage.save(fname+'_crop'+str(i)+ext)



# Crop all jpegs in a folder. Note: the code uses glob which follows unix shell rules.
# Use the boxScale to scale the cropping area. 1=opencv box, 2=2x the width and height

def create_dream(file):
    with open(file, "r") as f:
        data = json.load(f)
    
print(get_related_words("Nicholas Cage"))

get_images("Nicolas Cage", "cage")

faceCrop('cage/*',boxScale=1)

#get_faces("cage.png")