import numpy as np
import matplotlib 
matplotlib.use('Agg')
from mpdaf.obj import Cube,Image,Spectrum
import matplotlib.pylab as plt
from astropy import table 
import argparse
import datetime
import subprocess
import shlex
import os, sys
import numpy as np
import glob
from os.path import expanduser  


def mad(arr):
    """ Median Absolute Deviation: a "Robust" version of standard deviation.
        Indices variabililty of the sample.
        https://en.wikipedia.org/wiki/Median_absolute_deviation 
    """
    arr = np.ma.array(arr).compressed() # should be faster to not use masked arrays.

    med = np.median(arr)

    return np.median(np.abs(arr - med))

readout = datetime.timedelta(seconds=60)

def imlevels(imname,ZAPmask):	

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

	if os.path.isdir('/data/vera/DataQuality/'+name):

		print 'Folder already exits. Change it or the name of the output'

		sys.exit()
	else:
		dir = '/data/vera/DataQuality/'+name

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

	# Background spectra

	sp = cube[:,59:83,119:139].mean(axis=(1,2))

	sp.write(dir+name+'_SP.fits')


def makepdf(imname,lmin=None,lmax=None):	

	im = Image(imname)

	plt.figure()

	im.plot(vmin=lmin,vmax=lmax,colorbar='v')
	
	plt.savefig(im.filename[:-5]+'.pdf')

def sizeof_fmt(num):
    for x in ['bytes','KB','MB','GB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')

def time_fmt(num):
    for x in ['s','m']:
        if num<60:
            return "%3.1f%s" % (num, x)
        num /= 60.0
    return "%3.1f%s" % (num, 'h')



if __name__ == "__main__":
    
    # Parse the arguments
#parser = optparse.OptionParser(usage="%reduction_log.py inputlist")
#    parser.add_option("-n", "--noupload", dest="noupload", action="store_true", default=False, 
#                      help="do not upload comments for musewise")
#    parser.add_option("-t", "--notexdelete", dest="notexdelete", action="store_true", help="do not delete tex file")
#(options, args) = parser.parse_args()

	parser = argparse.ArgumentParser()
	
	parser.add_argument("inputlist", type=str, help = 'List with cube paths and respective prefixes to be used in the output images')

	parser.add_argument("--images", help = 'Produces the White light, Narrow band and Median band images (fits file)')

	parser.add_argument("--compare", help = 'Produces a pdf with side-by-side images of the cubes. REQUIRES MASK ARGUMENT')

	parser.add_argument("--mask",help = 'Mask to be used to estimate the image levels (same as ZAP mask)')
	
	args = parser.parse_args()

	if len(vars(args)) < 2:

        	print 'Missing argument'

        	print 'Usage: reduction_log.py inputlist --images --compare --mask \n where list is contains cube_path  and output_name'

        	sys.exit()	

	now = datetime.datetime.now()

    	date = now.strftime("%Y-%m-%d")

	inputlist = args.inputlist

	t = table.Table.read(inputlist,format='ascii')

	if args.images:

        	for (cube_path,prefix) in zip(t['cube_path'],t['output_name']):

                	print 'Reading',cube_path

                	cube = Cube(cube_path)

               		makefits(cube,prefix)

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

                mpagesize=max(int(20.0/len(t['output_name'])),10)

        else:
 		dir = '/data/vera/DataQuality/'+name

                print 'Searching for sub-folder '+dir +' in DataQuality folder'

                if os.path.isdir(dir):

                        print 'Folder already exits! Hurray!'

                else:

                        print 'Sorry, folder not found!'
                        
                        sys.exit()


		for p in t['output_name']:

        		print "Searching for prefix "+p

			searchedfiles = glob.glob(p+"*.fits")
			
			#Order by date (to be ordered in wavelenght)
			searchedfiles.sort(key=os.path.getmtime) 

        		prefix.append(p)
        		for filename in searchedfiles:

            			sufix=filename[len(p):-5]
	            		if(sufix[0]=='_'):
        	      			sufix=sufix[1:]
            			if(sufix[0:2]=='NB'):
                 			sufixnb.append(sufix[3:])
            			if(sufix[0:2]=='MB'):
                 			sufixmb.append(sufix[3:])
            			if(sufix[0:5]=='white'):
                 			sufixwhite.append(sufix)

    			sufixnb=np.unique(sufixnb).tolist()
    			sufixmn=np.unique(sufixmb).tolist()
    			sufixwhite=np.unique(sufixwhite).tolist()
    			print "Images found:"
    			print "Narrow-band: "+str(np.unique(sufixnb))
    			print "Median-band: "+str(np.unique(sufixmb))
    			print "White light: "+str(np.unique(sufixwhite))


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
                        
			(lmin,lmax)=imlevels(p+'_'+sufixwhite[0]+'.fits',ZAPmask)

			print lmin,lmax
       			
			for w in sufixwhite:
         
			        content+=r'''


White light image:%s

'''%(w.replace("_"," "))
         			for p in prefix:
              				
					pdfname=p+'_'+w+'.pdf'
					
					makepdf(p+'_'+w+'.fits',lmin=lmin,lmax=lmax)
              		
					content+=r'''\begin{minipage}{%dcm}
\begin{center}
%s
\end{center}

\includegraphics[width=%dcm]{%s}
\end{minipage}
'''%(mpagesize,p.replace("_"," "),mpagesize,pdfname)


	    	if(len(sufixmb)>0):
       	
			(lmin,lmax)=imlevels(p+'_MB_'+sufixmb[0]+'.fits',ZAPmask)		

			for m in sufixmb:
         	
				content+=r'''

Median band image:%s \AA\ 

'''%(m.replace("_"," "))

	       		 	for p in prefix:
        		      		
					pdfname=p+'_MB_'+m+'.pdf'

					makepdf(p+'_MB_'+m+'.fits',lmin=lmin,lmax=lmax)
              				
					content+=r'''\begin{minipage}{%dcm}
\begin{center}
%s
\end{center}

\includegraphics[width=%dcm]{%s}
\end{minipage}
'''%(mpagesize,p.replace("_"," "),mpagesize,pdfname)

		if(len(sufixnb)>0):

			(lmin,lmax)=imlevels(p+'_NB_'+sufixnb[0]+'.fits',ZAPmask)
       
			for n in sufixnb:
         			
				content+=r'''
Narrow band image:%s \AA\ 

'''%(n.replace("_"," "))
         			for p in prefix:
              
					pdfname=p+'_NB_'+n+'.pdf'

					makepdf(p+'_NB_'+n+'.fits',lmin=lmin,lmax=lmax)

					content+=r'''\begin{minipage}{%dcm}
\begin{center}
%s
\end{center}

\includegraphics[width=%dcm]{%s}
\end{minipage}
'''%(mpagesize,p.replace("_"," "),mpagesize,pdfname)
	
		plt.figure()
	
		for p in prefix:

			spname = p+'_SP.fits'

        		sp = Spectrum(spname)
        
       			sp.plot(label = p) 

		plt.legend()

	        plt.savefig('All_spectra.pdf')
		
		plt.figure()
		
		for p in prefix:

                        spname = p+'_SP.fits'

                        sp = Spectrum(spname)

                        sp.plot(lmin=7500,lmax=9000,label = p)

		plt.legend()

	        plt.savefig('All_spectra_zoom.pdf')

		content += r'''

BACKGROUND SPECTRUM

\begin{center}
\includegraphics[width=20cm]{All_spectra.pdf}

\includegraphics[width=20cm]{All_spectra_zoom.pdf}
\end{center}

\end{document}
'''
		with open('Reduction.tex','w') as f:
        
			f.write(content)
    	
			for i in range(1):
        
				proc=subprocess.Popen(shlex.split('pdflatex Reduction.tex'))
        
				#proc.communicate()
    	
			f.close()

