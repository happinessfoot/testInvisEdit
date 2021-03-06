# -*- coding: utf-8 -*-

"""
/***************************************************************************
 testInvisEdit
                                 A QGIS plugin
 testInvisEdit
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2020-04-09
        copyright            : (C) 2020 by testInvisEdit
        email                : testInvisEdit
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'testInvisEdit'
__date__ = '2020-04-09'
__copyright__ = '(C) 2020 by testInvisEdit'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import sys
import inspect

from qgis.core import QgsProcessingAlgorithm, QgsApplication,QgsProject
from .testInvisEdit_provider import testInvisEditProvider
from PyQt5.QtWidgets import QMessageBox,QWidget
from PyQt5.QtSql import *
from PyQt5.QtCore import QSettings,QObject
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProject,QgsFeatureRequest,QgsVectorLayerUndoCommandDeleteFeature,QgsMapLayerStore,QgsEditFormConfig,QgsEditorWidgetSetup,QgsDefaultValue,QgsExpression,QgsRectangle)
from qgis import utils
from qgis.gui import QgsMapMouseEvent,QgsMapTool,QgsMapCanvas,QgsMapToolEmitPoint 
import uuid 

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)


class testInvisEditPlugin(object):
    layerConnectedTax = None
    layerConnectedQuart = None
    def __init__(self):
        self.provider = None
        iface = utils.iface
        self.quart = None
        self.canvas = utils.iface.mapCanvas()
        iface.layerTreeView().currentLayerChanged.connect(self.connectSignalOnLayers)
        #qgsProject = QgsProject()
        self.copiedTax = []
        self.deletedTax = []
        self.unionFeatures = []
        self.newQuartals = []
        self.splitedQuarts = []
        self.splitedLines = {}
        self.connectedSignalsTax = False
        self.connectedSignalsQuart = False
        self.splitFeature = False
        self.addedQuarts = []
        self.deletedQuarts = []
        self.splitedQuartsFeatures = []
        self.taxFeaturesList = []
        self.layerTax = None
        self.connectSignalOnLayers()
        self.checkCommit = False
        self.unionQuarts = []
        self.cuttedQuart = []
        self.taxChanged = []
    def clickedOnMap(self, pointOnMap, buttonUsed):
       print(buttonUsed,pointOnMap)
    def initProcessing(self):
        """Init Processing provider for QGIS >= 3.8."""
        self.provider = testInvisEditProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        self.disconnect()
        QgsApplication.processingRegistry().removeProvider(self.provider)
    
    def findQuartByTax(self,taxLayer):
        source = taxLayer.source().split(' ')
        dbName = str(source[0].split('=')[1])
        dbHost = str(source[1].split('=')[1])
        dbPort = str(source[2].split('=')[1])
        layerList = QgsProject.instance().mapLayers().values()
        layerQuart = None
        for layer in layerList:
            if(dbName in layer.source() and dbHost in layer.source() and dbPort in layer.source() and 'table="public"."t_forestquarter"' in layer.source() and 'type=MultiPolygon' in layer.source()):
                layerQuart = layer
                break
        return layerQuart
    
    def disconnect(self):
        if(self.layerConnectedQuart!=None):
            self.layerConnectedQuart.beforeCommitChanges.disconnect()
            self.layerConnectedQuart.featureAdded.disconnect()
            self.layerConnectedQuart.featureDeleted.disconnect()
            self.layerConnectedQuart.committedFeaturesAdded.disconnect()
            self.layerConnectedQuart.committedGeometriesChanges.disconnect()
            self.layerConnectedQuart = None
        
        if(self.layerConnectedTax!=None):
            self.layerConnectedTax.beforeCommitChanges.disconnect()
            self.layerConnectedTax.committedFeaturesAdded.disconnect()
            self.layerConnectedTax.featureAdded.disconnect()
            self.layerConnectedTax.beforeEditingStarted.disconnect()
            self.layerConnectedTax = None
    
    def display_point(self,pointTool):
        try:
            print(pointTool.x(), pointTool.y())
        except AttributeError:
            pass
    def testClick(self,e,btn):
        print(e,btn)
    
    def connectSignalOnLayers(self):
        self.quart = None
        layerList = QgsProject.instance().mapLayers().values()
        if(len(layerList)>0):
            self.showEditForm(utils.iface.activeLayer())
            layer = utils.iface.activeLayer()
            print(layer.publicSource())
            if('table="public"."t_taxationisolated"' in layer.publicSource() and 'type=MultiPolygon' in layer.publicSource()): 
                self.hideEditForm(layer)
                print("connect hide")
                layer.beforeCommitChanges.connect(self.beforeCommitSignal_Tax)
                layer.committedFeaturesAdded.connect(self.afterCommit)
                layer.featureAdded.connect(self.addTaxSignal)
                layer.beforeEditingStarted.connect(self.testEditStart)
                #layer.geometryChanged.connect(self.testTaxGeoChange)
                self.layerConnectedTax = layer
                self.quart = self.findQuartByTax(layer)
            elif(self.layerConnectedTax!=None):
                self.layerConnectedTax.beforeCommitChanges.disconnect()
                self.layerConnectedTax.committedFeaturesAdded.disconnect()
                self.layerConnectedTax.featureAdded.disconnect()
                self.layerConnectedTax.beforeEditingStarted.disconnect()
                self.layerConnectedTax = None
              
            if ('table="public"."t_forestquarter"' in layer.publicSource() and 'type=MultiPolygon' in layer.publicSource()):
                self.setQuartValues(layer)
                print("connect quart signals")
                layer.beforeCommitChanges.connect(self.beforeCommitSignal_Quart)
                layer.featureAdded.connect(self.testChange)
                layer.featureDeleted.connect(self.deleteQuart)
                layer.committedFeaturesAdded.connect(self.afterCommit_quart)
                layer.committedGeometriesChanges.connect(self.afterGeometryChange)
                self.layerConnectedQuart = layer
            elif(self.layerConnectedQuart!=None):
                self.layerConnectedQuart.beforeCommitChanges.disconnect()
                self.layerConnectedQuart.featureAdded.disconnect()
                self.layerConnectedQuart.featureDeleted.disconnect()
                self.layerConnectedQuart.committedFeaturesAdded.disconnect()
                self.layerConnectedQuart.committedGeometriesChanges.disconnect()
                self.layerConnectedQuart = None
                
    def testEditStart(self):
        self.taxChanged.clear()
    def testTaxGeoChange(self,fid,geometry):
        print("geoChangeGeom")
        # for feat in layer.editBuffer().addedFeatures():
            # if('_' in feat['primarykey'] and feat['primarykey'].split('_')[0] not in self.taxChanged.keys()):
                # self.taxChanged[feat['primarykey'].split('_')[0]]=0
    # def layerChanged_AddSignals(self,i):
        # #print("test")
        # self.quart = None
        # layerList = QgsProject.instance().mapLayers().values()
        # for layer in layerList:
            # if ('table="public"."t_forestquarter"' in layer.publicSource() and 'type=MultiPolygon' in layer.publicSource()):
                # self.quart = layer
            # if('table="public"."t_taxationisolated"' in layer.publicSource() and 'type=MultiPolygon' in layer.publicSource()): 
                # layer.beforeCommitChanges.connect(self.editPrimarykey)
                # layer.committedFeaturesAdded.connect(self.afterCommit)
    def deleteQuart(self,fid):
        layer = utils.iface.activeLayer()
        feature = layer.getFeature(fid)
        indexList = []
        #print(fid)
        if(len(self.unionFeatures)>0):
            for i in range(len(self.unionFeatures)):
                for j in range(len(self.unionFeatures[i])):
                    if(fid==self.unionFeatures[i][j][2]):
                        indexList.append(i)
                        break
            #print(self.unionFeatures)
            j = 0
            #print(indexList)
            for i in indexList:
                del self.unionFeatures[i-j]
                j=j+1
        print("del")
        print(self.unionFeatures)
    
    def getLine(self,featureSource,layer):
        mainGuid = featureSource['primarykey'].split('_')[0]
        print(mainGuid)
        mainFeatureId = None
        if(self.splitedLines.get(mainGuid)==None):
            for feature in layer.getFeatures(QgsFeatureRequest(QgsExpression('primarykey=\'%s\'' % mainGuid))):
                mainFeatureId = feature.id()
                if(self.splitedLines.get(feature.id())==None):
                    self.splitedLines[feature.id()] = [feature.id()]
                
        self.splitedLines[mainFeatureId].append(featureSource.id())
        
        # for feature in layer.getFeatures(QgsFeatureRequest(QgsExpression('primarykey=\'%s\'' % findGuid))):
            # polygon1 = feature.geometry()
            # polygon1.convertToSingleType()
            # list1 = polygon1.asPolygon()[0]
            # polygon2 = featureSource.geometry()
            # polygon2.convertToSingleType()
            # list2 = polygon2.asPolygon()[0]
            # listEquals = list(set(list1) & set(list2))
            # print(listEquals)
    def addTaxSignal(self,fid):
        layer = utils.iface.activeLayer()
        feature = layer.getFeature(fid)
        if(feature['primarykey']!=None):
            if('_' in feature['primarykey'] and feature['primarykey'].split('_')[0] not in self.taxChanged):
                self.taxChanged.append(feature['primarykey'].split('_')[0])
        # if(feature['primarykey']!=None and '_' in feature['primarykey']):
            # featureSource = None
            # for feat in layer.getFeatures('"primarykey"=\''+feature['primarykey'].split('_')[0]+'\''):
                # featureSource = feat
            # if(self.quart!=None):
                # pointTax = feature.geometry().pointOnSurface()
                # pointTaxXY = feature.geometry().pointOnSurface().asPoint()
                # self.quart.selectByRect(QgsRectangle(pointTaxXY.x(),pointTaxXY.y(),pointTaxXY.x()-0.000000001,pointTaxXY.y()-0.000000001))
                # for quartFeature in self.quart.getSelectedFeatures():
                    # if(pointTax.within(quartFeature.geometry())):
                        # #feature.setAttribute(layer.fields().indexFromName('forestquarter'),quartFeature['primarykey'])
                        # layer.changeAttributeValue(feature.id(),layer.fields().indexFromName('forestquarter'),quartFeature['primarykey'])
                        # print(feature['primarykey'])
                        # print(quartFeature['primarykey'])
                # if(featureSource!=None):
                    # pointTax = featureSource.geometry().pointOnSurface()
                    # pointTaxXY = featureSource.geometry().pointOnSurface().asPoint()
                    # self.quart.selectByRect(QgsRectangle(pointTaxXY.x(),pointTaxXY.y(),pointTaxXY.x()-0.000000001,pointTaxXY.y()-0.000000001))
                    # for quartFeature in self.quart.getSelectedFeatures():
                        # if(pointTax.within(quartFeature.geometry())):
                            # #featureSource.setAttribute(layer.fields().indexFromName('forestquarter'),quartFeature['primarykey'])
                            # layer.changeAttributeValue(featureSource.id(),layer.fields().indexFromName('forestquarter'),quartFeature['primarykey'])
                            # print(featureSource['primarykey'])
                            # print(quartFeature['primarykey'])
    def testChange(self,fid):
        #print(fid)
        
        layer = utils.iface.activeLayer()
        feature = layer.getFeature(fid)
        #print(feature.geometry().asWkt())
        if(feature['primarykey']!=None and '_' not in feature['primarykey'] ):
            if(len(self.getUnionFeatures(feature,layer))>0):
                self.unionFeatures.append(self.getUnionFeatures(feature,layer))
        print(self.unionFeatures)  
            
    
    def getUnionFeatures(self,unionFeature,layer):
        ids = layer.editBuffer().deletedFeatureIds()
        combinedFeatures=list()
        print("unionGet")
        for feature in layer.dataProvider().getFeatures( QgsFeatureRequest().setFilterFids( ids ) ):
            if(feature.geometry().pointOnSurface().within(unionFeature.geometry()) and feature['primarykey']!=unionFeature['primarykey']):
                combinedFeatures.append([feature['primarykey'],unionFeature['primarykey'],unionFeature.id()])
                print("union:",unionFeature.id())
        return combinedFeatures
    
    def setQuartValues(self,layer):
        db = self.getDataBaseConnection(layer)
        mapConfig = []
        if(db.open() == False):
            QMessageBox.critical(None, "Error", db.lastError().text())
        query = db.exec_("select primarykey,name from t_foresty where hierarchy is not null order by name")
        while(query.next()):
            #print(str(query.value('name')))
            mapConfig.append({str(query.value('name')):str(query.value('primarykey'))})
            query.next()
        #print(mapConfig)
        db.close()
        config = {'map': mapConfig}
        newEditor = QgsEditorWidgetSetup('ValueMap',config)
        layer.setEditorWidgetSetup(layer.fields().indexFromName('forestdistrict'),newEditor)
        layer.setEditorWidgetSetup(layer.fields().indexFromName('primarykey'),QgsEditorWidgetSetup('UuidGenerator',{}))
        layer.setDefaultValueDefinition(layer.fields().indexFromName('number'),QgsDefaultValue('-1'))
        editConfig = layer.editFormConfig()
        editConfig.setReadOnly(layer.fields().indexFromName('primarykey'),True)
        editConfig.setReadOnly(layer.fields().indexFromName('number'),True)
        layer.setEditFormConfig(editConfig)
        
        
    
    def hideEditForm(self,layer):
        print("hideEidt")
        editConfig = layer.editFormConfig()
        editConfig.setSuppress(1)
        layer.setEditFormConfig(editConfig)
        
    def showEditForm(self,layer):
        editConfig = layer.editFormConfig()
        editConfig.setSuppress(0)
        layer.setEditFormConfig(editConfig)
    
    def getDataBaseConnection(self,layer):
        source = layer.source().split(' ')
        dbName = str(source[0].split('=')[1].replace('\'',''))
        dbHost = str(source[1].split('=')[1].replace('\'',''))
        dbPort = str(source[2].split('=')[1].replace('\'',''))
        dbLogin= str(source[3].split('=')[1].replace('\'',''))
        dbPassword= str(source[4].split('=')[1].replace('\'',''))
        
        db = QSqlDatabase.addDatabase("QPSQL");
        db.setDatabaseName(dbName)
        db.setHostName(dbHost)
        db.setPort(int(dbPort))
        db.setUserName(dbLogin)
        db.setPassword(dbPassword)
        return db
    
    def findDeleteFeatures(self,layer,guid,featureId):
        #print("guidFind:",guid)
        idPrimarykey = layer.fields().indexFromName('primarykey')
        ids = layer.editBuffer().deletedFeatureIds()
        for feature in layer.dataProvider().getFeatures( QgsFeatureRequest().setFilterFids( ids ) ):
            if(feature.attributes()[idPrimarykey] == guid and feature.id()!=featureId):
                #print(feature['primarykey'],feature.id())
                return feature
        return None
    
    def findFeature(self,layer,guid):
        idPrimarykey = layer.fields().indexFromName('primarykey')
        for feature in layer.getFeatures('"primarykey"=\''+guid+'\''):
            if(feature.attributes()[idPrimarykey]==guid):
                return feature
        return None
    
    def getNumberOfQuart(self,quartLayer,forestyGuid):
        max=-1
        for f in quartLayer.getFeatures('"forestdistrict"=\''+forestyGuid+'\''):
            if(f['number']!=None):
                if max<int(f['number']):
                    max=int(f['number'])
        return max
    
    def getMaxNumberOfTax(self,taxLayer,quartGuid):
        max = -1
        for f in taxLayer.getFeatures('"forestquarter"=\''+quartGuid+'\''):
            if(f['number']!=None):
                if max<int(f['number']):
                    max=int(f['number'])
        return max
    
    def afterGeometryChange(self,layerid,changedGeometries):
        print("afterGeomtry")
        layer = utils.iface.activeLayer()

                        
    def afterCommit_quart(self,layerid,addedFeatures):
        layer = utils.iface.activeLayer()
        print("aftercommit")
        for feature in addedFeatures:
            if(feature['primarykey'] in self.addedQuarts):
                self.addTax(layer,feature['primarykey'],feature.geometry())
            if(len(self.cuttedQuart)>0):
                layerTax = self.getLayerTaxByQuart(layer)
                editTaxFeatures = []
                for quartGuid in self.cuttedQuart:
                    for featureTax in layerTax.getFeatures('"forestquarter"=\''+quartGuid+'\''):
                        if featureTax.geometry().pointOnSurface().within(feature.geometry()):
                            editTaxFeatures.append(featureTax['primarykey'])
                db = self.getDataBaseConnection(layer)
                if(db.open() == False):
                    QMessageBox.critical(None, "Error", db.lastError().text())
                for tax in editTaxFeatures:
                    db.exec_("update t_taxationisolated set forestquarter='"+feature['primarykey']+"' where primarykey='"+tax+"'")
                    print(db.lastError().text)

                
        # db = self.getDataBaseConnection(layer)
        # for quart in self.deletedQuarts:
            # query=db.exec_("delete from t_forestquarter where primarykey='"+quart+"'")
        # db.close()
        # self.unionFeatures.clear()    
        # self.checkCommit = False 
        
    def afterCommit(self,layerid,addedFeatures):
        layer = utils.iface.activeLayer()
        db = self.getDataBaseConnection(layer)
        if(db.open() == False):
            QMessageBox.critical(None, "Error", db.lastError().text())
        for taxes in self.copiedTax:
            query = db.exec_("select copy_attr_isoletad('"+taxes[1]+"'::uuid,'"+taxes[0]+"'::uuid)")
        for taxes in self.deletedTax:
            query = db.exec_("delete from t_taxationisolated where primarykey='"+taxes+"'")
        db.close()
        
            
    
    # def editPrimarykeyTest(self):
        # layer = utils.iface.activeLayer()
        # idx = layer.fields().indexFromName('primarykey')
        # editBuffer = layer.editBuffer()
        # for fid in editBuffer.addedFeatures():
            # feature = layer.getFeature(fid)
            # print(feature['primarykey'],feature.id())

    
    def updateAllFeaturesTax(self,layer,quartPkDest,quartPkSource):
        db = self.getDataBaseConnection(layer)
        if(db.open() == False):
            QMessageBox.critical(None, "Error", db.lastError().text())
        query = db.exec_("select max(number) as num from t_taxationisolated where forestquarter='"+quartPkDest+"'")
        query.next()
        maxNumber = str(query.value(0))
        print(quartPkDest[0])
        print(maxNumber)
        query = db.exec_("update t_taxationisolated set number=number+"+maxNumber+",forestquarter='"+quartPkDest+"' where forestquarter='"+quartPkSource+"'")
        print(query.lastError().text())
        print("update t_taxationisolated set number=number+"+str(maxNumber)+",forestquarter='"+quartPkDest+"' where forestquarter='"+quartPkSource+"'")
        db.close()
        
    def deleteQuarts(self,layer,guid):
        idPrimarykey = layer.fields().indexFromName('primarykey')
        ids = layer.editBuffer().deletedFeatureIds()
        for feature in layer.dataProvider().getFeatures( QgsFeatureRequest().setFilterFids( ids ) ):
            if(feature.attributes()[idPrimarykey] == guid and feature.id()!=featureId):
                print(feature['primarykey'],feature.id())
                return feature
        return None
    
    def addTax(self,layer,quartPrimarykey,quartGeometry):
        print(quartGeometry.asWkt())
        db = self.getDataBaseConnection(layer)
        if(db.open() == False):
            QMessageBox.critical(None, "Error", db.lastError().text())
        query = QSqlQuery(db)
        query.prepare("INSERT INTO t_taxationisolated (primarykey, number, land_category,categoryofprotection,forestquarter,area,shape,centroid_shape,actual) VALUES (uuid_generate_v4(),:number, :land_category,:categoryofprotection,:forestquarter,:area,st_multi(ST_GeomFromText('"+quartGeometry.asWkt()+"',"+str(layer.sourceCrs().postgisSrid())+")),ST_GeomFromText(:centroid_shape),'1')")
        query.bindValue(":number",1)
        query.bindValue(":land_category","a8decd9a-268f-4a18-b334-220867640700")
        query.bindValue(":categoryofprotection","13e62ba4-f30f-4edf-99d6-2942a421edfd")
        query.bindValue(":forestquarter",quartPrimarykey)
        query.bindValue(":area",round(quartGeometry.area()/10000,1))
        query.bindValue(":centroid_shape",quartGeometry.pointOnSurface().asWkt())
        if(query.exec_()):
            db.commit()
        else:
            print(query)
            print(query.lastError().text())
    
    def getLayerTaxByQuart(self,layerQuart):
        source = layerQuart.source().split(' ')
        dbName = str(source[0].split('=')[1])
        dbHost = str(source[1].split('=')[1])
        dbPort = str(source[2].split('=')[1])
        layerList = QgsProject.instance().mapLayers().values()
        layerTax = None
        for layer in layerList:
            if(dbName in layer.source() and dbHost in layer.source() and dbPort in layer.source() and 'table="public"."t_taxationisolated"' in layer.source() and 'type=MultiPolygon' in layer.source()):
                layerTax = layer
                break
        return layerTax
        
    def editEnableTax(self,layerQuart):
        source = layerQuart.source().split(' ')
        dbName = str(source[0].split('=')[1])
        dbHost = str(source[1].split('=')[1])
        dbPort = str(source[2].split('=')[1])
        layerList = QgsProject.instance().mapLayers().values()
        layerTax = None
        for layer in layerList:
            if(dbName in layer.source() and dbHost in layer.source() and dbPort in layer.source() and 'table="public"."t_taxationisolated"' in layer.source() and 'type=MultiPolygon' in layer.source()):
                layerTax = layer
                break
        if(layerTax!=None):
            layerTax.startEditing()
            return layerTax
        return None

    def findQuartInLayer(self,layer,guid):
        for feature in layer.getFeatures('"primarykey"=\''+guid+'\''):
            return feature
        return None
    
    def updateTaxWhichInQuart(self,layer,quartGuid,quartGeometry):
        db = self.getDataBaseConnection(layer)
        if(db.open() == False):
            QMessageBox.critical(None, "Error", db.lastError().text())
    
    def findQuartInUnionQuart(self,layer,unionQuart):
        ids = layer.editBuffer().deletedFeatureIds()
        for feat in layer.dataProvider().getFeatures(QgsFeatureRequest(ids)):
            if(feat.geometry().pointOnSurface().within(unionQuart.geometry())):
                return feat
        return None
        
    def beforeCommitSignal_Quart(self):
        print("edit before")
        print(self.unionFeatures)
        quartGuid = None
        self.allChangedQuarts = []
        self.addedQuarts = []
        self.copiedTax = []
        layer = utils.iface.activeLayer()
        idx = layer.fields().indexFromName('primarykey')
        editBuffer = layer.editBuffer()
        checkQuart = False
        #print(editBuffer)
        self.taxFeaturesList = []
        self.layerTax = None
        self.deletedQuarts = []
        self.checkCommit = True
        self.cuttedQuart = []
        print("iamhere")
        for items in self.unionFeatures:
            for quart in items:
                print(quart)
                self.updateAllFeaturesTax(layer,quart[1],quart[0])
        for fid in editBuffer.addedFeatures():
            feature = layer.getFeature(fid)
            if(feature['primarykey']!=None):
                findFeature = self.findDeleteFeatures(layer,feature['primarykey'],feature.id())
                #print(findFeature['primarykey'])
                if(findFeature != None):
                    if(findFeature.id()!=feature.id()):
                        newGuid = str(uuid.uuid4())
                        #number = self.getMaxNumberOfTax(layer,feature['forestquarter'])+1
                        undodelete = QgsVectorLayerUndoCommandDeleteFeature(editBuffer,findFeature.id())
                        undodelete.undo()
                        #print('Before:',feature['primarykey'],feature.id())
                        editBuffer.changeGeometry(findFeature.id(),feature.geometry())
                        #print('After:',feature['primarykey'],feature.id())
                        #layer.changeAttributeValue(fid,layer.fields().indexFromName('number'),number)
                        #print(feature['primarykey'])
                        editBuffer.deleteFeature(feature.id())
                # elif('_' in feature['primarykey']):
                    # number = self.getMaxNumberOfTax(layer,feature['forestquarter'])+1
                    # newGuid = str(uuid.uuid4())
                    # #print('Before:',feature['primarykey'],feature.id())
                    # self.copiedTax.append([feature['primarykey'].split('_')[0],newGuid])
                    # layer.changeAttributeValue(fid,layer.fields().indexFromName('primarykey'),newGuid)
                    # layer.changeAttributeValue(fid,layer.fields().indexFromName('number'),number)
                    # #print('After:',feature['primarykey'],feature.id())
                    # layer.changeAttributeValue(fid,layer.fields().indexFromName('centroid_shape'),"SRID="+str(layer.sourceCrs().postgisSrid())+";"+feature.geometry().pointOnSurface().asWkt())
                elif('_' in feature['primarykey']):
                    newGuid =  str(uuid.uuid4())
                    layer.changeAttributeValue(fid,layer.fields().indexFromName('primarykey'),newGuid)
                    #findFeature = self.findQuartInLayer(layer,feature['primarykey'].split('_')[0])
                    self.cuttedQuart.append(feature['primarykey'].split('_')[0])
                    # # if(feature['primarykey'].split('_')[0] not in self.splitedQuartsFeatures):
                        # # self.splitedQuartsFeatures.append(feature['primarykey'].split('_')[0])
                    # # for featureTax in self.layerTax.getFeatures('"forestquarter"=\''+feature['primarykey'].split('_')[0]+'\''):
                        # # if feature.geometry().contains(featureTax.geometry()) == False and featureTax.id() not in self.taxFeaturesList:
                            # # self.taxFeaturesList.append(featureTax.id())
                            # # print("add",featureTax.id())
                        # # elif(featureTax.id() in self.taxFeaturesList):
                            # # print("remove",featureTax.id())
                            # # self.taxFeaturesList.remove(featureTax.id())
                            # # self.layerTax.changeAttributeValue(featureTax.id(),self.layerTax.fields().indexFromName('forestquarter'),newGuid)
                    # self.addedQuarts.append(newGuid)
                    # layer.changeAttributeValue(fid,layer.fields().indexFromName('primarykey'),newGuid)
                    # number = self.getNumberOfQuart(layer,feature['forestdistrict'])+1
                    # layer.changeAttributeValue(fid,layer.fields().indexFromName('number'),number)
                    
                    # number = self.getMaxNumberOfTax(layer,feature['forestquarter'])+1
                    # newGuid = str(uuid.uuid4())
                    # #print('Before:',feature['primarykey'],feature.id())
                    # findFeature = self.findDeleteFeatures(layer,feature['primarykey'].split('_')[0],feature.id())
                    # if(findFeature!=None):
                        # #print(findFeature.id(),findFeature['primarykey'])
                        # undodelete = QgsVectorLayerUndoCommandDeleteFeature(editBuffer,findFeature.id())
                        # undodelete.undo()
                        # self.deletedTax.append(findFeature['primarykey'])
                    # self.copiedTax.append([feature['primarykey'].split('_')[0],newGuid])
                    # layer.changeAttributeValue(fid,layer.fields().indexFromName('primarykey'),newGuid)
                    # layer.changeAttributeValue(fid,layer.fields().indexFromName('number'),number)
                    # #print('After:',feature['primarykey'],feature.id())
                    # layer.changeAttributeValue(fid,layer.fields().indexFromName('centroid_shape'),"SRID="+str(layer.sourceCrs().postgisSrid())+";"+feature.geometry().pointOnSurface().asWkt())
            else:
                newGuid =  str(uuid.uuid4())
                layer.changeAttributeValue(fid,layer.fields().indexFromName('primarykey'),newGuid)
                number = self.getNumberOfQuart(layer,feature['forestdistrict'])+1
                layer.changeAttributeValue(fid,layer.fields().indexFromName('number'),number)
                layer.changeAttributeValue(fid,layer.fields().indexFromName('centroid_shape'),"SRID="+str(layer.sourceCrs().postgisSrid())+";"+feature.geometry().pointOnSurface().asWkt())
                layer.changeAttributeValue(fid,layer.fields().indexFromName('area'),round(feature.geometry().area()/10000))
                self.addedQuarts.append(newGuid)
                

        # ids = layer.editBuffer().deletedFeatureIds()
        # for feature in layer.dataProvider().getFeatures( QgsFeatureRequest().setFilterFids( ids ) ):
            # undodelete = QgsVectorLayerUndoCommandDeleteFeature(editBuffer,feature.id())
            # undodelete.undo()
            # self.deletedQuarts.append(feature)
            
        # if(len(self.unionQuarts)>0):
            # layerTax = self.editEnableTax(layer)
            # for featureQuart in self.deletedQuarts:
                # for feature in layerTax.getFeatures("forestquarter='"+featureQuart['primarykey']+"'"):
                    # if(feature.geometry().pointOnSurface().within(featureQuart.geometry())):
                        # print(featureQuart['primarykey'])
                        # layerTax.changeAttributeValue(feature.id(),layerTax.fields().indexFromName('forestquarter'),featureQuart['primarykey'])
    
   
    
    def beforeCommitSignal_Tax(self):
        print("edit before")
        quartGuid = None
        self.copiedTax = []
        self.deletedTax = []
        layer = utils.iface.activeLayer()
        idx = layer.fields().indexFromName('primarykey')
        editBuffer = layer.editBuffer()
        #print(editBuffer)
        for fid in editBuffer.addedFeatures():
            feature = layer.getFeature(fid)
            #print(feature.id(),feature['primarykey'])
            if(feature['primarykey']!=None):
                #print("beforecommit:",feature.id(),feature['primarykey'])
                findFeature = self.findDeleteFeatures(layer,feature['primarykey'],feature.id())
                if(findFeature != None):
                    if(findFeature.id() != feature.id()):
                        newGuid = str(uuid.uuid4())
                        #number = self.getMaxNumberOfTax(layer,feature['forestquarter'])+1
                        undodelete = QgsVectorLayerUndoCommandDeleteFeature(editBuffer,findFeature.id())
                        undodelete.undo()
                        #print('Before:',feature['primarykey'],feature.id())
                        editBuffer.changeGeometry(findFeature.id(),feature.geometry())
                        editBuffer.changeAttributeValue(feature.id(),idx,newGuid)
                        #print('After:',feature['primarykey'],feature.id())
                        #layer.changeAttributeValue(fid,layer.fields().indexFromName('number'),number)
                        editBuffer.deleteFeature(feature.id())
                        
                elif('_' in feature['primarykey']):
                    number = self.getMaxNumberOfTax(layer,feature['forestquarter'])+1
                    newGuid = str(uuid.uuid4())
                    #print('Before:',feature['primarykey'],feature.id())
                    findFeature = self.findDeleteFeatures(layer,feature['primarykey'].split('_')[0],feature.id())
                    
                    if(findFeature!=None):
                        #print(findFeature.id(),findFeature['primarykey'])
                        undodelete = QgsVectorLayerUndoCommandDeleteFeature(editBuffer,findFeature.id())
                        undodelete.undo()
                        self.deletedTax.append(findFeature['primarykey'])
                    self.copiedTax.append([feature['primarykey'].split('_')[0],newGuid])
                    layer.changeAttributeValue(fid,layer.fields().indexFromName('primarykey'),newGuid)
                    layer.changeAttributeValue(fid,layer.fields().indexFromName('number'),number)
                    #print('After:',feature['primarykey'],feature.id())
                    layer.changeAttributeValue(fid,layer.fields().indexFromName('centroid_shape'),"SRID="+str(layer.sourceCrs().postgisSrid())+";"+feature.geometry().pointOnSurface().asWkt())
                    if(self.quart!=None):
                        if(feature.geometry().centroid().within(feature.geometry())):
                            pointTax = feature.geometry().centroid()
                        else:
                            pointTax = feature.geometry().pointOnSurface()
                        pointXYTax = pointTax.asPoint()
                        self.quart.selectByRect(QgsRectangle(pointXYTax.x(),pointXYTax.y(),pointXYTax.x()-0.00000001,pointXYTax.y()-0.00000001))
                        for quart in self.quart.getSelectedFeatures():
                            if pointTax.within(quart.geometry()):
                                layer.changeAttributeValue(feature.id(),layer.fields().indexFromName('forestquarter'),quart['primarykey'])
                                break
            else:
                if(self.quart!=None):
                    for quartFeature in self.quart.getFeatures():
                        if feature.geometry().intersects(quartFeature.geometry()):
                            quartGuid=quartFeature['primarykey']
                else:
                    QMessageBox.information(None,'DEBUG',u'???????? ?? ???????????????????? t_forestquarter ???? ????????????, ???????????????? ?? ?????????????????? ????????????????????')
                if quartGuid!= None:
                    layer.changeAttributeValue(fid,layer.fields().indexFromName('primarykey'),str(uuid.uuid4()))
                    layer.changeAttributeValue(fid,layer.fields().indexFromName('land_category'),'a8decd9a-268f-4a18-b334-220867640700')
                    layer.changeAttributeValue(fid,layer.fields().indexFromName('categoryofprotection'),'13e62ba4-f30f-4edf-99d6-2942a421edfd')
                    layer.changeAttributeValue(fid,layer.fields().indexFromName('forestquarter'),quartGuid)
                    number = self.getMaxNumberOfTax(layer,quartGuid)+1
                    layer.changeAttributeValue(fid,layer.fields().indexFromName('number'),number)
                    layer.changeAttributeValue(fid,layer.fields().indexFromName('centroid_shape'),"SRID="+str(layer.sourceCrs().postgisSrid())+";"+feature.geometry().pointOnSurface().asWkt())
                    layer.changeAttributeValue(fid,layer.fields().indexFromName('area'),round(feature.geometry().area()/10000,1))
                else:
                    QMessageBox.information(None,'DEBUG',u'?????????? ???? ???????????????????????? ?? ??????????????????, ???????????????? ???? ?????????????????? ?????? ????????????????, ?????????????????? ?????????????? ?????? ?????????????????? ?????????? ?? ???????????? ??????????')
        if(self.quart!=None):
            for tax in self.taxChanged:
                feature = None
                for feat in layer.getFeatures('"primarykey"=\''+tax+'\''):
                    feature = feat
                if(feature!=None):
                    if(feature.geometry().centroid().within(feature.geometry())):
                        pointTax = feature.geometry().centroid()
                    else:
                        pointTax = feature.geometry().pointOnSurface()
                    pointXYTax = pointTax.asPoint()
                    self.quart.selectByRect(QgsRectangle(pointXYTax.x(),pointXYTax.y(),pointXYTax.x()-0.00000001,pointXYTax.y()-0.00000001))
                    for quart in self.quart.getSelectedFeatures():
                        if pointTax.within(quart.geometry()):
                            layer.changeAttributeValue(feature.id(),layer.fields().indexFromName('forestquarter'),quart['primarykey'])
                            break
        self.taxChanged.clear()
                