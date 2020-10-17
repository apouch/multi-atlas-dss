#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

This script transforms a set of voxel indices to physical coordinates

"""

import sys
import numpy as np
import nibabel as nib

WDIR = sys.argv[1]
fn_vox_targ = sys.argv[2]
fn_img_targ = sys.argv[3]

# get NIfTI sform 
img = nib.load(fn_img_targ)
sform = img.get_sform()

# voxel landmarks
vox_targ = np.genfromtxt(fn_vox_targ)
vox_targ = np.concatenate((np.transpose(vox_targ[:, 0:3:1]),np.ones((1,5)))) - 1

# physical landmarks
coords_targ = np.transpose(np.matmul(sform,vox_targ))
coords_targ = coords_targ[:, 0:3:1]

#write physical landmarks
fn_coords_targ = WDIR + '/landmarks_coords.csv'
np.savetxt(fn_coords_targ,coords_targ,delimiter=' ',fmt='%1.5f')