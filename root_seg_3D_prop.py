#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct  1 13:38:02 2020

@author: apouch
"""

import subprocess 
import nibabel as nib
import multiprocessing as mp
import pandas as pd
import numpy as np
import time

C3D_PATH = '/usr/local/bin'
GREEDY_PATH = '/usr/local/bin'

def slice_registration(i,WDIR,fn_seg_ref,seg_lev,stj_lev,vaj_lev):
    
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

    WDIR = '/Volumes/stark/multi-atlas-test/tav11-masktest/testout'
    fn_img_rot = '/Volumes/stark/multi-atlas-test/tav11-masktest/img21_tav11_rot.nii.gz'
    fn_seg_rot = '/Volumes/stark/multi-atlas-test/tav11-masktest/seg_slice128.nii.gz'
    fn_vox_rot = '/Volumes/stark/multi-atlas-test/tav11-masktest/landmark_vox_rot.csv'
    fn_sl_vox_rot = '/Volumes/stark/multi-atlas-test/tav11-masktest/segslice_vox_rot.csv'
    fn_tform = '/Volumes/stark/multi-atlas-test/tav11-masktest/img21_tav11_tform.txt'
    
    # subdirectory in the working directory to store 2D data
    WDIR_2D = WDIR + '/slices'
    strc_subdir = ('mkdir -p ' + WDIR_2D)
    subprocess.call(strc_subdir,shell=True)
    
    # image spacing and voxel-to-physical transformation
    seg = nib.load(fn_seg_rot)
    nslices = seg.shape[2]
    img_affine = seg.affine
    
    # transformation applied by user
    fn_tform_mat = WDIR + '/img_tform.mat'
    strc_itk2mat = (C3D_PATH + '/c3d_affine_tool -itk ' + fn_tform + ''
                    ' -o ' + fn_tform_mat)
    subprocess.call(strc_itk2mat,shell=True)
    tform = pd.read_csv(fn_tform_mat,header=None,sep='\s+')
    tform = tform.to_numpy()
    
    # inverse of transformation applied by user
    fn_tform_inv = WDIR + '/img_tform_inv.txt'
    strc_tforminv = (C3D_PATH + '/c3d_affine_tool -itk ' + fn_tform + ''
                     ' -inv -o ' + fn_tform_inv)
    subprocess.call(strc_tforminv,shell=True)
    
    # level of STJ and VAJ (voxel coordinate) in rotated image
    vox_targ_rot = pd.read_csv(fn_vox_rot,header=None,sep='\s+')
    vox_targ_rot = vox_targ_rot.to_numpy() - 1
    vox_targ_rot = np.concatenate((np.transpose(vox_targ_rot[:, 0:3:1]),
                               np.ones((1,5))))
    stj_lev = int(np.ceil(vox_targ_rot[2,0]))
    vaj_lev = int(np.ceil(vox_targ_rot[2,4]))
    
    # level of 2D reference segmentation (voxel coordinate) in rotated image
    slice_vox_rot = pd.read_csv(fn_sl_vox_rot,header=None,sep='\s+')
    slice_vox_rot = slice_vox_rot.to_numpy() - 1
    seg_lev = int(np.ceil(slice_vox_rot[0,2]))
    
    # physical landmark coordinates in the rotated image
    coords_targ_rot = np.matmul(img_affine,vox_targ_rot)
    
    # physical landmark coordinates in original image
    fn_coords_targ = WDIR + '/landmarks_targ.csv'
    coords_targ = np.transpose(np.matmul(tform,coords_targ_rot))
    coords_targ = coords_targ[:, 0:3:1]
    np.savetxt(fn_coords_targ,coords_targ,delimiter=' ',fmt='%1.5f')
   
    # slice rotated image along z-axis
    strc_slice = (C3D_PATH + '/c3d ' + fn_img_rot + ' -slice z 0:-1'
                  + ' -oo ' + WDIR_2D + '/img_slice%03d.nii.gz')
    subprocess.call(strc_slice,shell=True)
    
    # slice 3D segmentation at the level of the 2D reference slice
    seg_lev_str = str(seg_lev).zfill(3)
    fn_seg_ref = WDIR_2D + '/seg_slice' + seg_lev_str + '.nii.gz'
    strc_seg_slice = (C3D_PATH + '/c3d ' + fn_seg_rot + ' -slice z' 
                      ' ' + seg_lev_str + ' -oo ' + fn_seg_ref)
    subprocess.call(strc_seg_slice,shell=True)
    
    # register reference slice to others in the 3D stack
    jobs = []
    for i in range(0,nslices):
        p = mp.Process(target=slice_registration,
                       args=(i,WDIR_2D,fn_seg_ref,seg_lev,stj_lev,vaj_lev))
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
        
        

    

        