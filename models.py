#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlalchemy as sa
import sqlalchemy_utils as sau

from sqlalchemy.ext.declarative import declarative_base
Model = declarative_base()


class Observatory(Model):

    __tablename__ = 'Observatory'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(100), nullable=False, unique=True)
    latitude = sa.Column(sa.Float, nullable=False)
    longitude = sa.Column(sa.Float, nullable=False)
    description = sa.Column(sa.Text, nullable=True)

    def repr(self):
        return self.name


class CCD(Model):

    __tablename__ = 'CCD'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(100), nullable=False, unique=True)
    brand = sa.Column(sa.String(100), nullable=False)
    model = sa.Column(sa.String(100), nullable=False)
    description = sa.Column(sa.Text, nullable=True)

    def __repr__(self):
        return self.name


class Campaign(Model):

    __tablename__ = 'Campaign'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(100), nullable=False, unique=True)
    description = sa.Column(sa.Text, nullable=True)

    observatory_id = sa.Column(sa.Integer, sa.ForeignKey('Observatory.id'))
    observatory = sa.orm.relationship(
        "Observatory", backref=sa.orm.backref('campaigns', order_by=id))
    ccd_id = sa.Column(sa.Integer, sa.ForeignKey('CCD.id'))
    ccd = sa.orm.relationship(
        "CCD", backref=sa.orm.backref('campaigns', order_by=id))

    def repr(self):
        return self.name


class State(Model):

    __tablename__ = 'State'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(100), nullable=False, unique=True)
    folder = sa.Column(sa.Text, nullable=True)
    order = sa.Column(sa.Integer, nullable=False)
    is_error = sa.Column(sa.Boolean, nullable=False)

    def __repr__(self):
        return self.name


class StateChange(Model):

    __tablename__ = 'StateChange'

    id = sa.Column(sa.Integer, primary_key=True)

    created_at = sa.Column(sa.DateTime(timezone=True))
    modified_at = sa.Column(sa.DateTime(timezone=True))
    count = sa.Column(sa.Integer)
    path = sa.Column(sa.Text, nullable=True)

    state_id = sa.Column(sa.Integer, sa.ForeignKey('State.id'))
    state = sa.orm.relationship(
        "State", backref=sa.orm.backref('statechanges', order_by=id))
    pawprint_id = sa.Column(sa.Integer, sa.ForeignKey('Pawprint.id'))
    pawprint = sa.orm.relationship(
        "Pawprint", backref=sa.orm.backref('statechanges', order_by=id))

    def repr(self):
        return "{} ({})".format(repr(self.pawprint), repr(self.state))


class Reference(Model):

    __tablename__ = 'Reference'

    id = sa.Column(sa.Integer, primary_key=True)
    path = sa.Column(sa.Text, nullable=True)
    ra = sa.Column(sa.Float, nullable=False)
    dec = sa.Column(sa.Float, nullable=False)
    FoV = sa.Column(sa.Float, nullable=False)

    def repr(self):
        return self.path


class Source(Model):

    __tablename__ = 'Source'

    id = sa.Column(sa.Integer, primary_key=True)
    ra = sa.Column(sa.Float, nullable=False)
    dec = sa.Column(sa.Float, nullable=False)
    mag = sa.Column(sa.Float, nullable=False)
    mag_err = sa.Column(sa.Float, nullable=False)
    class_source = sa.Column(sa.String, nullable=True)

    pawprint_id = sa.Column(sa.Integer, sa.ForeignKey('Pawprint.id'))
    pawprint = sa.orm.relationship(
        "Pawprint", backref=sa.orm.backref('sources', order_by=id))

    def repr(self):
        return "({}, {})".format(self.ra, self.dec)


class Candidate(Model):

    __tablename__ = 'Candidate'

    PREDICTED_TYPES = [
        ("real", "Real"), ("bogus", "Bogus")
    ]

    id = sa.Column(sa.Integer, primary_key=True)
    ra = sa.Column(sa.Float, nullable=False)
    dec = sa.Column(sa.Float, nullable=False)
    mag = sa.Column(sa.Float, nullable=False)
    mag_err = sa.Column(sa.Float, nullable=False)
    predicted = sa.Column(sau.ChoiceType(PREDICTED_TYPES), nullable=True)

    pawprint_id = sa.Column(sa.Integer, sa.ForeignKey('Pawprint.id'))
    pawprint = sa.orm.relationship(
        "Pawprint", backref=sa.orm.backref('candidates', order_by=id))
    stack_id = sa.Column(sa.Integer, sa.ForeignKey('Stack.id'))
    stack = sa.orm.relationship(
        "Stack", backref=sa.orm.backref('candidates', order_by=id))

    def repr(self):
        return "({}, {})".format(self.ra, self.dec)


class StackState(Model):

    __tablename__ = 'StackState'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(100), nullable=False, unique=True)
    folder = sa.Column(sa.Text, nullable=True)
    order = sa.Column(sa.Integer, nullable=False)
    is_error = sa.Column(sa.Boolean, nullable=False)

    def __repr__(self):
        return self.name


class StackStateChange(Model):

    __tablename__ = 'StackStateChange'

    id = sa.Column(sa.Integer, primary_key=True)

    created_at = sa.Column(sa.DateTime(timezone=True))
    modified_at = sa.Column(sa.DateTime(timezone=True))
    count = sa.Column(sa.Integer)
    path = sa.Column(sa.Text, nullable=True)

    stackstate_id = sa.Column(sa.Integer, sa.ForeignKey('StackState.id'))
    stackstate = sa.orm.relationship(
        "StackState", backref=sa.orm.backref('stack_statechanges', order_by=id))
    stack_id = sa.Column(sa.Integer, sa.ForeignKey('Stack.id'))
    stack = sa.orm.relationship(
        "Stack", backref=sa.orm.backref('stack_statechanges', order_by=id))

    def repr(self):
        return "{} ({})".format(repr(self.stack), repr(self.stackstate))


class Pawprint(Model):

    __tablename__ = 'Pawprint'

    id = sa.Column(sa.Integer, primary_key=True)
    created_at = sa.Column(sa.DateTime(timezone=True))
    observation_date = sa.Column(sa.DateTime(timezone=True))
    modified_at = sa.Column(sa.DateTime(timezone=True))

    # agregar todo lo que el fits header tenga
    # y columnas adicionales
    exptime = sa.Column(sa.Integer, nullable=False)
    ccdtemp = sa.Column(sa.Float, nullable=True)
    imagetype = sa.Column(sa.String(16), nullable=False)
    jd = sa.Column(sa.Float, nullable=False)
    targname = sa.Column(sa.String(40), nullable=True)
    xbinning = sa.Column(sa.Integer, nullable=False)
    ybinning = sa.Column(sa.Integer, nullable=False)

    state_id = sa.Column(sa.Integer, sa.ForeignKey('State.id'))
    state = sa.orm.relationship(
        "State", backref=sa.orm.backref('pawprints', order_by=id))
    campaign_id = sa.Column(sa.Integer, sa.ForeignKey('Campaign.id'))
    campaign = sa.orm.relationship(
        "Campaign", backref=sa.orm.backref('pawprints', order_by=id))

    def repr(self):
        return self.id


class Stack(Model):

    __tablename__ = 'Stack'

    id = sa.Column(sa.Integer, primary_key=True)
    created_at = sa.Column(sa.DateTime(timezone=True))
    modified_at = sa.Column(sa.DateTime(timezone=True))
    path = sa.Column(sa.Text, nullable=True)

    def repr(self):
        return self.id


class MasterCal(Model):

    __tablename__ = 'MasterCal'

    id = sa.Column(sa.Integer, primary_key=True)
    created_at = sa.Column(sa.DateTime(timezone=True))
    modified_at = sa.Column(sa.DateTime(timezone=True))
    path = sa.Column(sa.Text, nullable=True)
    imagetype = sa.Column(sa.String(40), nullable=False)

    def repr(self):
        return self.id


class Combination(Model):

    __tablename__ = 'Combination'

    id = sa.Column(sa.Integer, primary_key=True)

    calfile_id = sa.Column(sa.Integer, sa.ForeignKey('CalFile.id'))
    calfile = sa.orm.relationship(
        "CalFile", backref=sa.orm.backref('combinations', order_by=id))
    mastercal_id = sa.Column(sa.Integer, sa.ForeignKey('MasterCal.id'))
    mastercal = sa.orm.relationship(
        "MasterCal", backref=sa.orm.backref('combinations', order_by=id))

    def repr(self):
        return self.id


class CalFile(Model):

    __tablename__ = 'CalFile'

    id = sa.Column(sa.Integer, primary_key=True)
    path = sa.Column(sa.Text, nullable=True)
    observation_date = sa.Column(sa.DateTime(timezone=True))
    exptime = sa.Column(sa.Integer, nullable=False)
    created_at = sa.Column(sa.DateTime(timezone=True))
    imagetype = sa.Column(sa.String(16), nullable=False)

    def repr(self):
        return self.id
