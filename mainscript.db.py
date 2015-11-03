#/usr/local/bin/python
# -*- coding: utf-8 -*-
"""
TODO: DOCS
"""
import time
import os
import logging

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


#def enterFileInDB(filename, step):
#    import models
#
#    session = Session()
#
#    macon = models.Observatory()
#    macon.name = 'Macon Ridge'
#    macon.latitude = -24.623
#    macon.longitude = -67.328
#    macon.description = 'Observatory located in Macon Ridge'
#    session.add(macon)
#    session.commit()


if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", help="Input the directory to be processed.", \
                                                                    type=str)
    args = parser.parse_args()

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    startLogger("loaderscript", 'mainscript_' + timestamp + '.log')
    logger = logging.getLogger('loaderscript')

    dataRootFolder = "/data/observations"
    if args.dir is None:
        todaysfolder = time.strftime("%Y%m%d")
    else:
        todaysfolder = args.dir #"20151027"

    #Check if files on folder
    todayspath = os.path.join(dataRootFolder, todaysfolder)
    if os.path.exists(todayspath):

        #Gather all FITS files into a list to be iterated over
        allfitsfiles = [os.path.join(root, afile) for root, dirs, files \
                in os.walk(todayspath) for afile in files if '.fit' in afile]
        
        #import models
        #engine = sa.create_engine('sqlite:///toritos-dev.db', echo=True)
        #Session = sa.orm.sessionmaker()
        #Session.configure(bind=engine)
        #models.Model.metadata.create_all(engine)


        for afile in allfitsfiles:
            print afile
            #Enter each file into database
            enterFileInDB(afile, step='raw')
            #Reduce each file
            # *Create master dark or bias frames
            # *Create master flat frame
            # *Enter both masters and individual files into database
            # *Do the processing
            # *Enter the data into the database

    else:
        logger.warning("Folder %s not found. Ending script." % (todayspath))
        sys.exit(2)


