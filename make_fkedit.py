import numpy as np
import argparse
import os
import glob
import sys
from mpdaf.obj import Image

def make_fkedit_file(prefix_original):
	""" Calculates the offsets to be applied from the scamp output and 
	makes the corresponding fkedit file. A 'cata' folder with the 
	IMAGESX.head output is required.
	Parameters:
	----------
	prefix_original:	str
		prefix of the original images (example: IMAGE_FOV_SKYSUB_)
	Output:
	-------
		fkedit executable
	"""

	## Create auxiliary files with only the information needed
	os.system('cat cata/IMAGE*.head | grep CRVAL1 >crval1')
	os.system('cat cata/IMAGE*.head | grep CRVAL2 >crval2')

	## Read the auxiliary files (yes it's dummy to do it like this, but it's faster
	## to code...)
	fcrval1 = open('crval1','r')
	fcrval2 = open('crval2','r')

	## output the results
	f = open('dofkedit','w')
	crval1 = np.genfromtxt('crval1')
	crval1 = crval1[~np.isnan(crval1)] ## Clean from nan
	crval2 = np.genfromtxt('crval2')
	crval2 = crval2[~np.isnan(crval2)] ## Clean from nan

	imlist = glob.glob(prefix_original+'*fits')
	for i,imname in enumerate(imlist):
		im = Image(imname)
		good_ra = im.primary_header['RA']+ crval1[i] - im.data_header['CRVAL1']
		f.write('fkedit -m RA -- %s PIXTABLE_REDUCED_%s.fits\n'%(good_ra,i+1))

		good_dec = im.primary_header['DEC']+ crval2[i] - im.data_header['CRVAL2']
		if good_dec <0:
			f.write('fkedit -m DEC -- %s PIXTABLE_REDUCED_%s.fits\n'%(good_dec,i+1))
		else:
			f.write('fkedit -m DEC %s PIXTABLE_REDUCED_%s.fits\n'%(good_dec,i+1))

	f.close()
	os.system('rm crval1 crval2')
		
		


if __name__ == "__main__":

        parser = argparse.ArgumentParser()
        parser.add_argument("prefix_original", type=str, help='prefix of the original images (example: IMAGE_FOV_SKYSUB_)')
        args = parser.parse_args()

        if len(vars(args)) < 1:

                print 'Missing argument'
                print 'Usage: python make_fkedit.py prefix_original'
                sys.exit()

	else:
		
		make_fkedit_file(args.prefix_original)
