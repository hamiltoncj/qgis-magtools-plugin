import os
from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon
from .trackEnvelope import TrackEnvelopeAlgorithm

class MagToolsProvider(QgsProcessingProvider):

    def unload(self):
        QgsProcessingProvider.unload(self)

    def loadAlgorithms(self):
        self.addAlgorithm(TrackEnvelopeAlgorithm())
        
    '''def icon(self):
        return QIcon(os.path.dirname(__file__) + '/icon.png')'''
        
    def id(self):
        return 'magtools'

    def name(self):
        return 'Magnetometry tools'

    def longName(self):
        return self.name()
