# -*- coding: utf-8 -*-
"""
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import re
from qgis.PyQt.QtCore import QObject, QVariant, QCoreApplication
from qgis.PyQt.QtGui import QIcon

from qgis.core import QgsCoordinateReferenceSystem, QgsPoint, QgsPolygon, QgsLineString, QgsFeature, QgsGeometry, QgsFields, QgsField, QgsWkbTypes

from qgis.core import (QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSink)

import traceback

def tr(string):
    return QCoreApplication.translate('Processing', string)


class TrackEnvelopeAlgorithm(QgsProcessingAlgorithm):
    """
    Algorithm to import create track envelopes for MXPDA.
    """
    PrmInputLayer = 'InputLayer'
    PrmOutputLayer = 'OutputLayer'
    PrmProbeCount = 'ProbeCount'
    PrmOutputType = 'OutputType'

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.PrmInputLayer,
                tr('Input point layer'),
                [QgsProcessing.TypeVectorPoint])
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.PrmOutputType,
                tr('Visual display type'),
                options=[tr('Scan envelope'),tr('Probe lines')],
                defaultValue=0,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PrmProbeCount,
                tr('Number of probes'),
                QgsProcessingParameterNumber.Integer,
                defaultValue=16,
                minValue=2,
                maxValue=16,
                optional=True)
            )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.PrmOutputLayer,
                tr('Output layer'),
                optional=False)
            )

    def processAlgorithm(self, parameters, context, feedback):
        self.parameters = parameters
        self.context = context
        num_probe = self.parameterAsInt(parameters, self.PrmProbeCount, context)
        graph_type = self.parameterAsInt(parameters, self.PrmOutputType, context)
        source = self.parameterAsSource(parameters, self.PrmInputLayer, context)
        first_error = True
        
        srcCRS = source.sourceCrs()
        f = QgsFields()
        f.append(QgsField("fid", QVariant.LongLong))
        f.append(QgsField("trace", QVariant.String))
        if graph_type == 0:
            (sink, dest_id) = self.parameterAsSink(parameters,
                self.PrmOutputLayer, context, f,
                QgsWkbTypes.Polygon, srcCRS)
                
            cur_trace = None
            self.probe_first = []
            self.probe_last = []
            self.fid = 1
            iterator = source.getFeatures()
            fields = source.fields()
            trace_idx = fields.lookupField('trace')
            probe_idx = fields.lookupField('probe')
            if trace_idx == -1 or probe_idx == -1:
                feedback.reportError('Invalid data')
                raise QgsProcessingException('Invalid data')
                
            
            for feature in iterator:
                pt = feature.geometry().asPoint()
                try:
                    probe = int(feature[probe_idx])
                    trace = feature[trace_idx]
                except:
                    continue
                if probe < 1 or probe > num_probe:
                    continue
                if trace != cur_trace:
                    if cur_trace is not None:
                        self.outputPolygon(sink, cur_trace)
                    self.probe_first = []
                    self.probe_last = []
                    cur_trace = trace
                if probe == 1:
                    self.probe_first.append(QgsPoint(pt))
                if probe == num_probe:
                    self.probe_last.append(QgsPoint(pt))
                
            if len(self.probe_first) != 0:
                self.outputPolygon(sink, cur_trace)
        else:
            f.append(QgsField("probe", QVariant.Int))
            (sink, dest_id) = self.parameterAsSink(parameters,
                self.PrmOutputLayer, context, f,
                QgsWkbTypes.LineStringM, srcCRS)
                
            cur_trace = None
            self.probes = [[] for _ in range(num_probe)]
            self.fid = 1
            iterator = source.getFeatures()
            fields = source.fields()
            trace_idx = fields.lookupField('trace')
            probe_idx = fields.lookupField('probe')
            value_idx = fields.lookupField('value')
            if trace_idx == -1 or probe_idx == -1:
                feedback.reportError('Invalid data')
                raise QgsProcessingException('Invalid data')
                
            
            for feature in iterator:
                pt = QgsPoint(feature.geometry().asPoint())
                try:
                    probe = int(feature[probe_idx])
                    trace = feature[trace_idx]
                    value = float(feature[value_idx])
                    pt.addMValue(value)
                except:
                    if first_error:
                        s = traceback.format_exc()
                        feedback.pushInfo(s)
                        first_error = False
                    continue
                if probe < 1 or probe > num_probe:
                    continue
                if trace != cur_trace:
                    if cur_trace is not None:
                        self.outputLines(sink, cur_trace, num_probe)
                    self.probes = [[] for _ in range(num_probe)]
                    cur_trace = trace
                self.probes[probe-1].append(pt)
                
            self.outputLines(sink, cur_trace, num_probe)
            
        return {self.PrmOutputLayer: dest_id}

    def outputLines(self, sink, trace, num_probe):
        for i in range(num_probe):
            if len(self.probes[i]) == 0:
                continue
            linestring = QgsLineString(self.probes[i])
            f = QgsFeature()
            f.setGeometry(QgsGeometry(linestring))
            f.setAttributes([self.fid, trace, i+1])
            self.fid += 1
            sink.addFeature(f)

    def outputPolygon(self, sink, trace):
        # Append the rest of the points
        for pt in reversed(self.probe_last):
            self.probe_first.append(pt)
        # Close the polygon by appending the first point
        self.probe_first.append(self.probe_first[0])
        
        linestring = QgsLineString(self.probe_first)
        poly = QgsPolygon()
        poly.setExteriorRing(linestring)
        f = QgsFeature()
        f.setGeometry(QgsGeometry(poly))
        f.setAttributes([self.fid, trace])
        self.fid += 1
        sink.addFeature(f)
        
    def name(self):
        return 'trackenvelope'

    def displayName(self):
        return tr('MXPDA Track Envelope')

    def group(self):
        return tr('Magnetometry algorithms')

    def groupId(self):
        return 'magalg'

    def createInstance(self):
        return TrackEnvelopeAlgorithm()

