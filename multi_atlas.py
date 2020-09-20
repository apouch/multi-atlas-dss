# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
import subprocess

def trans(x):
    Tt = np.array([(1,0,0,x[0]),
                   (0,1,0,x[1]),
                   (0,0,1,x[2]),
                   (0,0,0,1)])
    return Tt
    
def rotx(alpha):
    Tx = np.array([(1,0,0,0),
                   (0,np.cos(alpha),-np.sin(alpha),0),
                   (0,np.sin(alpha),np.cos(alpha),0),
                   (0,0,0,1)])
    return Tx

def roty(beta):
    Ty = np.array([(np.cos(beta),0,np.sin(beta),0),
                   (0,1,0,0),
                   (-np.sin(beta),0,np.cos(beta),0),
                   (0,0,0,1)])
    return Ty

def rotz(gamma):
    Tz = np.array([(np.cos(gamma),-np.sin(gamma),0,0),
                   (np.sin(gamma),np.cos(gamma),0,0),
                   (0,0,1,0),
                   (0,0,0,1)])
    return Tz

def uniscale(s):
    Ts = np.array([(s,0,0,0),
                   (0,s,0,0),
                   (0,0,s,0),
                   (0,0,0,1)])
    return Ts

def mindist(x,fix,mov,flag):
    
    if(flag == 'translate'):
      
        T = trans(x)
    
    if(flag == 'rigid'):
    
        Tt = trans(x[:3])
        Tx = rotx(x[3])
        Ty = roty(x[4])
        Tz = rotz(x[5])
        T = np.matmul(Tx,np.matmul(Ty,np.matmul(Tz,Tt)))
    
    if(flag == 'similarity'):
        
        Tt = trans(x[:3])
        Tx = rotx(x[3])
        Ty = roty(x[4])
        Tz = rotz(x[5])
        Ts = uniscale(x[6])
        T = np.matmul(Ts,np.matmul(Tx,np.matmul(Ty,np.matmul(Tz,Tt))))
    
    mov_tformed = np.matmul(T,mov)
    
    diff = mov_tformed[0:3:1, :] - fix[0:3:1, :]
    Dsum = np.sum(np.sqrt(np.sum(np.square(diff),axis=0)))
    
    return Dsum

def similarity_tform(coords_targ,coords_atlas):
   
    ctarg = np.mean(coords_targ,axis=1)
    catlas = np.mean(coords_atlas,axis=1)
    
    Ttrans_targ = trans(-ctarg)
    Ttrans_atlas = trans(-catlas)
    
    coords_targ_trans = np.matmul(Ttrans_targ,coords_targ)
    coords_atlas_trans = np.matmul(Ttrans_atlas,coords_atlas)
    
    x0 = np.array([0,0,0,0,0,0,1])
    
    xrigid = minimize(mindist, x0, method='BFGS',
                      args=(coords_targ_trans,coords_atlas_trans,'rigid'))
    
    Tt = trans(xrigid.x[:3])
    Tx = rotx(xrigid.x[3])
    Ty = roty(xrigid.x[4])
    Tz = rotz(xrigid.x[5])
    
    Trigid = np.matmul(Tx,np.matmul(Ty,np.matmul(Tz,Tt)))
    coords_atlas_rigid = np.matmul(Trigid,coords_atlas_trans)
    
    xsim = minimize(mindist, x0, method='BFGS',
                   args=(coords_targ_trans,coords_atlas_rigid,'similarity'))
    
    Tt = trans(xsim.x[:3])
    Tx = rotx(xsim.x[3])
    Ty = roty(xsim.x[4])
    Tz = rotz(xsim.x[5])
    Ts = uniscale(xsim.x[6])
        
    Tsim = np.matmul(Ts,np.matmul(Tx,np.matmul(Ty,np.matmul(Tz,Tt))))
    
    Ttrans_targ_inv = trans(ctarg)
    
    T = np.matmul(Ttrans_targ_inv,np.matmul(Tsim,np.matmul(Trigid,Ttrans_atlas)))
        
    return T

C3D_path = '/usr/local/bin'
GREEDY_path = '/usr/local/bin'

WDIR = '/Volumes/stark/multi-atlas-test'
fn_atlas_list = '/Users/alison/multi_atlas_dss_repo/atlas_list.csv'
fn_coords_targ = '/Volumes/stark/HD-NEDU3-5-13-19/current/4Dsegs/nrml03/nrml03_atlases_trim/img05_nrml03_landmarks_coords.csv'
fn_img_targ = '/Volumes/stark/HD-NEDU3-5-13-19/current/4Dsegs/nrml03/img05_nrml03.nii.gz'

coords_targ = np.genfromtxt(fn_coords_targ,delimiter=' ')
coords_targ = np.concatenate((np.transpose(coords_targ[:, 0:3:1]),
                             np.ones((1,5))))

atlas_set = pd.read_csv(fn_atlas_list,sep=',',header=None)
atlas_set.columns = ['fn_img','fn_seg','fn_mask','fn_coords']

for i in range(0, len(atlas_set)):
    
    tag = str(i).zfill(2)

    fn_img_atlas = atlas_set['fn_img'][i]    
    fn_seg_atlas = atlas_set['fn_seg'][i]
    fn_mask_atlas = atlas_set['fn_mask'][i]
    fn_coords_atlas = atlas_set['fn_coords'][i]

    coords_atlas = np.genfromtxt(fn_coords_atlas)
    coords_atlas = np.concatenate((np.transpose(coords_atlas[:, 0:3:1]),
                                   np.ones((1,5))))

    # landmark-based tform for initialization
    T = similarity_tform(coords_targ,coords_atlas)
    Tinv = np.linalg.inv(T)
    
    fn_affine_init = WDIR + '/affine_init_atlas' + tag + '.txt'
    np.savetxt(fn_affine_init,Tinv,delimiter=' ',fmt='%1.5f')

    fn_affine_init_inv = WDIR + '/affine_init_atlas' + tag + '_inv.txt'
    np.savetxt(fn_affine_init_inv,T,delimiter=' ',fmt='%1.5f')

    # target (fixed) image mask for computing similarity metric
    fn_mask_targ = WDIR + '/mask' + tag + '.nii.gz'
    str_aff_rs_mask = (C3D_path + '/c3d -int 0 ' + fn_img_targ + ' ' 
                                 '' + fn_mask_atlas + ''
                                 ' -reslice-matrix ' + fn_affine_init + ''
                                 ' -o ' + fn_mask_targ + '')
    subprocess.call(str_aff_rs_mask,shell=True)
    
    # mask the target (fixed) image
    fn_img_targ_masked = WDIR + '/img_targ_masked.nii.gz'
    str_mask_targ = (C3D_path + '/c3d' 
                      ' ' + fn_img_targ + ''
                      ' ' + fn_mask_targ + ''
                      ' -multiply -o ' + fn_img_targ_masked)
    subprocess.call(str_mask_targ,shell=True)
    
    # affine initialize and mask the atlas (moving) image
    fn_img_atlas_aff_rs = WDIR + '/img_atlas' + tag + '_affine_reslice.nii.gz'
    str_aff_rs_atlas = (GREEDY_path + '/greedy -d 3'
                        ' -rf ' + fn_img_targ + ''
                        ' -ri LINEAR ' 
                        ' -rm ' + fn_img_atlas + ' ' + fn_img_atlas_aff_rs + ''
                        ' -r ' + fn_affine_init)
    subprocess.call(str_aff_rs_atlas,shell=True)
    
    str_mask_atlas = (C3D_path + '/c3d' 
                      ' ' + fn_img_atlas_aff_rs + ''
                      ' ' + fn_mask_targ + ''
                      ' -multiply -o ' + fn_img_atlas_aff_rs)
    subprocess.call(str_mask_atlas,shell=True)
    
    # deformable registration between the target and affine initialized atlas
    fn_regout_deform = WDIR + '/deformation_atlas' + tag + '.nii.gz'
    str_def_atlas = (GREEDY_path + '/greedy -d 3 '
                        ' -i ' + fn_img_targ + '' 
                           ' ' + fn_img_atlas_aff_rs + ''
                        ' -m SSD '
                        ' -n 100x100x50 '
                        ' -gm ' + fn_mask_targ + ' '
                        ' -o ' + fn_regout_deform)
    subprocess.call(str_def_atlas,shell=True)

    # apply deformation to the atlas (moving) image and segmentation
    fn_seg_targ = WDIR + '/seg_atlas' + tag + '_reslice.nii.gz'
    str_def_rs_seg = (GREEDY_path + '/greedy -d 3'
                      ' -rf ' + fn_img_targ + ''
                      ' -ri NN'
                      ' -rm ' + fn_seg_atlas + ' ' + fn_seg_targ + ''
                      ' -r ' + fn_regout_deform  + ' ' + fn_affine_init)
    subprocess.call(str_def_rs_seg,shell=True)
    
    fn_img_atlas_def_rs = WDIR + '/img_atlas' + tag + '_def_reslice.nii.gz'
    str_def_rs_img = (GREEDY_path + '/greedy -d 3'
                      ' -rf ' + fn_img_targ + ''
                      ' -ri LINEAR'
                      ' -rm ' + fn_img_atlas_aff_rs + ' ' + fn_img_atlas_def_rs + ''
                      ' -r ' + fn_regout_deform)
    subprocess.call(str_def_rs_img,shell=True)
