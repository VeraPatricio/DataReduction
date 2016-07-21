from mpdaf.obj import Cube,Image,iter_ima
import numpy as np
from multiprocessing import Process
#from multiprocessing import Pool
import argparse
import time

def rm_bg_multiproc(k,cube_in,cube_out):

        posmin=max(k-25,0)
        posmax=min(c.shape[0],k+25)
        for p in range(c.shape[1]):
        	med=np.ma.median(c.data[posmin:posmax,p,:])
                c2.data.data[k,p,:]-=med
        for q in range(c.shape[2]):
                med=np.ma.median(c.data[posmin:posmax,:,q])
         	c2.data.data[k,:,q]-=med

def dummy_function(i):
	return rm_bg_multiproc(i,c,c2)


def remove_bg(cube_in,mask,cube_out):
	""" Corrects background of a cube to zero (per wavelengh plane)
	Strong emission (e.g. cluster members) should be masked.
	Parameters:
	----------
	cube_in: string
		path to input cube to be corrected
	mask:	 string
		path to mask to be used. Image with 1 for masked regions and 0 for regions
		to be used to calculate the meadian background (same as ZAP).
	cube_out: string
		path to the output (corrected) cube
	Returns:
	----------
	mpdaf.obj.Cube 
		corrected cube
	"""

	c=Cube(cube_in)
	immask = Image(mask)

	c2=c.copy()
	mask = immask.data.astype(bool)
	mask_inv = np.invert(mask)
	c.data.mask[:, mask_inv] = True

	tstart = time.time()
	for k in range(c.shape[0]):
		posmin=max(k-25,0)
    		posmax=min(c.shape[0],k+25)
   		for p in range(c.shape[1]):
        		med=np.ma.median(c.data[posmin:posmax,p,:])
        		c2.data.data[k,p,:]-=med
    		for q in range(c.shape[2]):
        		med=np.ma.median(c.data[posmin:posmax,:,q])
        		c2.data.data[k,:,q]-=med
	tend = time.time()
        print('ellapsed time %s'%(tend-tstart))

	## Update Header
	c2.primary_header.add_comment('This cube has been median subtracted')
	c2.write(cube_out)
	
	return c2

if __name__ == "__main__":

        parser = argparse.ArgumentParser()
        parser.add_argument("cube_in", type=str, help='path to input cube to be corrected')
        parser.add_argument("mask",type=str, help = 'path to mask to be used')
        parser.add_argument("cube_out", type=str, help = 'path to the output (corrected) cube')
	parser.add_argument("multip",type=int,help='Uses python multiprocessing (1) or not (0)')
        args = parser.parse_args()
	
        if len(vars(args)) < 4:

                print 'Missing argument'
                print 'Usage: python rowcol.py cube_in mask cube_out multip'
                sys.exit()

	
	if args.multip == 1:

		print('Using multiprocessing')	
		c=Cube(args.cube_in)
        	immask = Image(args.mask)

        	c2=c.copy()
        	mask = immask.data.astype(bool)
        	mask_inv = np.invert(mask)
        	c.data.mask[:, mask_inv] = True
	
		tstart = time.time()
		#pool = Pool(processes=4)
		#pool.map(dummy_function, range(c.shape[0]))     
                for i in range(0,c.shape[0]):   
                        p = Process(target=rm_bg_multiproc, args=(i,c,c2))
                        p.start()

		tend = time.time()
                print('ellapsed time %s'%(tend-tstart))

		## Update Header
        	c2.primary_header.add_comment('This cube has been median subtracted')
		c2.write(args.cube_out)

	if args.multip == 0:

		remove_bg(args.cube_in,args.mask,args.cube_out)

	else:
		print '1 or 0 for multip option'


