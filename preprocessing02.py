import numpy as np
from astropy import units as u
from astropy.io import fits
import ccdproc

def combineBias(biaslist):
    """Combine all the bias files into a master bias"""
    ccdlist = [ccdproc.CCDData.read(abias, unit="adu") for abias in biaslist]
    biasComb = ccdproc.Combiner(ccdlist)
    biasComb.sigma_clipping(low_thresh=3, high_thresh=3, func=np.ma.median)
    biasmaster = biasComb.average_combine()
    return biasmaster

def combineDarks(darklist):
    """Combine all the dark files into a master dark"""
    darkComb = ccdproc.Combiner([ccdproc.CCDData.read(adark, unit="adu") for adark in darklist])
    darkComb.sigma_clipping(low_thresh=3, high_thresh=3, func=np.ma.median)
    darkmaster = darkComb.average_combine()
    darkmaster.header['exptime'] = fits.getval(darklist[0], 'exptime')
    return darkmaster

def combineFlats(flatlist, dark=None, bias=None):
    """Combine all flat files into a flat master. Subtract dark or bias if provided."""
    ccdflatlist = [ccdproc.CCDData.read(aflat, unit="adu") for aflat in flatlist]
    if dark is not None and bias is None:
        flat_sub = [ccdproc.subtract_dark(aflat, dark, exposure_time='exptime', exposure_unit=u.second) for aflat in ccdflatlist]
    elif dark is None and bias is not None:
        flat_sub = [ccdproc.subtract_bias(aflat, bias) for aflat in ccdflatlist]
    else:
        flat_sub = ccdflatlist

    flatComb = ccdproc.Combiner(flat_sub)
    flatComb.sigma_clipping(low_thresh=3, high_thresh=3, func=np.ma.median)
    flatComb.scaling = lambda arr: 1./np.ma.average(arr)
    flatmaster = flatComb.average_combine()
    return flatmaster

def preprocess(fits_path):
    """Apply basic CCD reduction tasks.

    Ask for the path to all the calibration and science files, and perform Bias, Dark and Flat combinations and proper substractions.

    Pipeline que aplica una reduccion basica a imagenes de tipo CCD.
    Realiza combinacion de Bias, de Darks, y Flats. Luego realiza las restas inherentes.
    """
    import os
    import sys
    from image_collection import ImageFileCollection

    #Collect all FITS files in path in fitslist
    fitslist = []
    for root, dirs, files in os.walk(fits_path, topdown=True):
        fitslist.extend([os.path.join(root, name) for name in files if '.fit' in name])
    
    #Dictionary with the image type (value) for each image file name (key)
    imagetypes = {img:fits.getval(img, 'IMAGETYP') for img in fitslist}
    
    #Make different lists for different image types
    biaslist = []
    sciencelist = []
    flatlist = []
    darklist = []
    unknown = []
    for k, v in imagetypes.iteritems():
        if 'LIGHT' in v.upper() or v.upper()=='OBJECT':
            sciencelist.append(k)
        elif 'BIAS' in v.upper() or v.upper()=='ZERO':
            biaslist.append(k)
        elif 'FLAT' in v.upper():
            flatlist.append(k)
        elif 'DARK' in v.upper():
            darklist.append(k)
        else:
            unknown.append(k)

    #Create the flat master
    if darklist:
        darkmaster = combineDarks(darklist_flat)
        flatmaster = combineFlats(flatlist, dark=darkmaster)
    elif biaslist:
        biasmaster = combineBias(biaslist)
        flatmaster = combineFlats(flatlist, bias=biasmaster)
    else:
        flatmaster = combineFlats(flatlist)

    for ascience in sciencelist:
        sci_image = ccdproc.CCDData.read(ascience, unit='adu')
        sci_darksub = ccdproc.subtract_dark(sci_image, darkmaster, exposure_time='exptime', exposure_unit=u.second)
        sci_flatcorrected = ccdproc.flat_correct(sci_darksub, flatmaster)
        outpath = os.path.join('/Users/utb/Desktop/reduced/', 'reduced_' + os.path.basename(ascience))
        hdulist = sci_flatcorrected.to_hdu()
        hdulist.writeto(outpath, clobber=True)

    return

if __name__ == "__main__":
    import sys
    fits_path = sys.argv[1]
    preprocess(fits_path)
