#!/bin/bash

WS=$1
WDIR=$2
SEG_PATH=$3

fn_img=$(itksnap-wt -P -i $WS -llf "Rotated Image")
tag_img=$(itksnap-wt -i $WS -lpbt "Rotated Image")
tag_img=${tag_img#*[}
tag_img=${tag_img%]*}
echo "Overlay image is: " $fn_img
echo "Overlay image tag is: " $tag_img

fn_seg_rot=$(itksnap-wt -P -i $WS -lp S -pgf)
fn_seg_rot=${fn_seg_rot##*]} 
echo "Rotated segmentation is " $fn_seg_rot

fn_annot=$WDIR/ws-annotations.txt
itksnap-wt -i $WS -annot-list > $fn_annot

fn_lm_vox=$WDIR/landmarks_vox.txt
awk '/VAJ/ {print $4 " " $5 " " $6}' $fn_annot > $fn_lm_vox
awk '/STJ/ {print $4 " " $5 " " $6}' $fn_annot >> $fn_lm_vox
awk '/2D/ {print $4 " " $5 " " $6}' $fn_annot >> $fn_lm_vox

fn_ws_tform=$WDIR/ws-tform.txt
itksnap-wt -P -i $WS -lp $tag_img -props-get-transform > $fn_ws_tform

fn_tform_rot=$WDIR/img_tform_rot.txt
awk '{if (NR!=1) {print}}' $fn_ws_tform > $fn_tform_rot

fn_tform_rot_inv=$WDIR/img_tform_rot_inv.txt
c3d_affine_tool $fn_tform_rot -inv -o $fn_tform_rot_inv

WDIR_2D=$WDIR/slices
mkdir -p $WDIR_2D

sc=$(itksnap-wt -P -i $WS -registry-get Layers.Layer[${tag_img}].LayerMetaData.DisplayMapping.SelectedComponent)
echo $sc

fn_img_rot=$WDIR/img_rot.nii.gz
c3d -mcs $fn_img -pick $sc -o $fn_img_rot
c3d $fn_img_rot $fn_img_rot -reslice-matrix $fn_tform_rot -o $fn_img_rot

c3d $fn_img_rot -slice z 0:-1 -oo $WDIR_2D/img_slice%03d.nii.gz
ns=$(ls -1q $WDIR_2D/img_slice*nii.gz | wc -l)
echo "Number of slices is " $ns

vaj_lev=$(awk 'FNR == 1 {print $3}' $fn_lm_vox)
stj_lev=$(awk 'FNR == 2 {print $3}' $fn_lm_vox)
seg_lev=$(awk 'FNR == 3 {print $3}' $fn_lm_vox)

echo $stj_lev
echo $vaj_lev
echo $seg_lev

stj_lev=$(echo $stj_lev | awk '{print int($0)}')
vaj_lev=$(echo $vaj_lev | awk '{print int($0)}')
seg_lev=$(echo $seg_lev | awk '{print int($0)}')

echo $stj_lev
echo $vaj_lev
echo $seg_lev

fn_seg_2d_ref=$WDIR_2D/seg_slice${seg_lev}.nii.gz
c3d $fn_seg_rot -slice z $seg_lev -o $fn_seg_2d_ref

python $SEG_PATH/rootseg_3Dprop_bash.py $WDIR $fn_img_rot $fn_seg_2d_ref $stj_lev $vaj_lev $seg_lev $ns

RESULT_WSP=$WDIR/result.itksnap
itksnap-wt -layers-set-main $fn_img \
           -layers-set-seg $WDIR/seg_volume.nii.gz \
           -layers-add-anat $fn_img_rot \
           -o $RESULT_WSP
itksnap-wt -i $RESULT_WSP -layers-pick 001 -props-set-transform $fn_tform_rot \
           -registry-set Layers.Layer[000].LayerMetaData.DisplayMapping.SelectedComponent $sc \
           -o $RESULT_WSP
