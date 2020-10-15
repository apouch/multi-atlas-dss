#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct  1 13:38:02 2020

@author: apouch
"""

import sys
import subprocess 
import multiprocessing as mp
import time

C3D_PATH = '/usr/local/bin'
GREEDY_PATH = '/usr/local/bin'
SNAP_PATH = '/usr/local/bin'

def slice_registration(i,WDIR,fn_seg_ref,stj_lev,vaj_lev,seg_lev):
    
    seg_lev_str = str(seg_lev).zfill(3)
    
    if (i >= vaj_lev and i <= stj_lev):
    
        if (i != seg_lev):
            
            tag_fix = str(i).zfill(3)
            
            fn_img_fix = WDIR + '/img_slice' + tag_fix + '.nii.gz'
            fn_img_mov = WDIR + '/img_slice' + seg_lev_str + '.nii.gz'
            
            fn_regout = (WDIR + '/warp' + seg_lev_str + '_to_' 
                            + tag_fix + '.nii.gz')
            
            strc_reg = (GREEDY_PATH + '/greedy -d 2'
                            ' -i ' + fn_img_fix + ' ' + fn_img_mov + ''
                            ' -m SSD'
                            ' -n 100x100'
                            ' -s 3mm 1.5mm'
                            ' -o ' + fn_regout)
            subprocess.call(strc_reg,shell=True)
            
            fn_seg_rs = WDIR + '/seg_slice' + tag_fix + '.nii.gz'
            strc_apply_tform = (GREEDY_PATH + '/greedy -d 2'
                               ' -rf ' + fn_img_fix + ''
                               ' -ri NN'
                               ' -rm ' + fn_seg_ref + ' ' + fn_seg_rs + ''
                               ' -r ' + fn_regout)
            subprocess.call(strc_apply_tform,shell=True)
            
    else:
    
        tag_fix = str(i).zfill(3)
        fn_seg_blank = WDIR + '/seg_slice' + tag_fix + '.nii.gz'
        
        strc_segcopy = (C3D_PATH + '/c3d '+ fn_seg_ref + ' -scale 0'
                        ' -o ' + fn_seg_blank)
        subprocess.call(strc_segcopy,shell=True)


if __name__ == "__main__":
    
    start = time.time()
    
    WDIR=sys.argv[1]
    fn_img_rot=sys.argv[2]
    fn_seg_ref=sys.argv[3]
    stj_lev=int(sys.argv[4])
    vaj_lev=int(sys.argv[5])
    seg_lev=int(sys.argv[6])
    nslices=int(sys.argv[7])
    print('STJ level is ' + str(stj_lev))
    print('VAJ level is ' + str(vaj_lev))
    print('SEG level is ' + str(seg_lev))
    print('NSLICES is ' + str(nslices))
    
    # subdirectory in the working directory to store 2D data
    WDIR_2D = WDIR + '/slices'
 
    # transformation applied by user
    fn_tform = WDIR + '/img_tform_rot.mat'
    
    # inverse of transformation applied by user
    fn_tform_inv = WDIR + '/img_tform_rot_inv.txt'
   
    # register reference slice to others in the 3D stack
    jobs = []
    for i in range(0,nslices):
        p = mp.Process(target=slice_registration,
                       args=(i,WDIR_2D,fn_seg_ref,stj_lev,vaj_lev,seg_lev))
        jobs.append(p)
        p.start()
    for p in jobs:
        p.join()

    # create a 3D segmentation by tiling 2D segmentations
    fn_segvol = WDIR + '/seg_volume_rot.nii.gz'
    strc_segvol = (C3D_PATH + '/c3d ' + WDIR_2D + '/seg_slice*.nii.gz -tile z' 
                   ' -smooth 1mm -thresh 0.5 inf 1 0 '
                   ' -o ' + fn_segvol)
    subprocess.call(strc_segvol,shell=True)
    
    # copy transform (header) from rotated image to segmentation
    strc_copytform = (C3D_PATH + '/c3d ' + fn_img_rot + '' 
                      ' ' + fn_segvol + ' -copy-transform -o ' + fn_segvol)

    subprocess.call(strc_copytform,shell=True)
    
    # create a dilated mask of the rotated segmentation
    fn_segvol_dil = WDIR + '/seg_volume_rot_dil.nii.gz'
    strc_segdil = (C3D_PATH + '/c3d ' + fn_segvol + ' -dilate 1 15x15x0vox'
                   ' -o ' + fn_segvol_dil)
    subprocess.call(strc_segdil,shell=True)  

    # apply inverse transform to 3D segmentation and its mask to align 
    # them with the original image
    fn_segvol_rs = WDIR + '/seg_volume.nii.gz'
    strc_segvol_rs = (C3D_PATH + '/c3d -int 0 ' + fn_img_rot + ''
                      ' ' + fn_segvol + ' -reslice-matrix ' + fn_tform_inv + ''
                      ' -o ' + fn_segvol_rs)
    subprocess.call(strc_segvol_rs,shell=True)
    
    fn_segvol_mask_rs = WDIR + '/seg_volume_mask.nii.gz'
    strc_segvol_mask_rs = (C3D_PATH + '/c3d -int 0 ' + fn_img_rot + ''
                      ' ' + fn_segvol_dil + ' -reslice-matrix ' + fn_tform_inv + ''
                      ' -o ' + fn_segvol_mask_rs)
    subprocess.call(strc_segvol_mask_rs,shell=True)
    
    print('Total time: ', time.time()-start, 'seconds')