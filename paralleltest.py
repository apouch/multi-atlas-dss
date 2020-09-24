#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 22 15:16:04 2020

@author: alison
"""
import multiprocessing 
import time 
  
  '''
class Process(multiprocessing.Process): 
    def __init__(self, id): 
        super(Process, self).__init__() 
        self.id = id
                 
    def run(self): 
        time.sleep(1) 
        print("I'm the process with id: {}".format(self.id)) 
  
if __name__ == '__main__': 
    p = Process(0) 
    p.start() 
    p.join() 
    p = Process(1) 
    p.start() 
    p.join() 
    print("Number of processors: ", multiprocessing.cpu_count())
    '''

def worker(num):
    """thread worker function"""
    print 'Worker:', num
    return

if __name__ == '__main__':
    jobs = []
    for i in range(5):
        p = multiprocessing.Process(target=worker, args=(i,))
        jobs.append(p)
        p.start()
        
 '''       
pool = mp.Pool(mp.cpu_count())
print("Number of processors: ", mp.cpu_count())
results = [pool.apply(atlas_reg, 
          args = (i, WDIR, fn_img_targ, coords_targ, atlas_set))
            for i in range(0,len(atlas_set))]
pool.close()


jobs = []
for i in range(0,len(atlas_set)):   
p = mp.Process(target=atlas_reg, args=(i,WDIR, fn_img_targ, coords_targ, atlas_set))
jobs.append(p)
p.start()
'''