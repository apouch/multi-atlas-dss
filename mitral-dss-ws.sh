#!/bin/bash

WS=$1
WDIR=$2
PATH_SCRIPTS=$3
TICKET_ID=$4

WM_PATH=/home/gormanlab/build/ANTs/bin
CONTEST_PATH=/home/gormanlab/build/bcmrep
CMREP_PATH=/home/gormanlab/build/cmrep

fn_img=$(itksnap-wt -P -i $WS -llf "Rotated Image")
tag_img=$(itksnap-wt -i $WS -lpbt "Rotated Image")
tag_img=${tag_img#*[}
tag_img=${tag_img%]*}
echo "Overlay image is: " $fn_img
echo "Overlay image tag is: " $tag_img

fn_annot=$WDIR/ws-annotations.txt
itksnap-wt -i $WS -annot-list > $fn_annot

fn_lm_vox=$WDIR/landmarks_vox.txt
awk '/APA/ {print $4 " " $5 " " $6}' $fn_annot > $fn_lm_vox
awk '/AC/ {print $4 " " $5 " " $6}' $fn_annot >> $fn_lm_vox
awk '/MPA/ {print $4 " " $5 " " $6}' $fn_annot >> $fn_lm_vox
awk '/PC/ {print $4 " " $5 " " $6}' $fn_annot >> $fn_lm_vox
awk '/MAL/ {print $4 " " $5 " " $6}' $fn_annot >> $fn_lm_vox

fn_lm_coords=$WDIR/landmarks_coords.csv
python $PATH_SCRIPTS/voxels2coords.py $WDIR $fn_lm_vox $fn_img

fn_ws_tform=$WDIR/ws-tform.txt
itksnap-wt -P -i $WS -lp $tag_img -props-get-transform > $fn_ws_tform

fn_tform_rot=$WDIR/img_tform_rot.txt
awk '{if (NR!=1) {print}}' $fn_ws_tform > $fn_tform_rot
#user-initialized rotation received (3%)
itksnap-wt -dssp-tickets-log $TICKET_ID info "User-initialized rotation received"
itksnap-wt -dssp-tickets-set-progress $TICKET_ID 0 1 0.03

fn_tform_rot_inv=$WDIR/img_tform_rot_inv.txt
c3d_affine_tool $fn_tform_rot -inv -o $fn_tform_rot_inv

sc=$(itksnap-wt -P -i $WS -registry-get Layers.Layer[${tag_img}].LayerMetaData.DisplayMapping.SelectedComponent)
echo $sc
#frame number identified (5%)
itksnap-wt -dssp-tickets-log $TICKET_ID info "Frame number identified"
itksnap-wt -dssp-tickets-set-progress $TICKET_ID 0 1 0.05

fn_img_rot=$WDIR/img_rot.nii.gz
c3d -mcs $fn_img -pick $sc -o $fn_img_rot
c3d $fn_img_rot $fn_img_rot -reslice-matrix $fn_tform_rot -o $fn_img_rot

fn_atlas_list='/home/apouch/ATLASES_MV/nrml_mv_atlas_list.csv'

# starting multi-atlas segmentation (10%)
itksnap-wt -dssp-tickets-log $TICKET_ID info "Starting multi-atlas segmentation"
itksnap-wt -dssp-tickets-set-progress $TICKET_ID 0 1 0.1

python $PATH_SCRIPTS/multi_atlas.py $WDIR $fn_img_rot $fn_lm_coords $fn_atlas_list
# multi-atlas segmentation complete (65%)
itksnap-wt -dssp-tickets-log $TICKET_ID info "Multi-atlas segmentation complete"
itksnap-wt -dssp-tickets-set-progress $TICKET_ID 0 1 0.65

fn_seg_rot=$WDIR/seg_atlas_consensus.nii.gz
fn_seg_consensus=$WDIR/seg_final.nii.gz
c3d -int 0 $fn_img_rot $fn_seg_rot -reslice-matrix $fn_tform_rot_inv -o $fn_seg_consensus

DIR_TMPL=$WDIR/template_initialization

if [[ ! -d $DIR_TMPL ]]; then
  mkdir -p $DIR_TMPL
fi

fn_med=/home/apouch/CMREP_TEMPLATES/medialtemplate_closed2.vtk
fn_bnd=/home/apouch/CMREP_TEMPLATES/medialtemplate_closed2.bnd.vtk
fn_seg_tmpl=/home/apouch/CMREP_TEMPLATES/medialtemplate_closed2.nii.gz
fn_lm_tmpl=/home/apouch/CMREP_TEMPLATES/medialtemplate_closed2_landmarks_coords.csv

# starting template initialization (70%)
itksnap-wt -dssp-tickets-log $TICKET_ID info "Starting template initialization"
itksnap-wt -dssp-tickets-set-progress $TICKET_ID 0 1 0.7

python $PATH_SCRIPTS/seg_reg_wlm.py $DIR_TMPL $fn_seg_rot $fn_lm_coords $fn_seg_tmpl $fn_lm_tmpl

fn_reg=$DIR_TMPL/deformation_cmp.nii.gz
c3d -mcs $fn_reg -oo $DIR_TMPL/deformation%02d.nii

fn_warpmesh=$DIR_TMPL/tmpl_def_init.vtk
$WM_PATH/warpmesh -w ants -m ras $fn_bnd $fn_warpmesh \
	$DIR_TMPL/deformation00.nii $DIR_TMPL/deformation01.nii $DIR_TMPL/deformation02.nii

fn_med_init=$DIR_TMPL/tmpl_med_init.vtk
cd $DIR_TMPL
$CONTEST_PATH/./contest -solver ma57 -lsq $fn_warpmesh $fn_warpmesh -o $fn_med_init
bash $PATH_SCRIPTS/cmrep_swap_points.sh ${fn_med_init%.vtk}_fit2tmp_med.vtk $fn_med $DIR_TMPL/model.vtk
bash $PATH_SCRIPTS/write_cmrep_param.sh $DIR_TMPL/model
bash $PATH_SCRIPTS/write_cmrep_header.sh $DIR_TMPL/model
# template initialization complete (80%)
itksnap-wt -dssp-tickets-log $TICKET_ID info "Template initialization complete"
itksnap-wt -dssp-tickets-set-progress $TICKET_ID 0 1 0.8

# running model fitting (85%)
itksnap-wt -dssp-tickets-log $TICKET_ID info "Running model fitting"
itksnap-wt -dssp-tickets-set-progress $TICKET_ID 0 1 0.85
$CMREP_PATH/cmrep_fit -m 2 \
	$DIR_TMPL/model_param.txt \
	$DIR_TMPL/model.cmrep \
	$fn_seg_rot \
	$DIR_TMPL/tmpfit
# model fitting complete - returning workspace (95%)

RESULT_WSP=$WDIR/result.itksnap
itksnap-wt -layers-set-main $fn_img_rot \
           -layers-set-seg $fn_seg_rot \
           -o $RESULT_WSP
#itksnap-wt -i $RESULT_WSP -layers-pick 001 -props-set-transform $fn_tform_rot \
#           -registry-set Layers.Layer[000].LayerMetaData.DisplayMapping.SelectedComponent $sc \
#           -o $RESULT_WSP
