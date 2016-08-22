import numpy as np
import argparse
import os
import glob
import sys
import re
from mpdaf.obj import Image

def make_fkedit_file(prefix):
	""" Calculates the offsets to be applied from the scamp output and 
	makes the corresponding fkedit file. A 'cata' folder with the 
	IMAGESX.head output is required. It assumes that prefix_X.fits --> IMAGE_X.head
	Parameters:
	----------
	prefix:	str
		prefix of the original images (example: IMAGE_FOV_SKYSUB_)
	Output:
	-------
		fkedit executable
	"""

	## Create auxiliary files with only the information needed
	os.system('ls  cata/IMAGE*head | grep -o "[0-9]*" > image_order')
	os.system('cat cata/IMAGE*.head | grep CRVAL1 >crval1')
	os.system('cat cata/IMAGE*.head | grep CRVAL2 >crval2')

	## output the results
	f = open('dofkedit','w')
	image_number = np.loadtxt('image_order')
	crval1 = np.genfromtxt('crval1')
	crval1 = crval1[~np.isnan(crval1)] ## Clean from nan
	crval2 = np.genfromtxt('crval2')
	crval2 = crval2[~np.isnan(crval2)] ## Clean from nan

	for i,im_nb in enumerate(image_number):
		im = Image(prefix+str(int(im_nb))+'.fits')
		good_ra = im.primary_header['RA']+ crval1[i] - im.data_header['CRVAL1']
		f.write('fkedit -m RA -- %s PIXTABLE_REDUCED_%s.fits\n'%(good_ra,i+1))

		good_dec = im.primary_header['DEC']+ crval2[i] - im.data_header['CRVAL2']
		if good_dec <0:
			f.write('fkedit -m DEC -- %s PIXTABLE_REDUCED_%s.fits\n'%(good_dec,i+1))
		else:
			f.write('fkedit -m DEC %s PIXTABLE_REDUCED_%s.fits\n'%(good_dec,i+1))

	f.close()
	os.system('rm crval1 crval2 image_order')
		
		
if __name__ == "__main__":

        parser = argparse.ArgumentParser()
        parser.add_argument("prefix", type=str, help='prefix of the original images (example: IMAGE_FOV_SKYSUB_)')
        args = parser.parse_args()

        if len(vars(args)) < 1:

                print 'Missing argument'
                print 'Usage: python make_fkedit.py prefix'
                sys.exit()

	else:
		
		make_fkedit_file(args.prefix)
