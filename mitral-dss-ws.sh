#!/bin/bash

WS=$1
WDIR=$2

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
python /home/apouch/multi_atlas_dss_repo/voxels2coords.py $WDIR $fn_lm_vox $fn_img

fn_ws_tform=$WDIR/ws-tform.txt
itksnap-wt -P -i $WS -lp $tag_img -props-get-transform > $fn_ws_tform

fn_tform_rot=$WDIR/img_tform_rot.txt
awk '{if (NR!=1) {print}}' $fn_ws_tform > $fn_tform_rot

fn_tform_rot_inv=$WDIR/img_tform_rot_inv.txt
c3d_affine_tool $fn_tform_rot -inv -o $fn_tform_rot_inv

sc=$(itksnap-wt -P -i $WS -registry-get Layers.Layer[${tag_img}].LayerMetaData.DisplayMapping.SelectedComponent)
echo $sc

fn_img_rot=$WDIR/img_rot.nii.gz
c3d -mcs $fn_img -pick $sc -o $fn_img_rot
c3d $fn_img_rot $fn_img_rot -reslice-matrix $fn_tform_rot -o $fn_img_rot

fn_atlas_list='/home/apouch/ATLASES_MV/nrml_mv_atlas_list.csv'

python /home/apouch/multi_atlas_dss_repo/multi_atlas.py $WDIR $fn_img_rot $fn_lm_coords $fn_atlas_list

fn_seg_rot=$WDIR/seg_atlas_consensus.nii.gz
fn_seg_consensus=$WDIR/seg_final.nii.gz
c3d $fn_img_rot $fn_seg_consensus -reslice-matrix $fn_tform_rot_inv -o $fn_seg_consensus

RESULT_WSP=$WDIR/result.itksnap
itksnap-wt -layers-set-main $fn_img \
           -layers-set-seg $fn_seg_consensus \
           -layers-add-anat $fn_img_rot \
           -o $RESULT_WSP
itksnap-wt -i $RESULT_WSP -layers-pick 001 -props-set-transform $fn_tform_rot \
           -registry-set Layers.Layer[000].LayerMetaData.DisplayMapping.SelectedComponent $sc \
           -o $RESULT_WSP
