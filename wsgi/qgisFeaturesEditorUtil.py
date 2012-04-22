# -*- coding: utf-8 -*-
from qgis.core import *
from PyQt4.QtCore import *

def getLayerFromRegByName(layersMap, layerName):
  result = None
  for mapLayerKey in layersMap:
    if layersMap[mapLayerKey].name() == layerName:
      result = layersMap[mapLayerKey]
  return result

def getConectionStringFromLayer(layer):
  result = None
  qgsDataSourceUri = getDataSourceUriFromLayer(layer)
  if None != qgsDataSourceUri:
    result = str(
    "host='"+qgsDataSourceUri.host()+
    "' dbname='"+qgsDataSourceUri.database()+
    "' user='"+qgsDataSourceUri.username()+
    "' password='"+qgsDataSourceUri.password()+"'"
    )
  return result

def getDataSourceUriFromLayer(layer):
  result = None
  if QgsMapLayer.VectorLayer == layer.type() and None !=layer.dataProvider():
    connectionURI = layer.dataProvider().dataSourceUri()
    result = QgsDataSourceURI(connectionURI)
  return result
