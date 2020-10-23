#!/bin/bash

fnprefix=$1
fnout=${fnprefix}.cmrep

printf '%s' 'Grid.Type = LoopSubdivision
Grid.Model.SolverType = BruteForce
Grid.Model.Atom.SubdivisionLevel = 2
Grid.Model.Coefficient.FileName = '${fnprefix##*/}'.vtk
Grid.Model.Coefficient.FileType = VTK
Grid.Model.nLabels = 1' > $fnout
