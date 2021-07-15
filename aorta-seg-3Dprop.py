#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct  1 13:38:02 2020

@author: apouch
"""

import subprocess 
import multiprocessing as mp
import time

C3D_PATH = '/usr/local/bin'
GREEDY_PATH = '/usr/local/bin'
SNAP_PATH = '/usr/local/bin'

def slice_registration(i,WDIR,fn_seg_ref,lev_slice,lev_sup,lev_inf):
   
    lev_slice_str = str(lev_slice).zfill(3)

    if (i >= lev_sup and i <= lev_inf):
    
        if (i != lev_slice):
            
            tag_fix = str(i).zfill(3)
            
            fn_img_fix = WDIR + '/img_slice' + tag_fix + '.nii.gz'
            fn_img_mov = WDIR + '/img_slice' + lev_slice_str + '.nii.gz'
            
            #fn_img_fix_msk = WDIR + '/img_slice' + tag_fix + '_masked.nii.gz'
            #strc_mask = (C3D_PATH + '/c2d ' + fn_img_fix + ''
            #             ' ' + fn_mask + ' -multiply -o ' + fn_img_fix_msk)
            #subprocess.call(strc_mask,shell=True)
            
            '''
            fn_affout = (WDIR + '/affine' + lev_slice_str + '_to_' 
                            + tag_fix + '.mat')
            strc_affine = (GREEDY_PATH + '/greedy -d 2 -a'
                           ' -i ' + fn_img_fix + ' ' + fn_img_mov + ''
                           ' -ia-identity '
                           ' -dof 6 -o ' + fn_affout + ''
                           ' -n 100x50x0 -m NCC 4x4x4')
            subprocess.call(strc_affine,shell=True)
            '''
            
            fn_regout = (WDIR + '/warp' + lev_slice_str + '_to_' 
                            + tag_fix + '.nii.gz')
            strc_reg = (GREEDY_PATH + '/greedy -d 2'
                            ' -i ' + fn_img_fix + ' ' + fn_img_mov + ''
                            ' -m SSD'
                            ' -n 100x100'
                            ' -s 1mm 0.5mm'
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
        
        
def slice_registration_consec(i,WDIR,fn_img_fix,fn_img_mov,fn_seg_mov):
   
    '''
    fn_affout = (WDIR + '/affine' + lev_slice_str + '_to_' 
                    + tag_fix + '.mat')
    strc_affine = (GREEDY_PATH + '/greedy -d 2 -a'
                   ' -i ' + fn_img_fix + ' ' + fn_img_mov + ''
                   ' -ia-identity '
                   ' -dof 6 -o ' + fn_affout + ''
                   ' -n 100x50x0 -m NCC 4x4x4')
    subprocess.call(strc_affine,shell=True)
    '''
    
    tag_fix = str(i).zfill(3)
    
    fn_regout = (WDIR + '/warp' + tag_fix + '.nii.gz')
    strc_reg = (GREEDY_PATH + '/greedy -d 2'
                    ' -i ' + fn_img_fix + ' ' + fn_img_mov + ''
                    ' -m SSD'
                    ' -n 100x100'
                    ' -s 3mm 1.5mm'
                    ' -o ' + fn_regout)
    subprocess.call(strc_reg,shell=True)
    
    
    fn_seg_fix = (WDIR + '/seg_slice' + tag_fix + '.nii.gz')
    strc_apply_tform = (GREEDY_PATH + '/greedy -d 2'
                       ' -rf ' + fn_img_fix + ''
                       ' -ri NN'
                       ' -rm ' + fn_seg_mov + ' ' + fn_seg_fix + ''
                       ' -r ' + fn_regout)
    subprocess.call(strc_apply_tform,shell=True)



if __name__ == "__main__":
    
    start = time.time()
    
    WDIR='/Volumes/stark/multi-atlas-test/aorta'
    fn_img = '/Volumes/stark/multi-atlas-test/aorta/Example1.nii.gz'
    fn_seg = '/Volumes/stark/multi-atlas-test/aorta/Example1_segmentation_lumen.nii.gz'
    lev_inf = 54
    lev_sup = 0
    lev_slice = 23
    
    # number of slices
    nslices = lev_inf - lev_sup + 1
    
    # subdirectory in the working directory to store 2D data
    WDIR_2D = WDIR + '/slices'
    strc_subdir = ('mkdir -p ' + WDIR_2D)
    subprocess.call(strc_subdir,shell=True)

    # slice 3D segmentation at the level of the 2D reference slice
    lev_slice_str = str(lev_slice).zfill(3)
    fn_seg_ref = WDIR_2D + '/seg_slice' + lev_slice_str + '.nii.gz'
    strc_seg_slice = (C3D_PATH + '/c3d ' + fn_seg + ' -slice z' 
                      ' ' + lev_slice_str + ' -oo ' + fn_seg_ref)
    subprocess.call(strc_seg_slice,shell=True)
    
    # mask reference segmentation
    #fn_mask = WDIR_2D + '/mask_slice' + lev_slice_str + '.nii.gz'
    #strc_mask = (C3D_PATH + '/c2d ' + fn_seg_ref + ' -dilate 1 25x25vox'
    #             ' ' + ' -o ' + fn_mask)
    #subprocess.call(strc_mask,shell=True)
    
    # slice image along z-axis
    strc_slice = (C3D_PATH + '/c3d ' + fn_img + ' -slice z 0:-1'
                  + ' -oo ' + WDIR_2D + '/img_slice%03d.nii.gz')
    subprocess.call(strc_slice,shell=True)
    
    # mask reference image
    #fn_img_ref_masked = WDIR_2D + '/img_slice' + lev_slice_str + '_masked.nii.gz'
    #strc_mask = (C3D_PATH + '/c2d ' + WDIR_2D + '/img_slice' + lev_slice_str + '.nii.gz'
    #             ' ' + fn_mask + ' -multiply -o ' + fn_img_ref_masked)
    #subprocess.call(strc_mask,shell=True)
    
    # register reference slice to others in the 3D stack
    '''
    for i in range(lev_slice,nslices-1):
        j = i + 1
        tag_fix = str(j).zfill(3)
        tag_mov = str(i).zfill(3)
        fn_img_fix = WDIR_2D + '/img_slice' + tag_fix + '.nii.gz'
        fn_img_mov = WDIR_2D + '/img_slice' + tag_mov + '.nii.gz'
        fn_seg_mov = WDIR_2D + '/seg_slice' + tag_mov + '.nii.gz'
        slice_registration_consec(j,WDIR_2D,fn_img_fix,fn_img_mov,fn_seg_mov)
    for i in range(0,lev_slice):
        tag_fix = str(i).zfill(3)
        fn_seg_rs = WDIR_2D + '/seg_slice' + tag_fix + '.nii.gz'
        strc_segcopy = ('cp ' + fn_seg_ref + ' ' + fn_seg_rs)
        subprocess.call(strc_segcopy,shell=True)
    '''
    
    jobs = []
    for i in range(0,nslices):
        p = mp.Process(target=slice_registration,
                       args=(i,WDIR_2D,fn_seg_ref,lev_slice,lev_sup,lev_inf))
        jobs.append(p)
        p.start()
    for p in jobs:
        p.join()
    
    # create a 3D segmentation by tiling 2D segmentations
    fn_segvol = WDIR + '/seg_volume.nii.gz'
    strc_segvol = (C3D_PATH + '/c3d ' + WDIR_2D + '/seg_slice*.nii.gz -tile z' 
                   ' -smooth 1mm -thresh 0.5 inf 1 0 '
                   ' -o ' + fn_segvol)
    subprocess.call(strc_segvol,shell=True)
    
    # copy transform (header) from rotated image to segmentation
    strc_copytform = (C3D_PATH + '/c3d ' + fn_img + '' 
                      ' ' + fn_segvol + ' -copy-transform -o ' + fn_segvol)
    subprocess.call(strc_copytform,shell=True)
    
    print('Total time: ', time.time()-start, 'seconds')