#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script defines an optimization of a similarity transform between two sets
of landmarks.

"""

import numpy as np
from scipy.optimize import minimize

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