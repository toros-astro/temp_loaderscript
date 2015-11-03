#/usr/local/bin/python
# -*- coding: utf-8 -*-
"""
TODO: DOCS
"""
import time
import os
import logging
import ccdproc
import numpy as np
from astropy.io import fits
from astropy import units as u

DATA_ROOT = "/Users/utb/Desktop/dataToTestPipeline/observations"

def startLogger(loggerName, logFilename):
    # create logger
    logger = logging.getLogger(loggerName)
    logger.setLevel(logging.DEBUG)

    # create a file handler and set level to debug
    fh = logging.FileHandler(logFilename, mode='w')
    fh.setLevel(logging.DEBUG)

    # create formatter and add it to the logger
    formatter = logging.Formatter('%(asctime)s %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # create a console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)


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
    darkComb = ccdproc.Combiner([ccdproc.CCDData.read(adark, unit="adu") \
        for adark in darklist])
    darkComb.sigma_clipping(low_thresh=3, high_thresh=3, func=np.ma.median)
    darkmaster = darkComb.average_combine()
    darkmaster.header['exptime'] = fits.getval(darklist[0], 'exptime')
    return darkmaster


def combineFlats(flatlist, dark=None, bias=None):
    """Combine all flat files into a flat master. Subtract dark or bias if provided."""
    ccdflatlist = [ccdproc.CCDData.read(aflat, unit="adu") for aflat in flatlist]
    if dark is not None and bias is None:
        flat_sub = [ccdproc.subtract_dark(aflat, dark, exposure_time='exptime',\
            exposure_unit=u.second) for aflat in ccdflatlist]
    elif dark is None and bias is not None:
        flat_sub = [ccdproc.subtract_bias(aflat, bias) for aflat in ccdflatlist]
    else:
        flat_sub = ccdflatlist

    flatComb = ccdproc.Combiner(flat_sub)
    flatComb.sigma_clipping(low_thresh=3, high_thresh=3, func=np.ma.median)
    flatComb.scaling = lambda arr: 1./np.ma.average(arr)
    flatmaster = flatComb.average_combine()
    return flatmaster


def saveCCDDataAndLog(outpath, calibfile):
    logger = logging.getLogger('loaderscript')
    try:
        calibfile.to_hdu().writeto(outpath, clobber=True)
        logger.info("Writing image to file: %s." % (outpath))
    except:
        logger.error("Error writing calibration image to file: %s." %(outpath))


if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", help="Input the directory to be processed.")
    args = parser.parse_args()

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    startLogger("loaderscript", 'mainscript_' + timestamp + '.log')
    logger = logging.getLogger('loaderscript')

    if args.dir is None:
        #todaysfolder = time.strftime("%Y%m%d")
        todaysfolder = "20150916"
    else:
        todaysfolder = args.dir

    #Check if files on folder
    todayspath = os.path.join(DATA_ROOT, todaysfolder)
    if not os.path.exists(todayspath):
        logger.error("Folder %s not found. Ending script." % (todayspath))
        sys.exit(2)

    #Gather all FITS files into a list to be iterated over
    allfitsfiles = [os.path.join(root, afile) for root, dirs, files \
            in os.walk(todayspath) for afile in files if '.fit' in afile]
    rawpath = os.path.join(todayspath, '01_raw')
    try:
        if not os.path.exists(rawpath):
            os.mkdir(rawpath)
    except:
        logger.error("Can't create dir %s. Exiting." % (rawpath))
        sys.exit(2)
    for afile in allfitsfiles:
        #logger.info("Moving file %s to raw folder" % \
        #    (os.path.basename(afile)))
        try:git sasfdadfsdfa
            os.rename(afile, os.path.join(rawpath, \
                os.path.basename(afile)))
        except:
            logger.error("Couldn't move file %s to raw folder." % \
                (todayspath))
        #Enter here file to database

    #Reduce each file
    from image_collection import ImageFileCollection

    #Create an image file collection storing the following keys
    keys = ['imagetyp', 'object', 'filter', 'exptime']
    allfits = ImageFileCollection(rawpath, keywords=keys)

    #Collect all dark files and make a dark frame for each diff exposure time
    dark_matches = np.ma.array(['dark' in atype.lower() \
                                   for atype in allfits.summary['imagetyp']])
    darkexp_set = set(allfits.summary['exptime'][dark_matches])
    darklists = {}
    for anexp in darkexp_set:
        my_darks = allfits.summary['file'][(\
                       allfits.summary['exptime'] == anexp) & dark_matches]
        my_darks = [os.path.join(rawpath, adark) for adark in my_darks]
        darklists[anexp] = combineDarks(my_darks)

    #Collect all science files
    sciencelist = allfits.files_filtered(imagetyp='light')
    sciencelist = [os.path.join(rawpath, afile) for afile in sciencelist]

    #Collect all bias files
    bias_matches = np.ma.array([('zero' in typ.lower() or 'bias' \
        in typ.lower()) for typ in allfits.summary['imagetyp']])
    biaslist = allfits.summary['file'][bias_matches]
    biaslist = [os.path.join(rawpath, afile) for afile in biaslist]
    biasmaster = combineBias(biaslist)

    #Create the flat master
    flatlist = allfits.files_filtered(imagetyp='flat')
    flatlist = [os.path.join(rawpath, aflat) for aflat in flatlist]
    exptime = fits.getval(flatlist[0], 'exptime')
    darkmaster = chooseClosestDark(darklists, exptime)
    flatmaster = combineFlats(flatlist, dark=darkmaster)

    preprocessedpath = os.path.join(todayspath, '02_preprocessed')
    try:
        if not os.path.exists(preprocessedpath):
            os.mkdir(preprocessedpath)
    except:
        logger.error("Can't create dir %s. Exiting." % (preprocessedpath))
        sys.exit(2)

    #Save calibration master files
    for adarkexp in darkexp_set:
        outpath = os.path.join(preprocessedpath, \
                                'dark_master_' + str(adarkexp) + 's.fits')
        saveCCDDataAndLog(outpath, darkmaster)
    outpath = os.path.join(preprocessedpath, 'bias_master.fits')
    saveCCDDataAndLog(outpath, biasmaster)
    outpath = os.path.join(preprocessedpath, 'flat_master.fits')
    saveCCDDataAndLog(outpath, flatmaster)

    for ascience in sciencelist:
        try:
            sci_image = ccdproc.CCDData.read(ascience, unit='adu')
            exp_time = fits.getval(ascience, 'exptime')
            darkmaster = chooseClosestDark(darklists, exp_time)
            sci_darksub = ccdproc.subtract_dark(sci_image, darkmaster, \
                exposure_time='exptime', exposure_unit=u.second)
            sci_flatcorrected = ccdproc.flat_correct(sci_darksub, flatmaster)
        except:
            logger.error("Couldn't reduce image %s." % (ascience))
            continue
        outpath = os.path.join(preprocessedpath, \
                 'preprocessed_' + os.path.basename(ascience))
        saveCCDDataAndLog(outpath, sci_flatcorrected)

