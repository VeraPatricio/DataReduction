from mpdaf.obj import Image
import numpy as np
import matplotlib.pylab as plt
import argparse

def do_zap_mask(imname,out,sig=7):
	""" Creates the mask to be used by ZAP. Masks everyhting above sig.
	Parameters:
	-----------
	im:	str
		Image where the threshold is to be calculated
	out:	str
		Output name of the mask
	sig:	float
		Number of sigmas (relative to background levels) to be used
		to define the object/sky threshold. Default is 7
	Output:
	--------
		Image with 0 in sky and 1 in source to be use as a mask in
		ZAP
	"""
	
	
	im = Image(imname)
	bg,std = im.background()
		
	mask = im.fftconvolve_gauss(fwhm=(0.7,0.7))
	
	mask = mask > bg+sig*std
	im[np.where(mask.data.mask == False)] = 1
	im[np.where(mask.data.mask == True)] = 0
	
	plt.figure()
	mask.plot()
	plt.show()

	im.write(out)

if __name__ == "__main__":

        parser = argparse.ArgumentParser()
        parser.add_argument("imname", type=str, help = 'Image where the threshold is to be calculated')
        parser.add_argument("out", type=str, help = 'Output name of the mask')
        parser.add_argument("--sig",type=float, help = 'Number of sigmas (relative to background levels) to be used to define the object/sky threshold. Default is 7')
        args = parser.parse_args()

        if len(vars(args)) < 2:
		print('Missing arguments')
		pirnt('Usage: python do_mask.py inname out --sig')

	else:

		if args.sig:

			do_zap_mask(args.imname,args.out,sig=args.sig)
		else:
			do_zap_mask(args.imname,args.out)
	


