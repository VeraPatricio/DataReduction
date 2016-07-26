from mpdaf.obj import Cube,Image,iter_ima
import numpy as np
from multiprocessing import Process
from multiprocessing import Pool
from multiprocessing import Array
import multiprocessing as mtp
import argparse
import time

def rm_bg_multiproc(k,cube_in,dummy_im,return_dict):
	
        posmin=max(k-25,0)
        posmax=min(c.shape[0],k+25)
        for p in range(c.shape[1]):
        	med=np.ma.median(c.data[posmin:posmax,p,:])
                dummy_im.data.data[p,:]+=med
        for q in range(c.shape[2]):
                med=np.ma.median(c.data[posmin:posmax,:,q])
         	dummy_im.data.data[:,q]+=med

	return_dict[k] = dummy_im.data.data[:,:]

def dummy_function(i):
	return rm_bg_multiproc(i,c,dummy_im,return_dict)


def remove_bg(cube_in,mask,cube_out):
	""" Corrects background of a cube to zero (per wavelengh plane)
	Strong emission (e.g. cluster members) should be masked.
	Parameters:
	----------
	cube_in: string
		path to input cube to be corrected
	mask:	 string
		path to mask to be used. Image with 0 for masked regions and 1 for regions
		to be used to calculate the meadian background (old version of ZAP).
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
        parser.add_argument("mask",type=str, help = 'path to mask to be used. Image with 1 for \									masked regions and 0 for regions to be used to calculate the meadian background (same as ZAP)')
        parser.add_argument("cube_out", type=str, help = 'path to the output (corrected) cube')
        args = parser.parse_args()
	
        if len(vars(args)) < 3:

                print 'Missing argument'
                print 'Usage: python rowcol.py cube_in mask cube_out'
                sys.exit()

	
	else:

		print('Using multiprocessing')	
		c=Cube(args.cube_in)
        	immask = Image(args.mask)

        	mask = immask.data.astype(bool)
        	mask_inv = np.invert(mask)
        	c.data.mask[:, mask_inv] = True
		
		manager = mtp.Manager()
        	return_dict = manager.dict()
	
		tstart = time.time()
		#pool = Pool(processes=20)
		#pool.map(dummy_function, range(c.shape[0]))     
		dummy_im = c[0,:,:]	
		dummy_im.data.data[:,:] = 0
		
                for i in range(0,c.shape[0]):   
                        p = Process(target=rm_bg_multiproc, args=(i,c,dummy_im,return_dict))
			p.start()

		tend = time.time()
                print('ellapsed time %s'%(tend-tstart))

		c.unmask()
		for k in range(c.shape[0]):
			c.data.data[k,:,:] = c.data.data[k,:,:] - return_dict[k]

		## Update Header
        	c.primary_header.add_comment('This cube has been median subtracted')
		c.write(args.cube_out)

	#if args.multip == 0:

	#	remove_bg(args.cube_in,args.mask,args.cube_out)


