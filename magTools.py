# -*- coding: utf-8 -*-
"""
/***************************************************************************
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
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsApplication
import processing
import webbrowser

import os
from .provider import MagToolsProvider

class MagTools(object):
    def __init__(self, iface):
        self.iface = iface
        self.provider = MagToolsProvider()        

    def initGui(self):
        """Create the menu & tool bar items within QGIS"""
        # icon = QIcon(os.path.dirname(__file__) + "/icon.png")
        self.tracEnvelopeAction = QAction("MXPDA Track Envelope", self.iface.mainWindow())
        self.tracEnvelopeAction.triggered.connect(self.showMagEnvelopeDialog)
        self.tracEnvelopeAction.setCheckable(False)
        self.iface.addPluginToMenu("Magnetometry Tools", self.tracEnvelopeAction)
        
        # Add the processing provider
        QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self):
        """Remove the plugin menu item and icon from QGIS GUI."""
        self.iface.removePluginMenu("Magnetometry Tools", self.tracEnvelopeAction)
        QgsApplication.processingRegistry().removeProvider(self.provider)
    
    def showMagEnvelopeDialog(self):
        """Display the KML Dialog window."""
        results = processing.execAlgorithmDialog('magtools:trackenvelope', {})
        
        
        
