#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 17 14:47:25 2020

@author: alison
"""

import sys
import subprocess
import numpy as np
import transformations as tform
import pandas as pd

GREEDY_PATH = '/usr/local/bin'

if __name__ == "__main__":
    
    # input arguments 
    WDIR = sys.argv[1]
    fn_seg_targ = sys.argv[2]
    fn_coords_targ = sys.argv[3]
    fn_seg_mov = sys.argv[4]
    fn_coords_mov = sys.argv[5]
    
    # physical landmarks in target image
    coords_targ = pd.read_csv(fn_coords_targ,header=None,delimiter=' ')
    coords_targ = coords_targ.to_numpy()
    coords_targ = np.concatenate((np.transpose(coords_targ[:, 0:3:1]),
                                 np.ones((1,5))))
    
    coords_mov = pd.read_csv(fn_coords_mov,header=None,delimiter=' ')
    coords_mov = coords_mov.to_numpy()
    coords_mov = np.concatenate((np.transpose(coords_mov[:, 0:3:1]),
                                 np.ones((1,5))))
    
    # landmark-based tform for initialization
    T = tform.similarity_tform(coords_targ,coords_mov)
    Tinv = np.linalg.inv(T)
    
    fn_affine_init = WDIR + '/affine_init.txt'
    np.savetxt(fn_affine_init,Tinv,delimiter=' ',fmt='%1.5f')

    fn_affine_init_inv = WDIR + '/affine_init_inv.txt'
    np.savetxt(fn_affine_init_inv,T,delimiter=' ',fmt='%1.5f')
    
    # affine initializion 
    fn_seg_mov_aff_rs = WDIR + '/seg_mov_affine_reslice.nii.gz'
    strc_aff_rs_atlas = (GREEDY_PATH + '/greedy -d 3'
                        ' -rf ' + fn_seg_targ + ''
                        ' -ri LABEL 0.2vox ' 
                        ' -rm ' + fn_seg_mov + ' ' + fn_seg_mov_aff_rs + ''
                        ' -r ' + fn_affine_init)
    subprocess.call(strc_aff_rs_atlas,shell=True)

    # deformable registration
    fn_regout = WDIR + '/deformation.nii.gz'
    fn_regout_inv = WDIR + '/deformation_inv.nii.gz'
    strc_def = (GREEDY_PATH + '/greedy -d 3 '
               ' -i ' + fn_seg_targ + '' 
               ' ' + fn_seg_mov_aff_rs + ''
               ' -m SSD '
               ' -n 100x100x40 '
               ' -o ' + fn_regout + ''
	       ' -oinv ' + fn_regout_inv)
    subprocess.call(strc_def,shell=True)
    
    # compose transformation
    fn_compose = WDIR + '/deformation_cmp.nii.gz'
    strc_cmp = (GREEDY_PATH + '/greedy -d 3 '
                ' -rf ' + fn_seg_mov + ''
                ' -r ' + fn_affine_init_inv + ' ' + fn_regout_inv + ''
                ' -rc ' + fn_compose)    
    subprocess.call(strc_cmp,shell=True)
