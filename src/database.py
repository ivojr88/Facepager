#from requester import *
import sqlalchemy as sql
from sqlalchemy import Column, Integer, String,ForeignKey,Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine,event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref,sessionmaker,session,scoped_session
from sqlalchemy.engine import Engine

import json
from utilities import *
from dateutil import parser
import datetime
import os
from PySide.QtGui import *
from PySide.QtCore import *
from collections import OrderedDict
Base = declarative_base()

class Database(object):

    def __init__(self,parent):
        self.parent = parent
        self.connected=False
        self.filename=""

    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


    def connect(self,filename):
        try:
            if self.connected:
                self.disconnect()

            self.engine = create_engine('sqlite:///%s'%filename, convert_unicode=True)
            self.session = scoped_session(sessionmaker(autocommit=False,autoflush=False,bind=self.engine))
            Base.query = self.session.query_property()
            #Create a query attribute by inheritance from the declarative base
            Base.metadata.create_all(bind=self.engine)
            self.filename = filename
            self.connected = True
        except Exception as e:
            self.filename=""
            self.connected=False
            QMessageBox.critical(self.parent,"Facepager",str(e))

    def disconnect(self):
        if self.connected:
            self.session.close()

        self.filename=""
        self.connected=False

    def createconnect(self,filename):
        """ Creates a new file (overwrite existing?!) and connects the DB to that file"""
        self.disconnect()
        if os.path.isfile(filename):
            os.remove(filename)
        self.connect(filename)

    def commit(self):
        if self.connected:
            try:
                self.session.commit()
            except Exception as e:
                QMessageBox.critical(self.parent,"Facepager",str(e))
        else:
            QMessageBox.information(self.parent,"Facepager","No database connection")

    def rollback(self):
        if self.connected:
            try:
                self.session.rollback()
            except Exception as e:
                QMessageBox.critical(self.parent,"Facepager",str(e))
        else:
            QMessageBox.information(self.parent,"Facepager","No database connection")



class Node(Base):
        """
        This is the central class for all db-entries
        relevant to the data-view. It creates an empty node on __init__
        """
        __tablename__='Nodes'

        objectid=Column(String)
        objecttype=Column(String)
        querystatus=Column(String)
        querytype=Column(String)
        querytime=Column(String)
        queryparams_raw=Column("queryparams",Text)
        response_raw=Column("response",Text)
        id=Column(Integer,primary_key=True,index=True)
        parent_id = Column(Integer, ForeignKey('Nodes.id',ondelete='CASCADE'),index=True)
        children = relationship("Node",backref=backref('parent', remote_side='Node.id'))
        level=Column(Integer)
        childcount=Column(Integer)

        def __init__(self,objectid,parent_id=None):
            self.objectid=objectid
            self.parent_id=parent_id
            self.level=0
            self.childcount=0
            self.querystatus=''
            self.objecttype = 'seed'

        @property
        def response(self):
            """
            The response attribute holds the data (JSON) itself
            """
            if (self.response_raw == None):
                return {}
            else:
                return  json.loads(self.response_raw,object_pairs_hook=OrderedDict)

        @response.setter
        def response(self, response_raw):
            """
            Tries to dump the data as JSON
            Note: Error Handling should be implemented here
            """
            self.response_raw = json.dumps(response_raw)

        @property
        def queryparams(self):
            """
            The queryparams atrribute holds the Query-Parameters
            spcified in the API-Tab
            """
            if (self.queryparams_raw == None):
                return {}
            else:
                return  json.loads(self.queryparams_raw)

        @queryparams.setter
        def queryparams(self, queryparams_raw):
            self.queryparams_raw = json.dumps(queryparams_raw)

        def getResponseValue(self,key,encoding=None):
            value=getDictValue(self.response,key)
            if encoding and isinstance(value, unicode):
                return value.encode(encoding)
            else:
                return value

        @property
        def objectid_encoded(self):
            return self.objectid.encode('utf-8')







