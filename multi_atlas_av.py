# -*- coding: utf-8 -*-
"""

This script runs landmark-initialized multi-atlas segmentation of the aortic valve and/or root.

INPUT ARGUMENTS: 
    WDIR is the working directory where intermediate/final data will be generated
    fn_img_targ is the filename of the image to be segmented
    fn_coords_targ is the filename of the csv file with physical coordinates of landmarks in the target image
    fn_mask_targ is the filename of a binary mask image of an ROI around the structure to be segmented
    fn_atlas_list is the csv file with the list of atlas filenames used for multi-atlas segmentation

"""

import sys
import numpy as np
import pandas as pd
import subprocess
import transformations as tform
import multiprocessing as mp

C3D_PATH = '/usr/local/bin'
GREEDY_PATH = '/usr/local/bin'
JLF_PATH = '/home/gormanlab/build/ANTs/bin/jointfusion'
FLAG_MULTIPROC=True

def atlas_registration(i, WDIR, fn_img_targ, coords_targ, fn_mask_targ, atlas_set):

    # numeric tag for output files related to this atlas
    tag = str(i).zfill(2)
    print('atlas' + tag + ' is being registered to target')
    
    # atlas image, segmentation, mask, and landmark files
    fn_img_atlas = atlas_set['fn_img'][i]    
    fn_seg_atlas = atlas_set['fn_seg'][i]
    fn_mask_atlas = atlas_set['fn_mask'][i]
    fn_coords_atlas = atlas_set['fn_coords'][i]

    # physical coordinates in landmark image
    coords_atlas = pd.read_csv(fn_coords_atlas,header=None)
    coords_atlas = coords_atlas.to_numpy()
    coords_atlas = np.concatenate((np.transpose(coords_atlas[:, 0:3:1]),
                                 np.ones((1,5))))

    # landmark-based tform for initialization
    T = tform.similarity_tform(coords_targ,coords_atlas)
    Tinv = np.linalg.inv(T)
    
    fn_affine_init = WDIR + '/affine_init_atlas' + tag + '.txt'
    np.savetxt(fn_affine_init,Tinv,delimiter=' ',fmt='%1.5f')

    fn_affine_init_inv = WDIR + '/affine_init_atlas' + tag + '_inv.txt'
    np.savetxt(fn_affine_init_inv,T,delimiter=' ',fmt='%1.5f')

    # target (fixed) image mask for computing similarity metric
    #fn_mask_targ = WDIR + '/mask' + tag + '.nii.gz'
    #str_aff_rs_mask = (C3D_PATH + '/c3d -int 0 ' + fn_img_targ + ' ' 
    #                             '' + fn_mask_atlas + ''
    #                             ' -reslice-matrix ' + fn_affine_init + ''
    #                             ' -o ' + fn_mask_targ + '')
    #subprocess.call(str_aff_rs_mask,shell=True)
    
    # masking of the target (fixed) image
    fn_img_targ_masked = WDIR + '/img_targ_masked.nii.gz'
    str_mask_targ = (C3D_PATH + '/c3d' 
                      ' ' + fn_img_targ + ''
                      ' ' + fn_mask_targ + ''
                      ' -multiply -o ' + fn_img_targ_masked)
    subprocess.call(str_mask_targ,shell=True)
    
    # affine initializion and masking of the atlas (moving) image
    fn_img_atlas_masked = WDIR + '/img_atlas' + tag + '_masked.nii.gz'
    str_atlas_mask = (C3D_PATH + '/c3d'
                      ' ' + fn_img_atlas + ''
                      ' ' + fn_mask_atlas + ''
                      ' -multiply -o ' + fn_img_atlas_masked)
    subprocess.call(str_atlas_mask,shell=True)
    
    fn_img_atlas_aff_rs = WDIR + '/img_atlas' + tag + '_affine_reslice.nii.gz'
    str_aff_rs_atlas = (GREEDY_PATH + '/greedy -d 3'
                        ' -rf ' + fn_img_targ + ''
                        ' -ri LINEAR ' 
                        ' -rm ' + fn_img_atlas_masked + ' ' + fn_img_atlas_aff_rs + ''
                        ' -r ' + fn_affine_init)
    subprocess.call(str_aff_rs_atlas,shell=True)
    
    #str_mask_atlas = (C3D_PATH + '/c3d' 
    #                  ' ' + fn_img_atlas_aff_rs + ''
    #                  ' ' + fn_mask_targ + ''
    #                  ' -multiply -o ' + fn_img_atlas_aff_rs)
    #subprocess.call(str_mask_atlas,shell=True)
    
    # deformable registration between the affine initialized atlas and target image
    fn_regout_deform = WDIR + '/deformation_atlas' + tag + '.nii.gz'
    str_def_atlas = (GREEDY_PATH + '/greedy -d 3 '
                        ' -i ' + fn_img_targ + '' 
                           ' ' + fn_img_atlas_aff_rs + ''
                        ' -m SSD '
                        ' -n 100x100x50 '
                        ' -gm ' + fn_mask_targ + ' '
                        ' -o ' + fn_regout_deform)
    subprocess.call(str_def_atlas,shell=True)

    #  warping of the atlas (moving) image and segmentation
    fn_seg_targ = WDIR + '/seg_atlas' + tag + '_reslice.nii.gz'
    str_def_rs_seg = (GREEDY_PATH + '/greedy -d 3'
                      ' -rf ' + fn_img_targ + ''
                      ' -ri LABEL 0.2vox'
                      ' -rm ' + fn_seg_atlas + ' ' + fn_seg_targ + ''
                      ' -r ' + fn_regout_deform  + ' ' + fn_affine_init)
    subprocess.call(str_def_rs_seg,shell=True)
    
    fn_img_atlas_def_rs = WDIR + '/img_atlas' + tag + '_def_reslice.nii.gz'
    str_def_rs_img = (GREEDY_PATH + '/greedy -d 3'
                      ' -rf ' + fn_img_targ + ''
                      ' -ri LINEAR'
                      ' -rm ' + fn_img_atlas + ' ' + fn_img_atlas_def_rs + ''
                      ' -r ' + fn_regout_deform + ' ' + fn_affine_init)
    subprocess.call(str_def_rs_img,shell=True)
    return

if __name__ == "__main__":
    
    # input arguments 
    WDIR = sys.argv[1]
    fn_img_targ = sys.argv[2]
    fn_coords_targ = sys.argv[3]
    fn_mask_targ = sys.argv[4]
    fn_atlas_list = sys.argv[5]
    
    # physical landmarks in target image
    coords_targ = pd.read_csv(fn_coords_targ,header=None)
    coords_targ = coords_targ.to_numpy()
    coords_targ = np.concatenate((np.transpose(coords_targ[:, 0:3:1]),
                                 np.ones((1,5))))
    
    # list of atlases
    atlas_set = pd.read_csv(fn_atlas_list,sep=',',header=None)
    atlas_set.columns = ['fn_img','fn_seg','fn_mask','fn_coords']
    
    str_atlas_img_rs = ''
    str_atlas_labels_rs = ''
    
    for i in range(0,len(atlas_set)):      
        tag = str(i).zfill(2)
        fn_img_atlas_def_rs = WDIR + '/img_atlas' + tag + '_def_reslice.nii.gz'
        fn_seg_targ = WDIR + '/seg_atlas' + tag + '_reslice.nii.gz'
        str_atlas_img_rs = str_atlas_img_rs + ' ' + fn_img_atlas_def_rs
        str_atlas_labels_rs = str_atlas_labels_rs + ' ' + fn_seg_targ
    
    # atlas registration to generate candidate segmentations of target image
    if (FLAG_MULTIPROC):
        jobs = []
        for i in range(0,len(atlas_set)):
            p = mp.Process(target=atlas_registration, 
                           args=(i,WDIR, fn_img_targ, coords_targ, 
                                 fn_mask_targ, atlas_set))
            jobs.append(p)
            p.start()            
        for p in jobs:
            p.join()
    else:
        pool = mp.Pool(mp.cpu_count())
        print("Number of processors: ", mp.cpu_count())
        results = [pool.apply_async(atlas_registration, 
                              args = (i, WDIR, fn_img_targ, coords_targ,
                                      fn_mask_targ,atlas_set))
                                for i in range(0,len(atlas_set))]
        pool.close()
        pool.join()
    
    # Without parallel processing...
    #for i in range(0, len(atlas_set)):
    #    atlas_registration(i, WDIR, fn_img_targ, coords_targ, atlas_set)
    
    # joint label fusion to generate consensus segmentation of the target image
    fn_seg_consensus = WDIR + '/seg_atlas_consensus.nii.gz'
    str_jointfusion = (JLF_PATH + '/./jointfusion 3 1 -g' + str_atlas_img_rs + ''
                       ' -tg ' + fn_img_targ + ' -l' + str_atlas_labels_rs + ''
                       ' -m Joint[0.1,1] -rp 4x4x4 -rs 4x4x4' 
                       ' ' + fn_seg_consensus)
    print('This is the joint label fusion step')
    #subprocess.call(str_jointfusion,shell=True)
    