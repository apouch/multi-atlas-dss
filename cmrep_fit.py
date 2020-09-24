#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 23 15:30:44 2020

@author: alison
"""

import sys
import multi_atlas
import numpy as np
import pandas as pd
import subprocess
import vtk
from vtk.util import numpy_support as vn

GREEDY_path = '/usr/local/bin'
'''
WDIR = sys.argv[1]
fn_seg_targ = sys.argv[2]
fn_coords_targ = sys.argv[3]
fn_template = sys.argv[4]
'''

WDIR = '/Volumes/stark/multi-atlas-test'
fn_seg_targ = '/Volumes/stark/multi-atlas-test/akita/seg_atlas_consensus.nii.gz'
fn_coords_targ = '/Volumes/stark/ATLASES_MV/img05_nrml11_landmarks_coords.csv'
fn_template = '/Volumes/stark/ATLASES_MV/mv_template/medialtemplate_closed2_filenames.csv'

coords_targ = np.genfromtxt(fn_coords_targ,delimiter=' ')
coords_targ = np.concatenate((np.transpose(coords_targ[:, 0:3:1]),
                             np.ones((1,5))))

template = pd.read_csv(fn_template,sep=',',header=None)
template.columns = ['fn_seg','fn_bnd','fn_coords']

fn_tmpl_seg = template['fn_seg'][0]
fn_tmpl_bnd = template['fn_bnd'][0]
fn_tmpl_coords = template['fn_coords'][0]

coords_tmpl = np.genfromtxt(fn_tmpl_coords,delimiter=' ')
coords_tmpl = np.concatenate((np.transpose(coords_tmpl[:, 0:3:1]),
                               np.ones((1,5))))

T = multi_atlas.similarity_tform(coords_targ,coords_tmpl)
Tinv = np.linalg.inv(T)

fn_affine_init = WDIR + '/affine_init_tmpl.txt'
np.savetxt(fn_affine_init,Tinv,delimiter=' ',fmt='%1.5f')

fn_affine_init_inv = WDIR + '/affine_init_tmpl_inv.txt'
np.savetxt(fn_affine_init_inv,T,delimiter=' ',fmt='%1.5f')

# deformable registration between the template and target segmentations
fn_regout_deform = WDIR + '/deformation_tmpl.nii.gz'
str_def_tmpl = (GREEDY_path + '/greedy -d 3 '
                    ' -i ' + fn_tmpl_seg + '' 
                       ' ' + fn_seg_targ + ''
                    ' -m SSD '
                    ' -it ' + fn_affine_init_inv + ''
                    ' -n 100x100x50 '
                    ' -o ' + fn_regout_deform)
#subprocess.call(str_def_tmpl,shell=True)

# apply deformation to the atlas (moving) image and segmentation
fn_tmpl_seg_rs = WDIR + '/seg_tmpl_reslice.nii.gz'
fn_tmpl_bnd_rs = WDIR + '/medial_template_init.vtk'
str_def_rs_seg = (GREEDY_path + '/greedy -d 3'
                  ' -rf ' + fn_seg_targ + ''
                  ' -rs ' + fn_tmpl_bnd + ' ' + fn_tmpl_bnd_rs + ''
                  ' -r ' + fn_regout_deform  + ' ' + fn_affine_init_inv)
#subprocess.call(str_def_rs_seg,shell=True)

#                  ' -ri LINEAR '
#                  ' -rs ' + fn_tmpl_bnd + ' ' + fn_tmpl_bnd_rs + ''
#                  ' -rm ' + fn_tmpl_seg + ' ' + fn_tmpl_seg_rs + ''

reader = vtk.vtkPolyDataReader()
reader.SetFileName(fn_tmpl_bnd)
reader.ReadAllScalarsOn()
reader.ReadAllVectorsOn()
reader.Update()

data = reader.GetOutput()
labels = vn.vtk_to_numpy(data.GetCellData().GetArray('Label'))
radius = vn.vtk_to_numpy(data.GetPointData().GetArray('Radius1'))

reader_rs = vtk.vtkPolyDataReader()
reader_rs.SetFileName(fn_tmpl_bnd_rs)
reader_rs.ReadAllScalarsOn()
reader_rs.ReadAllVectorsOn()
reader_rs.Update()

label_vtk = vn.numpy_to_vtk(labels)
label_vtk.SetName('Label')

radius_vtk = vn.numpy_to_vtk(radius)
radius_vtk.SetName('Radius')

data_rs = reader_rs.GetOutput()
#data_rs.GetCellData().AddArray(label_vtk)
data_rs.GetPointData().AddArray(radius_vtk)

fn_test = WDIR + '/testout_wlabels.vtk'
writer = vtk.vtkPolyDataWriter()
writer.SetFileName(fn_test)
writer.SetInputData(data_rs)
writer.Write()

        