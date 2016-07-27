from mpdaf.obj import Cube,Image
import argparse
import numpy as np
import matplotlib.pylab as plt

radii = 5 ## pix

def measure_psf(im,ra,dec):
	""" Fits a gaussian and moffat 2D profile in image 'im' centered in p,q coordinates.
	of each object to be measured.
	The output values of all objects are averaged (after a sigma clipping ti get rid
	of obvious bad fits)
	Parameters:
	----------
	im: mpdaf.obj.Image	
		image where to measure the psf
	ra:	float
		array of righ ascensions of objects to be measured 
	dec:	float
		array of righ declination to be measured 
	Returns:
	--------
	fwhm,n,gfwhm
		full width half maximum of the moffat and its std deviation
		n of the moffat	 and its std
		full width half maximum of the gaussian and its std
	"""

        fwhm = []
        gfwhm = []
        n = []

	#### TESTING ####
	plt.figure()
	im.plot(zscale=True)

	if np.isscalar(dec): 
	
		## I was having some troubles with gaussian/moffat fitting using ra,dec coordinates,
        	## and since mpdaf converts it internally, I prefer to do the converstion here.
	
        	(p,q) = im.wcs.sky2pix((dec,ra))[0]

		 ## Only one star (not a great idea for real science...)
                gfit = im.gauss_fit(center=(p,q),pos_min=(p-radii,q-radii),pos_max=(p+radii,q+radii),
			circular=True,verbose=0,unit_center=None,plot=True) ## FWHM will still be outputed in arcsec
                gfwhm.append(gfit.fwhm[0])
                try:
                        fit = im.moffat_fit(center=gfit.center,pos_min=(p-radii,q-radii),pos_max=(p+radii,q+radii),
				unit_center=None,circular=True,verbose=0)
                        n.append(fit.n)
                        fwhm.append(fit.fwhm[0])
                except RuntimeWarning:
                        n.append(np.nan)
                        fwhm.append(np.nan)

	else:	
        	## Fit all the objects
        	for r,d in zip(ra,dec):
			(p,q) = im.wcs.sky2pix((d,r))[0]
                	gfit = im.gauss_fit(center=(p,q),pos_min=(p-radii,q-radii),pos_max=(p+radii,q+radii),
				unit_center=None,circular=True,verbose=0,plot=True)
               		gfwhm.append(gfit.fwhm[0])
			try:
                		fit = im.moffat_fit(center=gfit.center,pos_min=(p-radii,q-radii),pos_max=(p+radii,q+radii),
					unit_center=None,circular=True,verbose=0)
                		n.append(fit.n)
                		fwhm.append(fit.fwhm[0])
			except RuntimeWarning:
                		n.append(np.nan)
                		fwhm.append(np.nan)
		

        ## Get rid of the bad ones and make an average
        mean_gfwhm = np.nanmean(gfwhm)
        std_gfwhm = np.nanstd(gfwhm)
        mean_fwhm = np.nanmean(fwhm)
        std_fwhm = np.nanstd(fwhm)
        mean_n = np.nanmean(n)
        std_n = np.nanstd(n)
	
        return (mean_gfwhm,std_gfwhm,mean_fwhm,std_fwhm,mean_n,std_n)


if __name__ == "__main__":

        parser = argparse.ArgumentParser()
        parser.add_argument("cube", type=str, help='Cube to be measured')
        parser.add_argument("star_list",type=str, help = 'List of stars coordinates to be measured (Nb ra dec in degrees)')
        args = parser.parse_args()

        if len(vars(args)) < 2:
                print 'Missing argument'
                print 'Usage: python measure_psf.py cube star_list'
                sys.exit()

	f = open('psf_results.dat','w')
	f.write('Wavelengh (A)	Gaussian FWHM (")	Moffat n/beta (") 	Moffat fwhm (") 	Moffat alpha(")\n')
	f.write('--------------------------------------------------------------------------------------------------------\n')

	## Read star list and open output results
        id,ra,dec = np.loadtxt(args.star_list,unpack=True)
	
	## Load cube and bin 
	c = Cube(args.cube)
	c = c.rebin((2*368,1,1))
	sample_fwhm = []
	sample_gfwhm= []
	sample_n = []
	sample_alpha = []
	white = c.sum(axis=0)
	(gfwhm,std_gfwhm,fwhm,std_fwhm,n,std_n) = measure_psf(white,ra,dec)
	alpha = fwhm / (2 *np.sqrt(2 * (1/n) - 1))
        err_alpha = std_fwhm / (2 *np.sqrt(2 * (1/n) - 1)) + std_n * fwhm / (2 * np.sqrt(2/n- n*n))
                        ## ugly derivative with Wolfram Alpha
	f.write('white light \t %0.2f +/- %0.2f \t %0.2f +/- %0.2f \t %0.2f +/- %0.2f \t %0.2f +/- %0.2f \n'
                        %(gfwhm,std_gfwhm,n,std_n,fwhm,std_fwhm, alpha,err_alpha))
	f.write('--------------------------------------------------------------------------------------------------------\n')
		
	for k in range(0,c.shape[0]):
		print('Measusing %s out of 5 slices'%k)
		im = c[k]
		im.wcs = c.wcs ## Not elegant, but the wcs is not keept when you only select one slice
		(gfwhm,std_gfwhm,fwhm,std_fwhm,n,std_n) = measure_psf(im,ra,dec)
		
		## Convert mpdaf fwhm in proper moffat parameters
        	## https://en.wikipedia.org/wiki/Moffat_distribution
        	## n == beta
        	## alpha = fwhm / (2 * sqrt (2 ** (1/n) -1))
       	 	alpha = fwhm / (2 *np.sqrt(2 * (1/n) - 1))
        	err_alpha = std_fwhm / (2 *np.sqrt(2 * (1/n) - 1)) + std_n * fwhm / (2 * np.sqrt(2/n- n*n)) 

		f.write('%d \t %0.2f +/- %0.2f \t %0.2f +/- %0.2f \t %0.2f +/- %0.2f \t %0.2f +/- %0.2f \n'
			%(c.wave.coord(k),gfwhm,std_gfwhm,n,std_n,fwhm,std_fwhm, alpha,err_alpha))
		
		## Keep the values to calculate mean and error
		sample_fwhm.append(fwhm)
		sample_gfwhm.append(gfwhm)
		sample_n.append(n)
		sample_alpha.append(alpha)

	print('Finished slices loop')
		
	f.write('--------------------------------------------------------------------------------------------------------\n')
	sqrt_nb = np.sqrt(len(sample_fwhm))
	f.write('mean \t %0.2f +/- %0.2f \t %0.2f +/- %0.2f \t %0.2f +/- %0.2f \t %0.2f +/- %0.2f \n'
			%(np.mean(sample_gfwhm),np.std(sample_gfwhm)/sqrt_nb,
			  np.mean(sample_n),np.std(sample_n)/sqrt_nb,
			  np.mean(sample_fwhm),np.std(sample_fwhm)/sqrt_nb,
			  np.mean(sample_alpha),np.std(sample_alpha)/sqrt_nb))

	f.close()	


