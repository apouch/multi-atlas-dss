#!/bin/bash

fnprefix=$1
fnout=${fnprefix}_param.txt

printf '%s' '# IMAGE MATCH

DefaultParameters.ImageMatch = VolumeOverlap
DefaultParameters.nLabels = 1

# INEQUALITY CONSTRAINTS

DefaultParameters.BoundaryJacobianEnergyTerm.Weight = 0.001
DefaultParameters.BoundaryJacobianEnergyTerm.PenaltyA = 20
DefaultParameters.BoundaryJacobianEnergyTerm.PenaltyB = 10
DefaultParameters.LoopTangentSchemeValidityPenaltyTerm.Weight = 0.01
DefaultParameters.BoundaryGradRPenaltyTerm.Weight = 5.0
DefaultParameters.RadiusPenaltyTerm.Weight = 0.000001
DefaultParameters.RadiusPenaltyTerm.UpperBound = 2.0 #15.0
DefaultParameters.RadiusPenaltyTerm.UpperScale = 1.0
DefaultParameters.RadiusPenaltyTerm.LowerBound = 0.1 #2.0
DefaultParameters.RadiusPenaltyTerm.LowerScale = 1.0
DefaultParameters.DiffeomorphicEnergyTerm.Weight = 1.0 #100 

# REGULARIZATION

DefaultParameters.MedialEdgeSmoothnessEnergyTerm.Weight = 1.0 #0.001
DefaultParameters.MedialEdgeSmoothnessEnergyTerm.Penalty1 = 0.0 #20 #200
DefaultParameters.MedialEdgeSmoothnessEnergyTerm.Penalty2 = 0.0 #2.0 #0.02
DefaultParameters.MedialEdgeSmoothnessEnergyTerm.Penalty3 = 1.0 #1.0
DefaultParameters.MedialEdgeSmoothnessEnergyTerm.MedialEdges = /home/apouch/CMREP_TEMPLATES/medialtemplate_closed2_annulus.txt
DefaultParameters.BoundaryAnglesPenaltyTerm.Weight = 0.00
DefaultParameters.MedialTriangleAnglePenaltyTerm.Weight = 0.0
DefaultParameters.BoundaryCurvaturePenaltyTerm.Weight = 0.0
DefaultParameters.BoundaryTriangleAreaPenaltyTerm.Weight = 0.0001
DefaultParameters.MedialJacobianDistortionPenaltyTerm.Weight = 0.0
DefaultParameters.MedialJacobianDistortionPenaltyTerm.ReferenceModel = '${fnprefix}'.cmrep

# OPTIMIZATION STAGES
Stage.ArraySize = 1

# First deformable stage
Stage.Element[0].Name = '${fnprefix##*/}'_def0
Stage.Element[0].Mode = FitToBinary
Stage.Element[0].Blur = 0.1
Stage.Element[0].MaxIterations = 150
Stage.Element[0].Refinement.Subdivision.Controls = 0
Stage.Element[0].Refinement.Subdivision.Atoms = 0' > $fnout

