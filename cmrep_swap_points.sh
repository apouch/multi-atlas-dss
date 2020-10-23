#!/bin/bash
set -x

file_fit=$1
file_tmpl=$2
file_out=$3

cp $file_tmpl $file_out

ed ${file_out}<<EOF
/^POINTS
+,/^POLYGONS/-1d
-r !sed -n '1,/^POINTS/d;/^POLYGONS/q;p' ${file_fit}|grep -v '^#'
w
q
EOF



