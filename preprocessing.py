#!/usr/local/bin/python
"""Apply basic CCD reduction tasks for the Toritos telescope at Cerro Macon, Salta, Argentina.

Bruno Sanchez & Martin Beroiz
"""
import numpy as np
from astropy import units as u
from astropy.io import fits
import ccdproc

def chooseClosestDark(darklists, exptime):
    best_t = np.inf
    for anexp in darklists.iterkeys():
        if abs(anexp - exptime) < best_t:
            best_t = anexp
    return darklists[best_t]

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
    #fitslist = []
    #for root, dirs, files in os.walk(fits_path, topdown=True):
    #    fitslist.extend([os.path.join(root, name) for name in files if '.fit' in name])
    #
    ##Dictionary with the image type (value) for each image file name (key)
    #imagetypes = {img:fits.getval(img, 'IMAGETYP') for img in fitslist}

    # now we make different lists for different image types
    #biaslist = []
    #sciencelist = []
    #flatlist = []
    #darklist = []
    #unknown = []
    #for k, v in imagetypes.iteritems():
    #    if 'LIGHT' in v.upper() or v.upper()=='OBJECT':
    #        sciencelist.append(k)
    #    elif 'BIAS' in v.upper() or v.upper()=='ZERO':
    #        biaslist.append(k)
    #    elif 'FLAT' in v.upper():
    #        flatlist.append(k)
    #    elif 'DARK' in v.upper():
    #        darklist.append(k)
    #    else:
    #        unknown.append(k)


    #Create an image file collection storing the following keys
    keys = ['imagetyp', 'object', 'filter', 'exptime']
    allfits = ImageFileCollection('.', keywords=keys)

    #Collect all dark files and make a dark frame for each different exposure time
    dark_matches = np.ma.array(['dark' in typ.lower() for typ in allfits.summary['imagetyp']])
    darkexp_set = set(allfits.summary['exptime'][dark_matches])
    darklists = {}
    for anexp in darkexp_set:
        my_darks = allfits.summary['file'][(allfits.summary['exptime'] == anexp) & dark_matches]
        darklists[anexp] = combineDarks(my_darks)

    #Collect all science files
    sciencelist = allfits.files_filtered(imagetyp='light')

    #Collect all bias files
    #bias_matches = ([('zero' in typ.lower() or 'bias' in typ.lower()) for typ in allfits.summary['imagetyp']]
    #biaslist = allfits.summary['file'][bias_matches]

    #Create the flat master
    flatlist = allfits.files_filtered(imagetyp='flat')
    exptime = fits.getval(flatlist[0], 'exptime')
    darkmaster = chooseClosestDark(darklists, exptime)
    flatmaster = combineFlats(flatlist, dark=darkmaster)

    for ascience in sciencelist:
        sci_image = ccdproc.CCDData.read(ascience, unit='adu')
        exp_time = fits.getval(ascience, 'exptime')
        darkmaster = chooseClosestDark(darklists, exp_time)
        try:
            sci_darksub = ccdproc.subtract_dark(sci_image, darkmaster, exposure_time='exptime', exposure_unit=u.second)
            sci_flatcorrected = ccdproc.flat_correct(sci_darksub, flatmaster)
            outpath = os.path.join('/Users/utb/Desktop/reduced/', 'reduced_' + os.path.basename(ascience))
        except:
            sci_flatcorrected = sci_image
            outpath = os.path.join('/Users/utb/Desktop/reduced/', 'failed_' + os.path.basename(ascience))
        hdulist = sci_flatcorrected.to_hdu()
        hdulist.writeto(outpath, clobber=True)

    return

if __name__ == "__main__":
    import sys
    fits_path = sys.argv[1]
    preprocess(fits_path)
