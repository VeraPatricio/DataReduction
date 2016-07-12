from mpdaf.obj import Cube,Image,iter_ima
import numpy as np
import multiprocessing

c=Cube('DATACUBE_MACS0416_ZAP_26Jan_MAD_ZAP_median_GOOD_VAR.fits')
#immask=Image('MASK_ZAP_MACS0416_ext1_24Aug.fits')
immask=Image('MASKINV.fits')

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


c2.write('DATACUBE_MACS0416_ZAP_26Jan_MAD_ZAP_median_GOOD_VAR_rowcol.fits')
