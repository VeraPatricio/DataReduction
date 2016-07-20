import numpy as np
import matplotlib 
matplotlib.use('Agg')
from mpdaf.obj import Cube,Image,Spectrum
import matplotlib.pylab as plt
from astropy import table 
import argparse
import datetime
#import subprocess
#import shlex
import os
import sys
import glob

readout = datetime.timedelta(seconds=60)

def mad(arr):
    """ Median Absolute Deviation: a "Robust" version of standard deviation.
        Indices variabililty of the sample.
        https:/en.wikipedia.org/wiki/Median_absolute_deviation 
    """
    arr = np.ma.array(arr).compressed() # should be faster to not use masked arrays.
    med = np.median(arr)

    return np.median(np.abs(arr - med))


def imlevels(imname,ZAPmask):	
	""" Calculates the background, and corresponding standard deviation,
	of an image. To be used in the colorbars.
	Parameters
	----------
	imname: string
		path to image
	ZAPmask: mpdaf.obj.Image
		mask with strong emission masked
	Returns
	----------
	lmin, lmax: (float,float)
		min and maximum levels to be aplied to a colorbar
	"""

	im = Image(imname)

	if ZAPmask != None:

        	mask_pix = np.where(ZAPmask.data.data == 0)
       		unmask_pix = np.where(ZAPmask.data.data == 1)
	       	im.data.mask[mask_pix] = True
        	bg_std = mad(im.data.data[unmask_pix])

	else:

		bg_std = mad(im.data.data)

        bg_mean = np.ma.mean(im.data)
        im.unmask()
	lmin = bg_mean-5*bg_std
	lmax = bg_mean+5*bg_std

	return (lmin,lmax)

def makefits(cube,name):
	""" Takes a cube and procuces some images and spectra in order to quicky accesss
	data quality:
		--- white light: sum all cube
		--- Median band images : (4755,5755),(5755,6755),(6755,7755),(7755,8755),(8755,9345)
		--- Narrow band images: (6297.33,7319,8399,8781.08,8916.08,9348)
		--- BGC spectra: spectra of the brighests object in the center of the cube
		--- BG spectra: spectra of an empty box of 10X10 pixels
	Parameters
	-----------
	cube: mpdaf.obj.cube
		data cube where images and spectra are going to be extracted
	name: string
		prefix to be added to the extrated images/spectra
	Output
	-----
		white light, median and narrow band images, BGC and backgound spectra
	"""

	dir = 'DataQuality/'
	if os.path.isdir(dir):
		print 'Folder already exits. Stuff may be overwritten'
	#	sys.exit()
	else:
		os.makedirs(dir)
		
        # White light
        white = cube.mean(axis=0)
        white.write(dir+name+'_white_image.fits')

        # Medium band images
        limMB = ((4755,5755),(5755,6755),(6755,7755),(7755,8755),(8755,9345))
        for l in range(len(limMB)):

                im  = cube.get_lambda(limMB[l][0],limMB[l][1]).mean(axis=0)
                im.write(dir+name+'_MB_'+str(limMB[l][0])+'_'+str(limMB[l][1])+'.fits')
	
        # Narrow band images
        limNB = (6297.33,7319,8399,8781.08,8916.08,9348)
        for l in range(len(limNB)):

                im = cube[int(cube.wave.pixel(limNB[l])),:,:]
                im.write(dir+name+'_NB_'+str(int(limNB[l]))+'.fits')

	# BCG spectrum
	smooth = white.gaussian_filter(5)
	max_p,max_q = np.where(smooth.data.data == np.max(smooth.data.data[100:200,100:200]))
	sp_CM = cube[:,max_p-3:max_p+3,max_q-3:max_q+3].sum(axis=(1,2))
	sp_CM.write(dir+name+'_CM_sp.fits')

	# Background spectra
	bg,std = white.background()
	mask_bg = smooth < (bg + std)
	## Sort of dumb: go though the cube until find a a pixel with all neighbours unmasked
	stop = False
	for p in range(50,cube.shape[0]-50):
		if stop == True:
			break
		for q in range(50, cube.shape[1]-50): 
			if not np.all(mask_bg[p-5:p+5,q-5:q+5].data.mask):
				sp = cube[:,p-5:p+5,q-5:q+5].sum(axis=(1,2))
				sp.write(dir+name+'_BG_sp.fits')
				stop = True
				break


def makepdf(imname,lmin=None,lmax=None):	
	""" Takes an image, opens it, plots it with an colorbar and saves
	the images as a pdf.
	Parameters
	----------
	imname: string
		image to be open
	lmin: float
		minimum level of the colorbar
	lmax: float
		max level of the colorbar
	Output
	---------
	pdf image
	
	"""

	im = Image(imname)
	plt.figure()
	im.plot(vmin=lmin,vmax=lmax,colorbar='v')
	plt.savefig(im.filename[:-5]+'.pdf')


if __name__ == "__main__":
	    
	parser = argparse.ArgumentParser()
	parser.add_argument("inputlist", type=str, help = 'List with cube paths and respective prefixes to be used in the output images')
	parser.add_argument("--images", help = 'Produces the White light, Narrow band and Median band images (fits file)')
	parser.add_argument("--compare", help = 'Produces a pdf with side-by-side images of the cubes. REQUIRES MASK ARGUMENT')
	parser.add_argument("--mask",help = 'Mask to be used to estimate the image levels (same as ZAP mask)')
	args = parser.parse_args()

	if len(vars(args)) < 2:

        	print 'Missing argument'
        	print 'Usage: reduction_log.py inputlist --images --compare --mask \n where list is contains cube_path  and output_name (TAB SEPARATED!)'
        	sys.exit()	

	now = datetime.datetime.now()
    	date = now.strftime("%Y-%m-%d")
	inputlist = args.inputlist
	t = table.Table.read(inputlist,format='ascii')

	if args.images:

        	for (cube_path,folder) in zip(t['cube_path'],t['output_name']):

                	print 'Reading',cube_path
                	cube = Cube(cube_path)
               		makefits(cube,folder)

	if args.compare:
	
		if args.mask:
			ZAPmask = None
			try:
				ZAPmask = Image(args.mask)
			except:
				print 'Mask '+args.mask +' not found'
	    
    		prefix=[]
    		sufixnb=[]
    		sufixmb=[]
   		sufixwhite=[]

                mpagesize=max(int(18.0/len(t['output_name'])),10)

		##Search for files
		for p in t['output_name']:

        		print "Searching for prefix "+p

			foundfiles = glob.glob('DataQuality/'+p+"*.fits")
			
			#Order by date (to be ordered in wavelenght)
			foundfiles.sort(key=os.path.getmtime) 

        		prefix.append(p)
        		for filename in foundfiles:
				
            			if 'NB' in filename:
                 			sufixnb.append(filename.split('NB_')[-1].strip('.fits'))
            			if 'MB' in filename:
                 			sufixmb.append(filename.split('MB_')[-1].strip('.fits'))
            			if 'white' in filename:
                 			sufixwhite.append('white_image')

    			sufixnb=np.unique(sufixnb).tolist()
    			sufixmn=np.unique(sufixmb).tolist()
    			sufixwhite=np.unique(sufixwhite).tolist()

    			print "Images found:"
    			print "Narrow-band: "+str(np.unique(sufixnb))
    			print "Median-band: "+str(np.unique(sufixmb))
    			print "White light: "+str(np.unique(sufixwhite))



		## Make pdf file
		title="Reduction comparison %s"%date
        	# create document
    		content = r'''
\documentclass[10pt, oneside]{scrartcl}
\usepackage[a4paper, margin=1cm]{geometry}
\usepackage[parfill]{parskip}
\usepackage{graphicx}
\title{%s}
\date{}
\let\footnote=\endnote
\begin{document}
\maketitle

'''%(title)

		if(len(sufixwhite)>0):
                        
			(lmin,lmax)=imlevels('DataQuality/'+p+'_'+sufixwhite[0]+'.fits',ZAPmask)
			for w in sufixwhite:
			        content+=r'''

White light image:%s\

'''%(w.replace("_"," "))
         			for p in prefix:
              				
					pdfname='DataQuality/'+p+'_'+w+'.pdf'
					makepdf('DataQuality/'+p+'_'+w+'.fits',lmin=lmin,lmax=lmax)
					content+=r'''\begin{minipage}{%dcm}
\begin{center}
%s
\end{center}

\includegraphics[width=%dcm]{%s}
\end{minipage}
'''%(mpagesize,p.replace("_"," "),mpagesize,pdfname)

	    	if(len(sufixmb)>0):
       	
			(lmin,lmax)=imlevels('DataQuality/'+p+'_MB_'+sufixmb[0]+'.fits',ZAPmask)		
			for m in sufixmb:
				content+=r'''

Median band image:%s \AA\ 

'''%(m.replace("_"," "))
	       		 	for p in prefix:
        		      		
					pdfname='DataQuality/'+p+'_MB_'+m+'.pdf'
					makepdf('DataQuality/'+p+'_MB_'+m+'.fits',lmin=lmin,lmax=lmax)
					content+=r'''\begin{minipage}{%dcm}
\begin{center}
%s
\end{center}

\includegraphics[width=%dcm]{%s}
\end{minipage}
'''%(mpagesize,p.replace("_"," "),mpagesize,pdfname)

		if(len(sufixnb)>0):

			(lmin,lmax)=imlevels('DataQuality/'+p+'_NB_'+sufixnb[0]+'.fits',ZAPmask)
       
			for n in sufixnb:
				content+=r'''
Narrow band image:%s \AA\ 

'''%(n.replace("_"," "))
         			for p in prefix:
              
					pdfname='DataQuality/'+p+'_NB_'+n+'.pdf'
					makepdf('DataQuality/'+p+'_NB_'+n+'.fits',lmin=lmin,lmax=lmax)
					content+=r'''\begin{minipage}{%dcm}
\begin{center}
%s
\end{center}

\includegraphics[width=%dcm]{%s}
\end{minipage}
'''%(mpagesize,p.replace("_"," "),mpagesize,pdfname)
	
		plt.figure()
	
		for p in prefix:

			spname = 'DataQuality/'+p+'_CM_sp.fits'
			print 'opening',spname
        		sp = Spectrum(spname)
       			sp.plot(label = p) 

		plt.legend()
	        plt.savefig('DataQuality/BCG_spectra.pdf')
		plt.figure()
		
		for p in prefix:

                        spname = 'DataQuality/'+p+'_CM_sp.fits'
                        sp = Spectrum(spname)
                        sp.plot(lmin=7500,lmax=9000,label = p)

		plt.legend()
	        plt.savefig('DataQuality/BCG_spectra_zoom.pdf')
		content += r'''

BCG Spectra

\begin{center}
\includegraphics[width=20cm]{DataQuality/BCG_spectra.pdf}

\includegraphics[width=20cm]{DataQuality/BCG_spectra_zoom.pdf}
\end{center}
'''#%(mpagesize,p.replace("_"," "),mpagesize,pdfname)

                plt.figure()

                for p in prefix:

                        spname = 'DataQuality/'+p+'_BG_sp.fits'
                        sp = Spectrum(spname)
                        sp.plot(label = p)

                plt.legend()
                plt.savefig('DataQuality/Background_spectra.pdf')
                plt.figure()

                for p in prefix:

                        spname = 'DataQuality/'+p+'_BG_sp.fits'
                        sp = Spectrum(spname)
                        sp.plot(lmin=7500,lmax=9000,label = p)

                plt.legend()
                plt.savefig('DataQuality/Background_spectra_zoom.pdf')
                content += r'''

Backgound Spectra

\begin{center}
\includegraphics[width=20cm]{DataQuality/Background_spectra.pdf}

\includegraphics[width=20cm]{DataQuality/Background_spectra_zoom.pdf}
\end{center}

\end{document}
'''
		## Compile .tex file
		with open('Reduction.tex','w') as f:
			f.write(content)
		f.close()

		os.system('pdflatex Reduction.tex')
		## Clean up auxiliary files
		os.remove('Reduction.log')
		os.remove('Reduction.tex')
		os.remove('Reduction.aux')
		pdffiles = glob.glob('DataQuality/*pdf')
		for f in pdffiles:
    			os.remove(f)
