import tablib

from ctools_common.geo import point_wkt_to_array

__author__ = 'nathan'

import uuid
import os
import tempfile
import shutil
import subprocess
from collections import namedtuple
import glob
import time
import numpy
import datetime

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.orm.session import object_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSON
from geoalchemy2 import Geometry

from ctools_common import geo
import ctools_backend.settings

engine = sa.create_engine(ctools_backend.settings.connection_string)
Base = declarative_base(metadata=sa.MetaData(bind=engine))
Session = orm.scoped_session(orm.sessionmaker(bind=engine))


def null_data(d):
    if d is None:
        return 0
    else:
        return d


class County(Base):
    __tablename__ = "us_counties"
    gid = sa.Column(sa.Integer, primary_key=True)
    geom = sa.Column(Geometry("MULTIPOLYGON"))
    stfips = sa.Column(sa.Numeric(asdecimal=False))
    ctfips = sa.Column(sa.Numeric(asdecimal=False))


class NWSSite(Base):
    __tablename__ = "nws_locations"
    gid = sa.Column(sa.Integer, primary_key=True)
    sf_id = sa.Column(sa.Numeric(asdecimal=False))
    geom = sa.Column(Geometry("POINT"))


class Receptor(object):
    fields = ["id", "x", "y", "lat", "lng"]
    namedtuple_class = namedtuple("Receptor", fields)

    def __init__(self, id_=None, lat=None, lng=None, x=None, y=None):
        if lat and lng:
            self.lat = lat
            self.lng = lng
            (self.x, self.y) = geo.mercator_to_lcc(lng, lat)
        elif x and y:
            self.x = x
            self.y = y
            (self.lng, self.lat) = geo.lcc_to_mercator(x, y)
        else:
            raise ValueError("Must specify either x and y or lat and lng")
        self.id = id_

    def as_namedtuple(self):
        return self.namedtuple_class(self.id, self.x, self.y, self.lat, self.lng)

    @staticmethod
    def instance_factory(fields, instance_tuples):
        return [Receptor(**{k: v for (k, v) in zip(fields, instance)}) for
                instance in instance_tuples]


class Road(Base):
    __tablename__ = "roads"
    fields = ["gid", "id", "sign1", "from_x", "from_y", "to_x", "to_y", "sf_id",
              "stfips", "ctfips", "fclass_rev", "aadt", "mph", "geom", "gas_car_multiplier",
              "gas_truck_multiplier", "diesel_car_multiplier",
              "diesel_truck_multiplier"]
    namedtuple_class = namedtuple("Road", fields)
    gid = sa.Column(sa.Integer, primary_key=True)
    id = sa.Column(sa.Numeric(asdecimal=False))
    sign1 = sa.Column(sa.String(100))
    from_x = sa.Column(sa.Numeric(asdecimal=False))
    from_y = sa.Column(sa.Numeric(asdecimal=False))
    to_x = sa.Column(sa.Numeric(asdecimal=False))
    to_y = sa.Column(sa.Numeric(asdecimal=False))
    sf_id = sa.Column(sa.Numeric(asdecimal=False))
    stfips = sa.Column(sa.Numeric(asdecimal=False))
    ctfips = sa.Column(sa.Numeric(asdecimal=False))
    fclass_rev = sa.Column(sa.Numeric(asdecimal=False))
    aadt = sa.Column("aadt07", sa.Numeric(asdecimal=False))
    mph = sa.Column("speed", sa.Integer)
    geom = sa.Column(Geometry('MULTILINESTRING'))

    def __init__(self, **kwargs):
        self.gas_car_multiplier = kwargs.pop("gas_car_multiplier", 1)
        self.gas_truck_multiplier = kwargs.pop("gas_truck_multiplier", 1)
        self.diesel_car_multiplier = kwargs.pop("diesel_car_multiplier", 1)
        self.diesel_truck_multiplier = kwargs.pop("diesel_truck_multiplier", 1)
        super(Road, self).__init__(**kwargs)

    @classmethod
    def construct_namedtuple(cls, *args):
        return cls.namedtuple_class(*[null_data(a) for a in args])

    def as_namedtuple(self):
        return self.namedtuple_class(
            self.gid, self.id, self.sign1, self.from_x, self.from_y, self.to_x, self.to_y,
            self.sf_id, self.stfips, self.ctfips, self.fclass_rev, self.aadt,
            self.mph, geo.multilinestring_to_point_list(self.geom), 1, 1, 1, 1)

    @staticmethod
    def instance_factory(fields, instance_tuples):
        return [Road(**{k: v for (k, v) in zip(fields, instance)}) for
                instance in instance_tuples]


class Railway(Base):
    __tablename__ = "railways"
    fields = ["gid", "rrowner1", "fromx", "fromy", "tox", "toy", "sf_id", "nox", "benz", "pm25",
              "dies_pm25", "ec", "oc", "co", "form", "ald2", "acro", "butal_3", "toluene", "so2", "geom"]
    namedtuple_class = namedtuple("Railway", fields)
    gid = sa.Column("objectid", sa.Integer, primary_key=True)
    rrowner1 = sa.Column(sa.String)
    fromx = sa.Column(sa.Numeric(asdecimal=False))
    fromy = sa.Column(sa.Numeric(asdecimal=False))
    tox = sa.Column(sa.Numeric(asdecimal=False))
    toy = sa.Column(sa.Numeric(asdecimal=False))
    sf_id = sa.Column(sa.Integer)
    nox = sa.Column(sa.Numeric(asdecimal=False))
    pm25 = sa.Column(sa.Numeric(asdecimal=False))
    co = sa.Column(sa.Numeric(asdecimal=False))
    benz = sa.Column(sa.Numeric(asdecimal=False))
    dies_pm25 = sa.Column(sa.Numeric(asdecimal=False))
    ec = sa.Column(sa.Numeric(asdecimal=False))
    oc = sa.Column(sa.Numeric(asdecimal=False))
    form = sa.Column(sa.Numeric(asdecimal=False))
    ald2 = sa.Column(sa.Numeric(asdecimal=False))
    acro = sa.Column(sa.Numeric(asdecimal=False))
    butal_3 = sa.Column(sa.Numeric(asdecimal=False))
    toluene = sa.Column(sa.Numeric(asdecimal=False))
    so2 = sa.Column(sa.Numeric(asdecimal=False))
    geom = sa.Column(Geometry('MULTILINESTRING'))

    @classmethod
    def construct_namedtuple(cls, *args):
        return cls.namedtuple_class(*[null_data(a) for a in args])

    def as_namedtuple(self):
        return self.namedtuple_class(self.gid, self.rrowner1, self.fromx, self.fromy, self.tox, self.toy,
                                     self.sf_id, null_data(self.nox), null_data(self.benz), null_data(self.pm25),
                                     null_data(self.dies_pm25), null_data(self.ec),
                                     null_data(self.oc), null_data(self.co), null_data(self.form),
                                     null_data(self.ald2), null_data(self.acro), null_data(self.butal_3),
                                     null_data(self.toluene), null_data(self.so2),
                                     geo.multilinestring_to_point_list(self.geom))

    @staticmethod
    def instance_factory(fields, instance_tuples):
        return [Railway(**{k: v for (k, v) in zip(fields, instance)}) for
                instance in instance_tuples]

    @staticmethod
    def split_source(source):
        src_list = []
        src_dict = source._asdict()
        if len(source.geom) == 2:
            (from_lng, from_lat) = source.geom[0]
            (to_lng, to_lat) = source.geom[1]
            (from_x, from_y) = geo.mercator_to_lcc(from_lng, from_lat)
            (to_x, to_y) = geo.mercator_to_lcc(to_lng, to_lat)
            src_dict["fromx"] = from_x
            src_dict["fromy"] = from_y
            src_dict["tox"] = to_x
            src_dict["toy"] = to_y
            src_list.append(Railway.namedtuple_class(**src_dict))
        else:
            total_length_m = 0
            for segment in zip(source.geom[:-1], source.geom[1:]):
                (lon1, lat1) = segment[0]
                (lon2, lat2) = segment[1]
                total_length_m += geo.distance_on_unit_sphere(lat1, lon1, lat2, lon2) * 6373

            for segment in zip(source.geom[:-1], source.geom[1:]):
                (lon1, lat1) = segment[0]
                (lon2, lat2) = segment[1]
                segment_length_m = geo.distance_on_unit_sphere(lat1, lon1, lat2, lon2) * 6373
                emis_fraction = segment_length_m / total_length_m

                (from_x, from_y) = geo.mercator_to_lcc(lon1, lat1)
                (to_x, to_y) = geo.mercator_to_lcc(lon2, lat2)
                src_dict["fromx"] = from_x
                src_dict["fromy"] = from_y
                src_dict["tox"] = to_x
                src_dict["toy"] = to_y
                src_dict["geom"] = segment

                for attr in ["nox", "pm25", "co", "benz", "dies_pm25", "ec", "oc",
                             "form", "ald2", "acro", "butal_3", "toluene", "so2"]:
                    src_dict[attr] = getattr(source, attr) * emis_fraction

                src_list.append(Railway.namedtuple_class(**src_dict))
        return src_list


class AreaSource(Base):
    __tablename__ = "area_sources"
    fields = ["facility", "gid", "sf_id", "nox", "benz", "pm2_5", "dies_pm25", "ec", "oc",
              "co", "form", "ald2", "acro", "butal_3", "toluene", "so2", "geom"]
    namedtuple_class = namedtuple("AreaSource", fields)
    facility = sa.Column(sa.Text)
    gid = sa.Column("object_id", sa.Integer, primary_key=True)
    sf_id = sa.Column(sa.Integer)
    nox = sa.Column(sa.Numeric(asdecimal=False))
    pm2_5 = sa.Column(sa.Numeric(asdecimal=False))
    co = sa.Column(sa.Numeric(asdecimal=False))
    benz = sa.Column(sa.Numeric(asdecimal=False))
    dies_pm25 = sa.Column(sa.Numeric(asdecimal=False))
    ec = sa.Column(sa.Numeric(asdecimal=False))
    oc = sa.Column(sa.Numeric(asdecimal=False))
    form = sa.Column(sa.Numeric(asdecimal=False))
    ald2 = sa.Column(sa.Numeric(asdecimal=False))
    acro = sa.Column(sa.Numeric(asdecimal=False))
    butal_3 = sa.Column(sa.Numeric(asdecimal=False))
    toluene = sa.Column(sa.Numeric(asdecimal=False))
    so2 = sa.Column(sa.Numeric(asdecimal=False))
    geom = sa.Column(Geometry('MULTIPOLYGON'))

    @classmethod
    def construct_namedtuple(cls, *args):
        return cls.namedtuple_class(*[null_data(a) for a in args])

    def as_namedtuple(self):
        geom = geo.multipolygon_to_point_list(self.geom)
        return self.namedtuple_class(self.facility, self.gid, self.sf_id, null_data(self.nox), null_data(self.benz),
                                     null_data(self.pm2_5), null_data(self.dies_pm25), null_data(self.ec),
                                     null_data(self.oc), null_data(self.co), null_data(self.form),
                                     null_data(self.ald2), null_data(self.acro), null_data(self.butal_3),
                                     null_data(self.toluene), null_data(self.so2), geom)

    @staticmethod
    def to_vertices(source):
        results = []
        for (lng, lat) in source.geom:
            (x, y) = geo.mercator_to_lcc(lng, lat)
            results.append(
                [source.gid, source.sf_id, x, y, null_data(source.nox), null_data(source.benz),
                 null_data(source.pm2_5),
                 null_data(source.dies_pm25), null_data(source.ec),
                 null_data(source.oc), null_data(source.co), null_data(source.form),
                 null_data(source.ald2), null_data(source.acro), null_data(source.butal_3),
                 null_data(source.toluene), null_data(source.so2)])
        return results


class ShipInTransit(Base):
    __tablename__ = "ships_in_transit"
    fields = ["facility", "gid", "startx", "starty", "endx", "endy", "sf_id", "nox", "benz", "pm2_5",
              "dies_pm25", "ec", "oc", "co", "form", "ald2", "acro", "butal_3", "toluene", "so2", "stack_height",
              "stack_diameter", "stack_velocity", "stack_temperature", "geom"]
    namedtuple_class = namedtuple("ShipInTransit", fields)
    gid = sa.Column("object_id", sa.Integer, primary_key=True)
    facility = sa.Column(sa.Text)
    startx = sa.Column(sa.Numeric(asdecimal=False))
    starty = sa.Column(sa.Numeric(asdecimal=False))
    endx = sa.Column(sa.Numeric(asdecimal=False))
    endy = sa.Column(sa.Numeric(asdecimal=False))
    sf_id = sa.Column(sa.Integer)
    nox = sa.Column(sa.Numeric(asdecimal=False))
    pm2_5 = sa.Column(sa.Numeric(asdecimal=False))
    co = sa.Column(sa.Numeric(asdecimal=False))
    benz = sa.Column(sa.Numeric(asdecimal=False))
    dies_pm25 = sa.Column(sa.Numeric(asdecimal=False))
    ec = sa.Column(sa.Numeric(asdecimal=False))
    oc = sa.Column(sa.Numeric(asdecimal=False))
    form = sa.Column(sa.Numeric(asdecimal=False))
    ald2 = sa.Column(sa.Numeric(asdecimal=False))
    acro = sa.Column(sa.Numeric(asdecimal=False))
    butal_3 = sa.Column(sa.Numeric(asdecimal=False))
    toluene = sa.Column(sa.Numeric(asdecimal=False))
    so2 = sa.Column(sa.Numeric(asdecimal=False))
    stack_height = sa.Column(sa.Numeric(asdecimal=False))
    stack_diameter = sa.Column(sa.Numeric(asdecimal=False))
    stack_velocity = sa.Column(sa.Numeric(asdecimal=False))
    stack_temperature = sa.Column(sa.Numeric(asdecimal=False))
    geom = sa.Column(Geometry('MULTILINESTRING'))

    @classmethod
    def construct_namedtuple(cls, *args):
        return cls.namedtuple_class(*[null_data(a) for a in args])

    def as_namedtuple(self):
        return self.namedtuple_class(self.facility, self.gid, self.startx, self.starty, self.endx,
                                     self.endy, self.sf_id, null_data(self.nox), null_data(self.benz),
                                     null_data(self.pm2_5), null_data(self.dies_pm25), null_data(self.ec),
                                     null_data(self.oc), null_data(self.co), null_data(self.form),
                                     null_data(self.ald2), null_data(self.acro), null_data(self.butal_3),
                                     null_data(self.toluene), null_data(self.so2), self.stack_height, self.stack_diameter,
                                     self.stack_velocity, self.stack_temperature,
                                     geo.multilinestring_to_point_list(self.geom))

    @staticmethod
    def split_source(source):
        src_list = []
        src_dict = source._asdict()
        if len(source.geom) == 2:
            (from_lng, from_lat) = source.geom[0]
            (to_lng, to_lat) = source.geom[1]
            (from_x, from_y) = geo.mercator_to_lcc(from_lng, from_lat)
            (to_x, to_y) = geo.mercator_to_lcc(to_lng, to_lat)
            src_dict["startx"] = from_x
            src_dict["starty"] = from_y
            src_dict["endx"] = to_x
            src_dict["endy"] = to_y
            src_list.append(ShipInTransit.namedtuple_class(**src_dict))
        else:
            total_length_m = 0
            for segment in zip(source.geom[:-1], source.geom[1:]):
                (lon1, lat1) = segment[0]
                (lon2, lat2) = segment[1]
                total_length_m += geo.distance_on_unit_sphere(lat1, lon1, lat2, lon2) * 6373

            for segment in zip(source.geom[:-1], source.geom[1:]):
                (lon1, lat1) = segment[0]
                (lon2, lat2) = segment[1]
                segment_length_m = geo.distance_on_unit_sphere(lat1, lon1, lat2, lon2) * 6373
                emis_fraction = segment_length_m / total_length_m

                (from_x, from_y) = geo.mercator_to_lcc(lon1, lat1)
                (to_x, to_y) = geo.mercator_to_lcc(lon2, lat2)
                src_dict["startx"] = from_x
                src_dict["starty"] = from_y
                src_dict["endx"] = to_x
                src_dict["endy"] = to_y
                src_dict["geom"] = segment

                for attr in ["nox", "pm2_5", "co", "benz", "dies_pm25", "ec", "oc",
                             "form", "ald2", "acro", "butal_3", "toluene", "so2"]:
                    src_dict[attr] = getattr(source, attr) * emis_fraction

                src_list.append(ShipInTransit.namedtuple_class(**src_dict))
        return src_list


class PointSource(Base):
    __tablename__ = "point_sources"
    fields = ["pltname", "gid", "x", "y", "sf_id", "stkht", "stkdm", "stktmp", "stkvel", "nox", "benz",
              "pm25", "dies_pm25", "ec", "oc", "co", "form", "ald2", "acro", "butal_3", "toluene", "so2", "geom",
              "in_port"]
    namedtuple_class = namedtuple("PointSource", fields)
    pltname = sa.Column(sa.Text)
    gid = sa.Column(sa.Integer, primary_key=True)
    y = sa.Column(sa.Numeric(asdecimal=False))
    x = sa.Column(sa.Numeric(asdecimal=False))
    sf_id = sa.Column(sa.Integer)
    stkht = sa.Column(sa.Numeric(asdecimal=False))
    stkdm = sa.Column(sa.Numeric(asdecimal=False))
    stktmp = sa.Column(sa.Numeric(asdecimal=False))
    stkvel = sa.Column(sa.Numeric(asdecimal=False))
    nox = sa.Column(sa.Numeric(asdecimal=False))
    pm25 = sa.Column(sa.Numeric(asdecimal=False))
    co = sa.Column(sa.Numeric(asdecimal=False))
    benz = sa.Column(sa.Numeric(asdecimal=False))
    dies_pm25 = sa.Column(sa.Numeric(asdecimal=False))
    ec = sa.Column(sa.Numeric(asdecimal=False))
    oc = sa.Column(sa.Numeric(asdecimal=False))
    form = sa.Column(sa.Numeric(asdecimal=False))
    ald2 = sa.Column(sa.Numeric(asdecimal=False))
    acro = sa.Column(sa.Numeric(asdecimal=False))
    butal_3 = sa.Column(sa.Numeric(asdecimal=False))
    toluene = sa.Column(sa.Numeric(asdecimal=False))
    so2 = sa.Column(sa.Numeric(asdecimal=False))
    geom = sa.Column(Geometry('POINT'))
    in_port = sa.Column(sa.Boolean)

    @classmethod
    def construct_namedtuple(cls, *args):
        return cls.namedtuple_class(*[null_data(a) for a in args])

    def as_namedtuple(self):
        shape = geo.to_shape(self.geom)
        return self.namedtuple_class(self.pltname, self.gid, self.x, self.y, self.sf_id, self.stkht,
                                     self.stkdm, self.stktmp, self.stkvel, null_data(self.nox),
                                     null_data(self.benz), null_data(self.pm25),
                                     null_data(self.dies_pm25), null_data(self.ec),
                                     null_data(self.oc), null_data(self.co), null_data(self.form),
                                     null_data(self.ald2), null_data(self.acro), null_data(self.butal_3),
                                     null_data(self.toluene), null_data(self.so2), [shape.x, shape.y], self.in_port)


class Scenario(Base):
    __tablename__ = "scenario"
    scenario_id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Text)
    tool = sa.Column(sa.Text)
    name = sa.Column(sa.Text)
    hour = sa.Column(sa.Integer)
    season = sa.Column(sa.Integer)
    wind = sa.Column(sa.Text)
    day = sa.Column(sa.Integer)
    met_conditions = sa.Column(sa.Integer)
    area_sources = sa.Column(JSON)
    point_sources = sa.Column(JSON)
    railways = sa.Column(JSON)
    roads = sa.Column(JSON)
    ships_in_transit = sa.Column(JSON)
    center = sa.Column(Geometry("POINT"))
    zoom = sa.Column(sa.Integer)
    area_source_fields = sa.Column(JSON)
    point_source_fields = sa.Column(JSON)
    railway_fields = sa.Column(JSON)
    road_fields = sa.Column(JSON)
    ship_in_transit_fields = sa.Column(JSON)
    include_area_sources = sa.Column(sa.Boolean)
    include_point_sources = sa.Column(sa.Boolean)
    include_railways = sa.Column(sa.Boolean)
    include_roads = sa.Column(sa.Boolean)
    include_ships_in_transit = sa.Column(sa.Boolean)
    last_update = sa.Column(sa.DateTime)

    @property
    def safe_name(self):
        return "".join([x if x.isalnum() else "_" for x in self.name])

    @property
    def to_dict(self):
        return {
            "scenario_id": self.scenario_id,
            "tool": self.tool,
            "name": self.name,
            "hour": self.hour,
            "season": self.season,
            "wind": self.wind,
            "day": self.day,
            "met_conditions": self.met_conditions,
            "area_sources": self.area_sources,
            "point_sources": self.point_sources,
            "railways": self.railways,
            "roads": self.roads,
            "ships_in_transit": self.ships_in_transit,
            "center": point_wkt_to_array(self.center),
            "zoom": self.zoom,
            "area_source_fields": self.area_source_fields,
            "point_source_fields": self.point_source_fields,
            "railway_fields": self.railway_fields,
            "road_fields": self.road_fields,
            "ship_in_transit_fields": self.ship_in_transit_fields,
            "include_area_sources": self.include_area_sources,
            "include_point_sources": self.include_area_sources,
            "include_railways": self.include_railways,
            "include_roads": self.include_roads,
            "include_ships_in_transit": self.include_ships_in_transit,
            "last_update": self.last_update.isoformat()
        }


class AbstractScenarioRun(object):

    @property
    def current_status(self):
        select = sa.select([self.__table__.c.status]).where(type(self).scenario_run_id == self.scenario_run_id)
        return select.execute().fetchone()[0]

    def _get_bounds_helper(self, scenario):
        if scenario.include_area_sources:
            for source in scenario.area_sources:
                for (lng, lat) in source[16]:
                    if lat < self.min_lat or self.min_lat is None:
                        self.min_lat = lat
                    if lat > self.max_lat or self.max_lat is None:
                        self.max_lat = lat
                    if lng < self.min_lng or self.min_lng is None:
                        self.min_lng = lng
                    if lng > self.max_lng or self.max_lng is None:
                        self.max_lng = lng
        if scenario.include_point_sources:
            for source in scenario.point_sources:
                (lng, lat) = source[22]
                if lat < self.min_lat or self.min_lat is None:
                    self.min_lat = lat
                if lat > self.max_lat or self.max_lat is None:
                    self.max_lat = lat
                if lng < self.min_lng or self.min_lng is None:
                    self.min_lng = lng
                if lng > self.max_lng or self.max_lng is None:
                    self.max_lng = lng
        if scenario.include_roads:
            for source in scenario.roads:
                for (lng, lat) in source[13]:
                    if lat < self.min_lat or self.min_lat is None:
                        self.min_lat = lat
                    if lat > self.max_lat or self.max_lat is None:
                        self.max_lat = lat
                    if lng < self.min_lng or self.min_lng is None:
                        self.min_lng = lng
                    if lng > self.max_lng or self.max_lng is None:
                        self.max_lng = lng
        if scenario.include_railways:
            for source in scenario.railways:
                for (lng, lat) in source[20]:
                    if lat < self.min_lat or self.min_lat is None:
                        self.min_lat = lat
                    if lat > self.max_lat or self.max_lat is None:
                        self.max_lat = lat
                    if lng < self.min_lng or self.min_lng is None:
                        self.min_lng = lng
                    if lng > self.max_lng or self.max_lng is None:
                        self.max_lng = lng
        if scenario.include_ships_in_transit:
            for source in scenario.ships_in_transit:
                for (lng, lat) in source[24]:
                    if lat < self.min_lat or self.min_lat is None:
                        self.min_lat = lat
                    if lat > self.max_lat or self.max_lat is None:
                        self.max_lat = lat
                    if lng < self.min_lng or self.min_lng is None:
                        self.min_lng = lng
                    if lng > self.max_lng or self.max_lng is None:
                        self.max_lng = lng

    def _get_bounds(self):
        if isinstance(self, ScenarioRun):
            self._get_bounds_helper(self.scenario)
        else:
            self._get_bounds_helper(self.scenario_1)
            self._get_bounds_helper(self.scenario_2)

    @property
    def mode_name(self):
        if self.model_type > 1:
            return "ANNUAL"
        else:
            return "HOURLY"

    @staticmethod
    def _merge_concentration_dicts(*dicts):
        result_dict = dict()
        all_keys = set()
        for d in dicts:
            for k in d.keys():
                all_keys.add(k)
        for key in all_keys:
            result_dict[key] = sum(d.get(key, 0) for d in dicts)
        return result_dict

    def _load_receptors_file(self, scenario):
        ds = tablib.Dataset()
        receptors = {}
        with open(self.receptor_file(scenario)) as receptor_list:
            ds.csv = receptor_list.read()
            receptors = {int(r[0]): Receptor(x=r[1], y=r[2]) for r in ds}
        return receptors

    def _load_concentrations_files(self, scenario):
        ds = tablib.Dataset()
        result_dicts = []
        if self.model_type > 1:
            model_field = self.model_type + 1
        else:
            model_field = 3

        area_concentrations = {}
        if scenario.include_area_sources and os.path.isfile(self.area_file(scenario)):
            with open(self.area_file(scenario)) as area_output:
                ds.csv = area_output.read()
                area_concentrations = {int(r[0]): float(r[model_field]) for
                                       r in ds}
                result_dicts.append(area_concentrations)
        point_concentrations = {}
        if scenario.include_point_sources and os.path.isfile(self.point_file(scenario)):
            with open(self.point_file(scenario)) as point_output:
                ds.csv = point_output.read()
                point_concentrations = {int(r[0]): float(r[model_field]) for
                                        r in ds}
                result_dicts.append(point_concentrations)
        rail_concentrations = {}
        if scenario.include_railways and os.path.isfile(self.rail_file(scenario)):
            with open(self.rail_file(scenario)) as rail_output:
                ds.csv = rail_output.read()
                rail_concentrations = {int(r[0]): float(r[model_field]) for
                                       r in ds}
                result_dicts.append(rail_concentrations)
        road_concentrations = {}
        if scenario.include_roads and os.path.isfile(self.road_file(scenario)):
            with open(self.road_file(scenario)) as road_output:
                ds.csv = road_output.read()
                road_concentrations = {int(r[0]): float(r[model_field]) for
                                       r in ds}
                result_dicts.append(road_concentrations)
        sit_concentrations = {}
        if scenario.include_ships_in_transit and os.path.isfile(self.sit_file(scenario)):
            with open(self.sit_file(scenario)) as sit_output:
                ds.csv = sit_output.read()
                sit_concentrations = {int(r[0]): float(r[model_field]) for
                                      r in ds}
                result_dicts.append(sit_concentrations)
        concentrations = self._merge_concentration_dicts(*result_dicts)
        return {
            "area": area_concentrations,
            "point": point_concentrations,
            "rail": rail_concentrations,
            "road": road_concentrations,
            "sit": sit_concentrations,
            "total": concentrations
        }


class ScenarioRun(Base, AbstractScenarioRun):
    __tablename__ = "scenario_run"
    scenario_run_id = sa.Column(sa.Integer, primary_key=True)
    scenario_id = sa.Column(sa.Integer, sa.ForeignKey("scenario.scenario_id"))
    user_id = sa.Column(sa.Text)
    tool = sa.Column(sa.Text)
    status = sa.Column(sa.Text)
    output_directory = sa.Column(sa.Text)
    results_file_name = sa.Column(sa.Text)
    model_type = sa.Column(sa.Integer)
    pollutant = sa.Column(sa.Text)
    model_min_value = sa.Column(sa.Float)
    model_max_value = sa.Column(sa.Float)
    scenario = orm.relationship(Scenario)
    min_lat = sa.Column(sa.Numeric(asdecimal=False))
    max_lat = sa.Column(sa.Numeric(asdecimal=False))
    min_lng = sa.Column(sa.Numeric(asdecimal=False))
    max_lng = sa.Column(sa.Numeric(asdecimal=False))
    last_update = sa.Column(sa.DateTime)

    def __init__(self, *args, **kwargs):
        super(ScenarioRun, self).__init__(*args, **kwargs)

    def prepare_run(self):
        dir_name = str(uuid.uuid4())
        self.output_directory = os.path.join(ctools_backend.settings.scenario_run_directory, dir_name)
        self.results_file_name = "%s_%s.tar.gz" % (self.scenario.safe_name, str(time.time()).replace(".", ""))
        self.temp_dir = tempfile.mkdtemp()
        try:
            os.mkdir(self.output_directory)
        except OSError:
            pass
        self._get_bounds()
        self.status = "running"
        self.last_update = datetime.datetime.now()

    @property
    def to_dict(self):
        return {
            "scenario_run_id": self.scenario_run_id,
            "tool": self.tool,
            "status": self.status,
            "model_type": self.model_type,
            "min_value": self.model_min_value,
            "max_value": self.model_max_value,
            "min_lat": self.min_lat,
            "max_lat": self.max_lat,
            "min_lng": self.min_lng,
            "max_lng": self.max_lng,
            "pollutant": self.pollutant,
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario.name,
            "last_update": self.last_update.isoformat()
        }

    @property
    def image_file(self):
        return os.path.join(self.output_directory, "concentrations.png")

    @property
    def legend_file(self):
        return os.path.join(self.output_directory, "concentrations_legend.png")

    def finalize_run(self):
        self.status = "processing"
        self.last_update = datetime.datetime.now()
        receptors = self._load_receptors_file(self.scenario)
        concentrations = self._load_concentrations_files(self.scenario)
        for receptor in concentrations["total"]:
            point = (receptors[receptor].lng, receptors[receptor].lat)
            self.results.append(ScenarioRunResultDataPoint(
                receptor_id=receptor,
                area_value=concentrations["area"].get(receptor, None),
                point_value=concentrations["point"].get(receptor, None),
                rail_value=concentrations["rail"].get(receptor, None),
                road_value=concentrations["road"].get(receptor, None),
                sit_value=concentrations["sit"].get(receptor, None),
                total_value=concentrations["total"].get(receptor, None),
                scenario_run=self,
                receptor_location=geo.point_to_point(point)
            ))

    def create_package(self):
        output_directory = os.path.join(self.temp_dir, self.scenario.safe_name)
        os.mkdir(output_directory)
        shutil.copy(os.path.join(self.output_directory, "concentrations.png"), self.temp_dir)
        shutil.copy(os.path.join(self.output_directory, "concentrations_legend.png"), self.temp_dir)
        shutil.copy(os.path.join(ctools_backend.settings.template_directory, "ctools.prj"), self.temp_dir)
        shutil.copy(os.path.join(self.output_directory, "CTOOLS_Inputs.txt"), output_directory)
        for filename in glob.glob(os.path.join(self.output_directory, "*.csv")):
            shutil.copy(filename, output_directory)
        starting_dir = os.getcwd()
        os.chdir(ctools_backend.settings.output_tar_directory)
        subprocess.call(["tar", "-C", self.temp_dir, "-czf", self.results_file_name, "."])
        os.chdir(starting_dir)
        self.status = "completed"
        self.last_update = datetime.datetime.now()

    def failed(self):
        self.status = "failed"
        self.last_update = datetime.datetime.now()

    def receptor_file(self, scenario=None):
        return os.path.join(self.output_directory, "receptors.csv")

    def area_file(self, scenario=None):
        return os.path.join(self.output_directory, "results_CTOOLS_%s_AREA_Output.csv" % self.mode_name)

    def point_file(self, scenario=None):
        return os.path.join(self.output_directory, "results_CTOOLS_%s_POINT_Output.csv" % self.mode_name)

    def rail_file(self, scenario=None):
        return os.path.join(self.output_directory, "results_CTOOLS_%s_RAIL_Output.csv" % self.mode_name)

    def road_file(self, scenario=None):
        return os.path.join(self.output_directory, "results_CTOOLS_%s_ROAD_Output.csv" % self.mode_name)

    def sit_file(self, scenario=None):
        return os.path.join(self.output_directory, "results_CTOOLS_%s_SIT_Output.csv" % self.mode_name)

    def generate_concentration_array(self, source_type=None):
        min_non_zero = 10 ** -6

        def transform_concentration(c):
            (x, y) = point_wkt_to_array(c[0])
            return x, y, max(c[1], min_non_zero)

        session = object_session(self)
        if not source_type:
            source_type = ScenarioRunResultDataPoint.total_value
        concentrations = session.query(ScenarioRunResultDataPoint.receptor_location, source_type)\
            .filter(ScenarioRunResultDataPoint.scenario_run_id == self.scenario_run_id).all()
        return numpy.array([transform_concentration(c) for c in concentrations])


class ComparisonScenarioRun(Base, AbstractScenarioRun):
    __tablename__ = "comparison_scenario_run"
    scenario_run_id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Text)
    status = sa.Column(sa.Text)
    tool = sa.Column(sa.Text)
    output_directory_1 = sa.Column(sa.Text)
    output_directory_2 = sa.Column(sa.Text)
    results_file_name = sa.Column(sa.Text)
    model_type = sa.Column(sa.Integer)
    pollutant = sa.Column(sa.Text)
    model_min_value = sa.Column(sa.Float)
    model_max_value = sa.Column(sa.Float)
    comparison_mode = sa.Column(sa.Integer)
    min_lat = sa.Column(sa.Numeric(asdecimal=False))
    max_lat = sa.Column(sa.Numeric(asdecimal=False))
    min_lng = sa.Column(sa.Numeric(asdecimal=False))
    max_lng = sa.Column(sa.Numeric(asdecimal=False))
    scenario_1_id = sa.Column(sa.Integer, sa.ForeignKey("scenario.scenario_id"))
    scenario_2_id = sa.Column(sa.Integer, sa.ForeignKey("scenario.scenario_id"))
    scenario_1 = orm.relationship(Scenario, primaryjoin=scenario_1_id == Scenario.scenario_id)
    scenario_2 = orm.relationship(Scenario, primaryjoin=scenario_2_id == Scenario.scenario_id)
    last_update = sa.Column(sa.DateTime)

    def __init__(self, *args, **kwargs):
        super(ComparisonScenarioRun, self).__init__(*args, **kwargs)

    def prepare_run(self):
        dir_name_1 = str(uuid.uuid4())
        dir_name_2 = str(uuid.uuid4())
        self.output_directory_1 = os.path.join(ctools_backend.settings.scenario_run_directory, dir_name_1)
        self.output_directory_2 = os.path.join(ctools_backend.settings.scenario_run_directory, dir_name_2)
        self.results_file_name = "%s_vs_%s_%s.tar.gz" % (self.scenario_1.safe_name, self.scenario_2.safe_name, str(time.time()).replace(".", ""))
        self.temp_dir = tempfile.mkdtemp()
        try:
            os.mkdir(self.output_directory_1)
            os.mkdir(self.output_directory_2)
        except OSError:
            pass
        self._get_bounds()
        self.status = "running"
        self.last_update = datetime.datetime.now()

    @property
    def to_dict(self):
        return {
            "scenario_run_id": self.scenario_run_id,
            "status": self.status,
            "tool": self.tool,
            "model_type": self.model_type,
            "min_value": self.model_min_value,
            "max_value": self.model_max_value,
            "min_lat": self.min_lat,
            "max_lat": self.max_lat,
            "min_lng": self.min_lng,
            "max_lng": self.max_lng,
            "pollutant": self.pollutant,
            "comparison_mode": self.comparison_mode,
            "scenario_1_id": self.scenario_1_id,
            "scenario_2_id": self.scenario_2_id,
            "scenario_1_name": self.scenario_1.name,
            "scenario_2_name": self.scenario_2.name,
            "last_update": self.last_update.isoformat()
        }

    @property
    def image_file(self):
        return os.path.join(self.output_directory_1, "concentrations.png")

    @property
    def legend_file(self):
        return os.path.join(self.output_directory_1, "concentrations_legend.png")

    @staticmethod
    def _relative(v1, v2):
        return (v1 or 0) - (v2 or 0)

    @staticmethod
    def _relative_percent(v1, v2):
        return 100 * ((v1 or 0) - (v2 or 0))/(v2 or v1 or 1)

    def finalize_run(self):
        self.status = "processing"
        self.last_update = datetime.datetime.now()
        receptors_1 = self._load_receptors_file(self.scenario_1)
        concentrations_1 = self._load_concentrations_files(self.scenario_1)
        receptors_2 = self._load_receptors_file(self.scenario_2)
        concentrations_2 = self._load_concentrations_files(self.scenario_2)
        if self.comparison_mode == 1:
            comp_f = self._relative
        else:
            comp_f = self._relative_percent
        data_points = {}
        for receptor_id in concentrations_1["total"]:
            receptor = receptors_1[receptor_id]
            area_val = concentrations_1["area"].get(receptor_id, None)
            point_val = concentrations_1["point"].get(receptor_id, None)
            rail_val = concentrations_1["rail"].get(receptor_id, None)
            road_val = concentrations_1["road"].get(receptor_id, None)
            sit_val = concentrations_1["sit"].get(receptor_id, None)
            total_val = concentrations_1["total"].get(receptor_id, None)
            data_points[receptor.x, receptor.y] = ComparisonScenarioRunResultDataPoint(
                receptor_id=receptor_id,
                scenario_1_area_value=area_val,
                scenario_1_point_value=point_val,
                scenario_1_rail_value=rail_val,
                scenario_1_road_value=road_val,
                scenario_1_sit_value=sit_val,
                scenario_1_total_value=total_val,
                scenario_2_area_value=None,
                scenario_2_point_value=None,
                scenario_2_rail_value=None,
                scenario_2_road_value=None,
                scenario_2_sit_value=None,
                scenario_2_total_value=None,
                area_value=comp_f(area_val, None),
                point_value=comp_f(point_val, None),
                rail_value=comp_f(rail_val, None),
                road_value=comp_f(road_val, None),
                sit_value=comp_f(sit_val, None),
                total_value=comp_f(total_val, None),
                scenario_run=self,
                receptor_location=geo.point_to_point((receptor.lng, receptor.lat))
            )
        for receptor_id in concentrations_2["total"]:
            receptor = receptors_2[receptor_id]
            area_val = concentrations_2["area"].get(receptor_id, None)
            point_val = concentrations_2["point"].get(receptor_id, None)
            rail_val = concentrations_2["rail"].get(receptor_id, None)
            road_val = concentrations_2["road"].get(receptor_id, None)
            sit_val = concentrations_2["sit"].get(receptor_id, None)
            total_val = concentrations_2["total"].get(receptor_id, None)
            if not (receptor.x, receptor.y) in data_points:
                data_points[receptor.x, receptor.y] = ComparisonScenarioRunResultDataPoint(
                    receptor_id=receptor_id,
                    scenario_1_area_value=None,
                    scenario_1_point_value=None,
                    scenario_1_rail_value=None,
                    scenario_1_road_value=None,
                    scenario_1_sit_value=None,
                    scenario_1_total_value=None,
                    scenario_2_area_value=area_val,
                    scenario_2_point_value=point_val,
                    scenario_2_rail_value=rail_val,
                    scenario_2_road_value=road_val,
                    scenario_2_sit_value=sit_val,
                    scenario_2_total_value=total_val,
                    area_value=comp_f(None, area_val),
                    point_value=comp_f(None, point_val),
                    rail_value=comp_f(None, rail_val),
                    road_value=comp_f(None, road_val),
                    sit_value=comp_f(None, sit_val),
                    total_value=comp_f(None, total_val),
                    scenario_run=self,
                    receptor_location=geo.point_to_point((receptor.lng, receptor.lat))
                )
            else:
                data_point = data_points[receptor.x, receptor.y]
                if receptor_id != data_point.receptor_id:
                    data_point.receptor_id = str(data_point.receptor_id) + "_" + str(receptor_id)
                data_point.scenario_2_area_value = area_val
                data_point.scenario_2_point_value = point_val
                data_point.scenario_2_rail_value = rail_val
                data_point.scenario_2_road_value = road_val
                data_point.scenario_2_sit_value = sit_val
                data_point.scenario_2_total_value = total_val
                data_point.area_value=comp_f(data_point.scenario_1_area_value, area_val),
                data_point.point_value=comp_f(data_point.scenario_1_point_value, point_val),
                data_point.rail_value=comp_f(data_point.scenario_1_rail_value, rail_val),
                data_point.road_value=comp_f(data_point.scenario_1_road_value, road_val),
                data_point.sit_value=comp_f(data_point.scenario_1_sit_value, sit_val),
                data_point.total_value=comp_f(data_point.scenario_1_total_value, total_val)
        self.results = data_points.values()

    def create_package(self):
        output_directory_1 = os.path.join(self.temp_dir, self.scenario_1.safe_name)
        output_directory_2 = os.path.join(self.temp_dir, self.scenario_2.safe_name)
        os.mkdir(output_directory_1)
        os.mkdir(output_directory_2)
        shutil.copy(os.path.join(self.output_directory_1, "concentrations.png"), self.temp_dir)
        shutil.copy(os.path.join(self.output_directory_1, "concentrations_legend.png"), self.temp_dir)
        shutil.copy(os.path.join(ctools_backend.settings.template_directory, "ctools.prj"), self.temp_dir)
        shutil.copy(os.path.join(self.output_directory_1, "CTOOLS_Inputs.txt"), output_directory_1)
        for filename in glob.glob(os.path.join(self.output_directory_1, "*.csv")):
            shutil.copy(filename, output_directory_1)
        shutil.copy(os.path.join(self.output_directory_2, "CTOOLS_Inputs.txt"), output_directory_2)
        for filename in glob.glob(os.path.join(self.output_directory_2, "*.csv")):
            shutil.copy(filename, output_directory_2)
        starting_dir = os.getcwd()
        os.chdir(ctools_backend.settings.output_tar_directory)
        subprocess.call(["tar", "-C", self.temp_dir, "-czf", self.results_file_name, "."])
        os.chdir(starting_dir)
        self.status = "completed"
        self.last_update = datetime.datetime.now()

    def failed(self):
        self.status = "failed"
        self.last_update = datetime.datetime.now()

    def receptor_file(self, scenario):
        if scenario == self.scenario_1:
            output_directory = self.output_directory_1
        else:
            output_directory = self.output_directory_2
        return os.path.join(output_directory, "receptors.csv")

    def area_file(self, scenario):
        if scenario == self.scenario_1:
            output_directory = self.output_directory_1
        else:
            output_directory = self.output_directory_2
        return os.path.join(output_directory, "results_CTOOLS_%s_AREA_Output.csv" % self.mode_name)

    def point_file(self, scenario):
        if scenario == self.scenario_1:
            output_directory = self.output_directory_1
        else:
            output_directory = self.output_directory_2
        return os.path.join(output_directory, "results_CTOOLS_%s_POINT_Output.csv" % self.mode_name)

    def rail_file(self, scenario):
        if scenario == self.scenario_1:
            output_directory = self.output_directory_1
        else:
            output_directory = self.output_directory_2
        return os.path.join(output_directory, "results_CTOOLS_%s_RAIL_Output.csv" % self.mode_name)

    def road_file(self, scenario):
        if scenario == self.scenario_1:
            output_directory = self.output_directory_1
        else:
            output_directory = self.output_directory_2
        return os.path.join(output_directory, "results_CTOOLS_%s_ROAD_Output.csv" % self.mode_name)

    def sit_file(self, scenario):
        if scenario == self.scenario_1:
            output_directory = self.output_directory_1
        else:
            output_directory = self.output_directory_2
        return os.path.join(output_directory, "results_CTOOLS_%s_SIT_Output.csv" % self.mode_name)

    def generate_concentration_array(self, source_type=None):
        def transform_concentration(c):
            (x, y) = point_wkt_to_array(c[0])
            if self.comparison_mode == 1:
                abs_val = numpy.abs(c[1])
                if -1 <= abs_val <= 1:
                    return x, y, 0
                return x, y, numpy.sign(c[1]) * numpy.log10(abs_val)
            else:
                return x, y, c[1]

        session = object_session(self)
        if not source_type:
            source_type = ComparisonScenarioRunResultDataPoint.total_value
        concentrations = session.query(ComparisonScenarioRunResultDataPoint.receptor_location, source_type)\
            .filter(ComparisonScenarioRunResultDataPoint.scenario_run_id == self.scenario_run_id).all()
        return numpy.array([transform_concentration(c) for c in concentrations])


class ScenarioRunResultDataPoint(Base):
    __tablename__ = "scenario_run_result_data_point"
    scenario_run_result_id = sa.Column(sa.Integer, primary_key=True)
    scenario_run_id = sa.Column(sa.Integer, sa.ForeignKey("scenario_run.scenario_run_id"))
    receptor_location = sa.Column(Geometry("POINT"))
    receptor_id = sa.Column(sa.Text)
    area_value = sa.Column(sa.Float)
    point_value = sa.Column(sa.Float)
    rail_value = sa.Column(sa.Float)
    road_value = sa.Column(sa.Float)
    sit_value = sa.Column(sa.Float)
    total_value = sa.Column(sa.Float)
    scenario_run = orm.relationship(ScenarioRun, backref="results")

    @property
    def to_dict(self):
        return {
            "scenario_run_result_id": self.scenario_run_result_id,
            "scenario_run_id": self.scenario_run_id,
            "receptor_location": geo.point_wkt_to_array(self.receptor_location),
            "area_value": self.area_value,
            "point_value": self.point_value,
            "rail_value": self.rail_value,
            "road_value": self.road_value,
            "sit_value": self.sit_value,
            "total_value": self.total_value
        }


class ComparisonScenarioRunResultDataPoint(Base):
    __tablename__ = "comparison_scenario_run_result_data_point"
    scenario_run_result_id = sa.Column(sa.Integer, primary_key=True)
    scenario_run_id = sa.Column(sa.Integer, sa.ForeignKey("comparison_scenario_run.scenario_run_id"))
    receptor_location = sa.Column(Geometry("POINT"))
    receptor_id = sa.Column(sa.Text)
    scenario_1_area_value = sa.Column(sa.Float)
    scenario_1_point_value = sa.Column(sa.Float)
    scenario_1_rail_value = sa.Column(sa.Float)
    scenario_1_road_value = sa.Column(sa.Float)
    scenario_1_sit_value = sa.Column(sa.Float)
    scenario_1_total_value = sa.Column(sa.Float)
    scenario_2_area_value = sa.Column(sa.Float)
    scenario_2_point_value = sa.Column(sa.Float)
    scenario_2_rail_value = sa.Column(sa.Float)
    scenario_2_road_value = sa.Column(sa.Float)
    scenario_2_sit_value = sa.Column(sa.Float)
    scenario_2_total_value = sa.Column(sa.Float)
    area_value = sa.Column(sa.Float)
    point_value = sa.Column(sa.Float)
    rail_value = sa.Column(sa.Float)
    road_value = sa.Column(sa.Float)
    sit_value = sa.Column(sa.Float)
    total_value = sa.Column(sa.Float)
    scenario_run = orm.relationship(ComparisonScenarioRun, backref="results")

    @property
    def to_dict(self):
        return {
            "scenario_run_result_id": self.scenario_run_result_id,
            "scenario_run_id": self.scenario_run_id,
            "receptor_location": geo.point_wkt_to_array(self.receptor_location),
            "scenario_1_area_value": self.scenario_1_area_value,
            "scenario_1_point_value": self.scenario_1_point_value,
            "scenario_1_rail_value": self.scenario_1_rail_value,
            "scenario_1_road_value": self.scenario_1_road_value,
            "scenario_1_sit_value": self.scenario_1_sit_value,
            "scenario_1_total_value": self.scenario_1_total_value,
            "scenario_2_area_value": self.scenario_2_area_value,
            "scenario_2_point_value": self.scenario_2_point_value,
            "scenario_2_rail_value": self.scenario_2_rail_value,
            "scenario_2_road_value": self.scenario_2_road_value,
            "scenario_2_sit_value": self.scenario_2_sit_value,
            "scenario_2_total_value": self.scenario_2_total_value,
            "area_value": self.area_value,
            "point_value": self.point_value,
            "rail_value": self.rail_value,
            "road_value": self.road_value,
            "sit_value": self.sit_value,
            "total_value": self.total_value
        }


class CensusBlockGroup(Base):
    __tablename__ = "census_block_groups"
    gid = sa.Column(sa.Integer, primary_key=True)
    geom = sa.Column(Geometry('MULTIPOLYGON'))

    @property
    def to_dict(self):
        try:
            return {
                "gid": self.gid,
                "geom": geo.multipolygon_to_point_list(self.geom)
            }
        except:
            print "bad census block group:", self.gid
            return {
                "gid": self.gid,
                "geom": None
            }


if __name__ == "__main__":
    session = Session()
    CensusBlockGroup.__table__.create()
    ScenarioRunResultDataPoint.__table__.create()
    ComparisonScenarioRunResultDataPoint.__table__.create()