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
    
    '''
    seg_lev = 109
    stj_lev = 157
    vaj_lev = 73
    '''
    
    vox_targ = pd.read_csv(fn_vox_rot,header=None,sep='\s+')
    vox_targ = vox_targ.to_numpy()
    stj_lev = int(np.ceil(vox_targ[0,2]))
    vaj_lev = int(np.ceil(vox_targ[4,2]))
    
    slice_vox = pd.read_csv(fn_sl_vox_rot,header=None,sep='\s+')
    slice_vox = slice_vox.to_numpy()
    seg_lev = int(np.ceil(slice_vox[0,2]))
    
    # number of slices and spacing in 3D image
    seg = nib.load(fn_seg_rot)
    nslices = seg.shape[2]
    
    '''
    dx = str(seg.affine[0,0])
    dy = str(seg.affine[1,1])
    dz = str(seg.affine[2,2])
    '''
    
    # slice image along z-axis
    strc_slice = (C3D_PATH + '/c3d ' + fn_img_rot + ' -slice z 0:-1'
                  + ' -oo ' + WDIR + '/img_slice%03d.nii.gz')
    subprocess.call(strc_slice,shell=True)
    
    # slice 3D segmentation at the level of the 2D reference slice
    seg_lev_str = str(seg_lev).zfill(3)
    fn_seg_ref = WDIR + '/seg_slice' + seg_lev_str + '.nii.gz'
    strc_seg_slice = (C3D_PATH + '/c3d ' + fn_seg_rot + ' -slice z' 
                      ' ' + seg_lev_str + ' -oo ' + fn_seg_ref)
    subprocess.call(strc_seg_slice,shell=True)
    
    # register reference slice to others in the series
    jobs = []
    for i in range(0,nslices):
        p = mp.Process(target=slice_registration,
                       args=(i,WDIR,fn_seg_ref,seg_lev,stj_lev,vaj_lev))
        jobs.append(p)
        p.start()
    for p in jobs:
        p.join()
            
    fn_segvol = WDIR + '/seg_volume_rot.nii.gz'
    #strc_segvol = (C3D_PATH + '/c3d ' + WDIR + '/seg_slice*.nii.gz -tile z'
    #               ' -spacing ' + dx + 'x' + dy + 'x' + dz + 'mm'
    #               ' -smooth 1mm -thresh 0.5 inf 1 0 -o ' + fn_segvol + '')
    strc_segvol = (C3D_PATH + '/c3d ' + WDIR + '/seg_slice*.nii.gz -tile z' 
                   ' -smooth 1mm -thresh 0.5 inf 1 0 '
                   ' -o ' + fn_segvol)
    strc_copytform = (C3D_PATH + '/c3d ' + fn_segvol + ' ' 
                      '' + fn_img_rot + ' -copy-transform -o ' + fn_segvol)
    subprocess.call(strc_segvol,shell=True)
    subprocess.call(strc_copytform,shell=True)
    
    fn_tform_inv = WDIR + '/tform_inv.txt'
    strc_tforminv = (C3D_PATH + '/c3d_affine_tool -itk ' + fn_tform_inv + ''
                     ' -inv -oitk ' + fn_tform_inv)
    subprocess.call(strc_tforminv,shell=True)
    
    fn_segvol_rs = WDIR + '/seg_volume_rs.nii.gz'
    strc_segvol_rs = (C3D_PATH + '/c3d -int 0 ' + fn_img_rot + ''
                      ' ' + fn_segvol + ' -reslice-itk ' + fn_tform_inv + ''
                      ' -o ' + fn_segvol_rs)
    subprocess.call(strc_segvol_rs,shell=True)
    
    print('Total time: ', time.time()-start, 'seconds')
        
        

    

        