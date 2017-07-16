#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sat Jul 15 15:18:58 2017

@author: pistol
"""
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import cv2
import time 
#from image2ism_new import extrinsicTransform, determineHorizon,intersection_line_plane,update_homography
from image2ism_new import InversePerspectiveMapping

useMultiChannel = 2
dirTestImage = '/home/pistol/DataFolder/stereo0.png'




if useMultiChannel == 0:
    imgIn = cv2.cvtColor(cv2.imread(dirTestImage),cv2.COLOR_BGR2RGB)
elif useMultiChannel == 1:
    imgIn = cv2.cvtColor(cv2.imread(dirTestImage),cv2.COLOR_BGR2GRAY)
elif useMultiChannel == 2:
    
    filename = '/home/pistol/Code/ros_workspaces/private/src/fcn8_ros/src/semanticOutputData.npz'
    filenameImage = '/home/pistol/Code/ros_workspaces/private/src/fcn8_ros/src/test_img2.png'
    imgRaw = cv2.imread(filenameImage)
    
    out = np.load(filename)
    imgClass = out['imgClass']
    imgConfidence = out['imgConfidence']

    configFile = '../cfg/image2ismFcn8.cfg'
    configData = open(configFile,'r') 
    configText = configData.read()
    strsClassNumberAndName = [line for idx,line in enumerate(str(configText).split('\n')) if line is not '' and idx is not 0]
    pubOutputTopics = {}
    outputTopicsNumber = {}
    loadFile = False
    if loadFile:
        for strClass in strsClassNumberAndName:
            strNumberAndClass = strClass.split(' ')
            outputTopicsNumber[strNumberAndClass[1]] = int(strNumberAndClass[0])
    else:
        outputTopicsNumber['human'] = 0
        
        
    #for each class
    for objectType in outputTopicsNumber.keys():
        classNumber = outputTopicsNumber[objectType]
        bwClass = imgClass==classNumber
        imgConfidenceClass = np.zeros_like(imgConfidence)
        imgConfidenceClass[bwClass] = imgConfidence[bwClass]
        
    imgIn = imgConfidenceClass
        
        
        
        
t1 = time.time()



maxDistance = 20.0
## Extrinsic Camera settings
# Camera angling
degPitch = 20.0 # Degrees in downward direction.
degYaw = 0
degRoll = 0

# Camera position 
camHeight = 2.0;
pCamera = np.array([0,0,camHeight])

## Intrinsic Camera settings
# Focal length fx,fy
fl = np.array([582.5641679547480,581.4956911617406])

# Principal point offset x0,y0
ppo = np.array([512.292836648199,251.580929633186])

# Axis skew
s = 0.0

degCutBelowHorizon = 7.5 # 10.0

# Image dimensions. (The input image size to be remapped and the original image size is not always the same !!! If e.g. the input image have been resized)
imDimOrg = [544,1024]

# Grid resolution. 
resolution = 0.1


imDim = imgIn.shape[0:2]
# Detemine if the image is [nRows,nCols] or [nRows,nCols,nChannels]
if len(imgIn.shape) == 2:    
    multiChannel = False
else:
    multiChannel = True


### INIT #############
# DETERMINE K 
# Camera intrinsic matrix is determined. 
K = np.eye(3)
K[[0,1],[0,1]] = fl; 
K[0:2,2] = ppo;
K[0,1] = s
#K1 = np.array([[fl[0], s, ppo[0]],[0,fl[1],ppo[1]],[0,0,1]])
Kinv = np.linalg.inv(K)


# Determine field-of-view from focal length and image dimensions.
#radFOV = 2*np.arctan(imDimOrg/(2*fl))

######################

 # Convert to radians
radPitch = degPitch*np.pi/180
radYaw = degYaw*np.pi/180
radRoll = degRoll*np.pi/180

# The horizon is determined. 
# rHorizonTrue: The actual horizon. 
# rHorizon: To avoid uncertain localization, the image is cropped below the horizon by degCutBelowHorizon
#rHorizon, rHorizonTrue = determineHorizon(radFOV,radPitch,degCutBelowHorizon=10.0)

# The extrinsic transformation is determined by angling (radPitch,radYaw,radRoll) and position of camera (pCamera)
#T_extrinsic = extrinsicTransform(radPitch,radYaw,radRoll,pCamera)

# Determine homography
#M,pDstSize = update_homography(T_extrinsic, pCamera, imDimOrg,imDim, Kinv,resolution,rHorizon)


ipm = InversePerspectiveMapping(resolution,degCutBelowHorizon)

# Update intrinsic based on focal length, principal point offset, original image resolution and optionally skew.
# (Consider making a function to update based on K)
ipm.update_intrinsic(fl,ppo,imDimOrg)

# Update extrinsic 
# (Consider making a function to updated based on a single transformation)
ipm.update_extrinsic(radPitch,radYaw,radRoll,pCamera)

# Update homography
pRayStarts,pDst,rHorizon, rHorizonTrue = ipm.update_homography(imDim)

# Create wrapped image. 
warped = ipm.makePerspectiveMapping(imgIn)

# Consider making mapping matrices - like in the previous version. 
#ipm.M
#mapXY = 

print 'run time: ', (time.time()-t1)*1000,  'ms' 


########################

# Draw horizon to image
if rHorizonTrue > 0:
    pHorizon = (imDim[0]*rHorizon).astype(np.int)
    pHorizonTrue = (imDim[0]*rHorizonTrue).astype(np.int)
    cv2.line(imgIn,(0, pHorizon),(imDim[1],pHorizon),(255,255,255),3)
    cv2.line(imgIn,(0, pHorizonTrue),(imDim[1],pHorizonTrue),(255,255,255),3)
    

#plt.figure()
#plt.imshow(imgRaw)
plt.figure()
plt.imshow(imgIn)
plt.figure()
plt.imshow(warped)


fig = plt.figure()

ax = fig.add_subplot(111, projection='3d')
n = 100

points = np.vstack((pCamera,pRayStarts,pDst))
#points = np.vstack((pCamera,linePX,pDst[[0,3],:]))


X = points[:,0]
Y = points[:,1]
Z = points[:,2]
ax.scatter(X,Y,Z)
ax.set_xlabel('X Label')
ax.set_ylabel('Y Label')
ax.set_zlabel('Z Label')

max_range = np.array([X.max()-X.min(), Y.max()-Y.min(), Z.max()-Z.min()]).max() / 2.0

mid_x = (X.max()+X.min()) * 0.5
mid_y = (Y.max()+Y.min()) * 0.5
mid_z = (Z.max()+Z.min()) * 0.5
ax.set_xlim(mid_x - max_range, mid_x + max_range)
ax.set_ylim(mid_y - max_range, mid_y + max_range)
#ax.set_zlim(mid_z - max_range, mid_z + max_range)
ax.set_zlim(0, mid_z + max_range)
plt.show()