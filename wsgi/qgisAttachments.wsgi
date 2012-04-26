# -*- coding: utf-8 -*-
from webob import Request
from webob import Response
import json
import psycopg2
import base64
import sys
import re
from lxml import etree


def application(environ, start_response):
  request = Request(environ)
  responseText = ''
  if(request.GET['func']=='GetFileList'):
    return GetFileList(request, start_response)
  if(request.GET['func']=='GetFile'):
    return GetFile(request, start_response)

def getConnectionStringFromRequest(request):
  baseLayerName = request.GET['layer']
  qgisFile = request.GET['qgisFile']
  xmlQgisProject = getProjectXml(qgisFile)
  result = getConectionStringFromLayer(xmlQgisProject, baseLayerName)
  return result

def GetFileList(request, start_response):
  baseLayerName = request.GET['layer']
  featureId = request.GET['feature']
  qgisFile = request.GET['qgisFile']

  metaTableName = baseLayerName+'_meta'
  attachList = []
  sql='SELECT "ID", tag, meta, mimetype, fk_obj from ' 
  sql+=metaTableName # TODO SQL Injection here!!!
  sql+=" where fk_obj=%(fk_obj)s and tag='attachment' "
  conn = psycopg2.connect(getConnectionStringFromRequest(request))
  curr = conn.cursor()
  curr.execute(sql,{"fk_obj":featureId})
  result = curr.fetchone()
  while(None != result):
    metaObject = {}
    metaObject["ID"] = result[0]
    metaObject["tag"] = result[1]
    metaObject["meta"] = result[2]
    metaObject["mimeType"] = result[3]
    if metaObject["mimeType"] == None:
      metaObject["mimeType"]="application/octet-stream"

    metaObject["feature"]=featureId
    metaObject["layer"]=baseLayerName
    metaObject["qgisFile"]=qgisFile
    metaObject["table"]=metaTableName
    attachList.append(metaObject)
    result = curr.fetchone()
  curr.close()
  conn.close()
  responseText = json.dumps(attachList)
  status = '200 OK'
  response_headers = [('Content-type', 'text/plain'),
                        ('Content-Length', str(len(responseText)))]
  start_response(status, response_headers)
  return [responseText]

def GetFile(request, start_response):
  objectId = request.GET['id']
  metaTableName = request.GET['table']
  sql='SELECT mimetype, meta, data from ' 
  sql+=metaTableName  # TODO SQL Injection here, better 
                      # to have dict of table names and select name there!!!
                      # this dict could be obtained from the file
  sql+=' where "ID"=%(obj_id)s'
  conn = psycopg2.connect(getConnectionStringFromRequest(request))
  curr = conn.cursor()
  curr.execute(sql,{"obj_id":objectId})
  result = curr.fetchone()
  metaObject = {}
  while(None != result):
    metaObject["mimeType"] = result[0]
    metaObject["meta"] = result[1]
    metaObject["data"] = base64.b64decode(result[2])
    result = curr.fetchone()
  curr.close()
  conn.close()
  
  if metaObject["mimeType"] == None:
    metaObject["mimeType"]="application/octet-stream"
  
  status = '200 OK'
  response_headers = [('Content-type', metaObject["mimeType"]),
      ('Content-Disposition','attachment; filename="'+metaObject["meta"]+'"'),
      ('Content-Transfer-Encoding','binary'),
      ('Accept-Ranges','bytes'),
      ('Content-Length', str(len(metaObject["data"])))]
  start_response(status, response_headers)
  return [metaObject["data"]]

def getProjectXml(filePath):
  return etree.parse(filePath)

def getLayerByName(projectXml, layerName):
  result = projectXml.xpath('//projectlayers/maplayer/layername[text()=\''+layerName+'\']/..')
  if 0 < len(result):
    result = result[0]
  else:
    result = None
  return result

def getConectionStringFromLayer(projectXml, layerName):
  result = None
  mapLayerXml = getLayerByName(projectXml, layerName)
  if None != mapLayerXml:
    xmlLayerDataSource = mapLayerXml.xpath('datasource')
    if 0 < len(xmlLayerDataSource):
      strLayerDataSource = xmlLayerDataSource[0].text
      strHost = re.search('host(\s*)=(\s*)\S*', strLayerDataSource).group(0)
      strDbName = re.search('dbname(\s*)=(\s*)\S*', strLayerDataSource).group(0)
      strUser = re.search('user(\s*)=(\s*)\S*', strLayerDataSource).group(0)
      strPassword = re.search('password(\s*)=(\s*)\'.*?\'', strLayerDataSource).group(0)
      result = strHost +" "+ strDbName +" "+ strUser+" "+strPassword
  return result
