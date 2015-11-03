#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import datetime

from sqlalchemy.orm import sessionmaker
from astropy.io import fits

#from toritos import models
import models

import sqlalchemy as sa

engine = sa.create_engine('sqlite:///toritos-dev.db', echo=True)
Session = sessionmaker()
Session.configure(bind=engine)

models.Model.metadata.create_all(engine)

session = Session()

macon = models.Observatory()
macon.name = 'Macon ridge'
macon.latitude = -24.623
macon.longitude = -67.328
macon.description = 'Observatory located in macon ridge'
session.add(macon)

ligoO1Campaign = models.Campaign()


session.commit()


