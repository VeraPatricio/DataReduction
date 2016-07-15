from mpdaf.obj import Cube,Image,iter_ima
import numpy as np
import multiprocessing

def remove_bg(cube_in,mask,cube_out):
	""" Corrects background of a cube to zero (per wavelengh plane)
	Strong emission (e.g. cluster members) should be masked.
	Parameters:
	----------
	cube_in: string
		path to input cube to be corrected
	mask:	 string
		path to mask to be used
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
	c.data.mask[:, mask] = True

	for k in range(c.shape[0]):
    		print k," out of ",c.shape[0]
    		posmin=max(k-25,0)
    		posmax=min(c.shape[0],k+25)
   		for p in range(c.shape[1]):
        		med=np.ma.median(c.data[posmin:posmax,p,:])
        		c2.data.data[k,p,:]-=med
    		for q in range(c.shape[2]):
        		med=np.ma.median(c.data[posmin:posmax,:,q])
        		c2.data.data[k,:,q]-=med

	## Update Header
	c2.primary_header.add_comment('This cube as been median subtracted.')

	c2.write(cubeout)
	
	return c2
