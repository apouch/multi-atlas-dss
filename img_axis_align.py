#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct  1 11:31:22 2020

@author: apouch

THIS IS TEST SCRIPT

"""

import pandas as pd
import numpy as np
import nibabel as nib
import transformations as tf

fn_axis_coords = '/Volumes/stark/AV_ATLASES/Landmarks/seg05_tav06_root_Landmarks.csv'
fn_img = '/Volumes/stark/AV_ATLASES/seg05_tav06_root.nii.gz'

axis_coords = pd.read_csv(fn_axis_coords,header=None)
axis_coords = axis_coords.to_numpy()

img = nib.load(fn_img)
affine = img.affine

c = (np.array(img.shape) - 1) / 2 - 1.

img_vox_center = np.ones((4,1))
img_vox_center[0] = c[0]
img_vox_center[1] = c[1]
img_vox_center[2] = c[2]

img_coords_center = np.transpose(np.matmul(affine,img_vox_center))

'''
axis_coords_trans = img_coords_center
axis_coords_trans[0,0] = axis_coords[0,0] - img_coords_center[0,0]
axis_coords_trans[1,0] = axis_coords[0,1] - img_coords_center[0,1]
axis_coords_trans[2,0] = axis_coords[0,2] - img_coords_center[0,2]
'''

# angle wrt y-axis
beta = np.arctan(axis_coords_trans[0,1]/axis_coords_trans[0,0])
Tz = tf.rotz(beta)

# angle wrt z-axis
gamma = np.arctan(axis_coords_trans[0,1]/axis_coords_trans[0,2])
Tx = tf.rotx(gamma)

Trot = np.matmul(Tx,Tz)

axis_coords_rot = np.matmul(Trot,axis_coords_trans)