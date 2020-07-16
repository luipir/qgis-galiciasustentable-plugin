# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

import json
import copy
from functools import reduce
from qgis.PyQt.QtCore import (
    QCoreApplication,
    QVariant
)
from qgis.core import (QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFeatureSource,
                       QgsFeatureRequest,
                       QgsProject,
                       QgsProcessingParameterFeatureSink,
                       QgsFields,
                       QgsFeatureSink,
                       QgsFeature,
                       QgsField,
                       QgsFields,
                       QgsWkbTypes)
from qgis import processing

YEAR_COLUMN = 'año'

class Walker():
    """
    Navigate recursively the dictionary executin action in walked_dictionary 
    when a key is found.
    :param walked_dictionary: The dictionary to modify basing on some rule walking it's copy
    :type dict_to_modify: dict
    :param actions: A set of match key value/callback e.g. {'key':callback,...} where 
                    callback as the following API callback(key, target)
    :type actions: list of tuples

    code idea get from https://stackoverflow.com/questions/47983728/create-dynamic-level-nested-dict-from-a-list-of-objects
    """

    walked_dictionary = {}
    actions = {}
    trigger_keys = []
    guide = {}
    # Take trace of the nesting key during recursion
    nesting = []

    def __init__(self, walked_dictionary, actions):
        self.walked_dictionary = walked_dictionary
        self.actions = actions
        # get keys notw to avoid get every leaf
        self.trigger_keys = self.actions.keys()
        # A deep copy of walked_dictionary to avoid invalidate iterators
        self.guide = copy.deepcopy(self.walked_dictionary)
    
    def introspect(self, value=None):
        if value is None:
            value = self.guide
        if isinstance(value, dict):
            for key, val in value.items():
                self.nesting.append(key)
                self.introspect(val) # recursive
                del self.nesting[-1]
        elif isinstance(value, list):
            for index, val in enumerate(value):
                self.nesting.append(index)
                self.introspect(val) # recursive
                del self.nesting[-1]
        else:
            # manage a leaf, e.g. self.guide now contains the leaf value
            key = self.nesting[-1]
            if key in self.trigger_keys:
                callback = self.actions[key]
                target = reduce( lambda k, v: k[v], self.nesting[:-1], self.walked_dictionary)
                callback(key, target)

class SunburstDataPreparationProcessingAlgorithm(QgsProcessingAlgorithm):
    """
    Prepare data for Sunburst visualization in Grafana panel.
    If accept a JSON config and generate a JSON based on configuration.
    A JSON config is mainly used to configure output sunburst linking 
    data sources to sunburst leaf.
    JSON config lists all indexes have to be get values. Indexes have to be already loaded in QGIS
    as the table with metadata necessary to link index names to table and columns wioth values to reads
    and more data.
    The JSON configuration has the following format:
    {
        "name": "Vida inteligente", // this is the entry key to indexes_metadata table
                                    // where to get color table, reference to index table
        "children": [
        {
            "name": "Atractivo de ciudad",
            "children": [
            {
                "name": "Atractivo laboral/residencial",
                "children": [
                {
                    "name": "Autocontención laboral" ,
                    "size": 0.36           // take absolutly care that the SUM of all "size" of
                                           // all children HAVE to be 1 e.g. 0.36+0.24+.0.15+0.24
                },
                {
                    "name": "Saldo migratorio",
                    "size": 0.24
                }
                ]
            },
            {
                "name": "Atractivo turístico",
                "children": [
                {
                    "name": "Visitantes en la ciudad",
                    "size": 0.16
                },
                {
                    "name": "Visitantes que repiten",
                    "size": 0.24
                }
                ]
            }
            ]
        },
        {
            "name": "Salud",
            "children": [
            {
                "name": "Accesibilidad a recursos sanitarios",
                "children": [
                {
                    "name": "Proximidad ciudadana a un centro de atención primaria",
                    "size": 0.2
                }
                ]
            },
            {
                "name": "Recursos sanitarios",
                "children": [
                {
                    "name": "Capacidad sanitaria municipal de atención primaria",
                    "size": 0.3
                }
                ]
            },
            {
                "name": "Vida saludable",
                "children": [
                {
                    "name": "Esperanza de vida al nacer",
                    "size": 0.5
                }
                ]
            }
            ]
        }
        ]
    }
    """

    INPUT = 'INPUT'
    METADATA = 'METADATA'
    OUTPUT = 'OUTPUT'
    indexes_metadata = None # remember layer where storing index metadata
    feedback = None

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return SunburstDataPreparationProcessingAlgorithm()

    def name(self):
        return 'generatesunburst'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Sunburst data preparation')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('GaliciaSustentable')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'galiciasustentable'

    def shortHelpString(self):
        return self.tr("Prepare data for Sunburst visualization in Grafana panel")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input JSON configuration
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT,
                self.tr('JSON configuration file'),
                extension = 'json'
            )
        )

        # the table with metadata to get values configured in JSON config
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.METADATA,
                self.tr('Metadata table with configuration data'),
                [QgsProcessing.TypeVector],
                defaultValue = 'indexes_metadata'
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output generated sunburst JSONs by year')
            )
        )

    def getIndexMetadata(self, index_name):
        if not self.indexes_metadata:
            raise QgsProcessingException(self.tr('No index metadata layer setup'))
        
        request = QgsFeatureRequest().setFilterExpression('"display_name" = \'{}\''.format(index_name))
        features = self.indexes_metadata.getFeatures(request)
        features = [f for f in features]
        if len(features) != 1:
            raise QgsProcessingException(self.tr('Found: {} features instead of only 1 with expression: "{}" for index: "{}"').format(len(features), request.filterExpression().dump(), index_name))

        # get metadata in form o dict with column name and value
        metadata = dict(zip(features[0].fields().names(), features[0].attributes()))
        
        return metadata

    def name_callback(self, key, target, year):
        """
        A callback to manage when key is "name"
        """
        # get the index name, that should be the value of display_name in
        # indexs_metadata table
        index_name = target[key]
        self.feedback.pushInfo("Managing index: {}".format(index_name))

        # get the metadata associated to the diplay name
        index_metadata = self.getIndexMetadata(index_name)
        index_table_name = index_metadata['index_table_name']
        index_classes = index_metadata['classes'] # would be similar to: [{"low": 0,"high": 15,"value": "Bajo","color": "dark-red"},...]
        index_metric_column = index_metadata['metric_column'] # the column name inside index_table_name where to get the value
        index_hiperlinks = index_metadata.setdefault('hyperlinks', '<some hiperlinks>')


        # look for layer into the project having the name as:
        # index_name or index_table_name
        index_layer = QgsProject.instance().mapLayersByName(index_name)
        if len(index_layer) == 0:
            index_layer = QgsProject.instance().mapLayersByName(index_table_name)
        if (len(index_layer) == 0) or not index_layer[0].isValid():
            raise QgsProcessingException(self.tr('Index layer: "{}" or "{}" not loaded into project or invalid, load all index tables before!').format(index_name, index_table_name))
        index_layer = index_layer[0]

        # get the index value to the specified year
        expression = '"{}" = {}'.format(YEAR_COLUMN, year) # TODO: year column should be configurable
        request = QgsFeatureRequest()
        request.setFilterExpression(expression)
        features = index_layer.getFeatures(request)
        features = [f for f in features]
        if len(features) != 1:
            self.feedback.reportError(self.tr('Skipped! Found: {} features instead of only 1 with expression: "{}" for layer: "{}"').format(len(features), request.filterExpression().dump(), index_layer.name()))
            # then do nothing to the target
            return
        
        # convert index_classes json in dictionary
        try:
            index_classes = json.loads(index_classes)
        except Exception as ex:
            raise QgsProcessingException(self.tr('Configured index: "{}" classes are malformed: {}').format(index_name, str(ex)))

        # add the value to the target
        feature = features[0]
        percentage = feature.attribute(index_metric_column)
        if percentage == QVariant(): # manage if value in DB is NULL
            percentage = None
        target['percentage'] = percentage

        # basing of index_classes set evaluation string and related color representation
        # btw set before value to undefined in case the value is outside the intervals
        target['value'] = None if isinstance(target['percentage'], int) else target['percentage']
        target['color'] = 'black'
        if target['percentage'] is not None:
            for color_class in index_classes["classes"]:
                if (isinstance(target['percentage'], str) and
                    target['percentage'] == color_class["value"]):
                        target['color'] = color_class["color"]
                if (not isinstance(target['percentage'], str) and
                    target['percentage'] >= color_class["low"] and
                    target['percentage'] < color_class["high"]):
                        target['value'] = self.tr(color_class["value"])
                        target['color'] = color_class["color"]
        
        # add all hiperlinks
        target.setdefault('hiperlinks', [])
        for i, hyperlink in enumerate(index_hiperlinks.split(',')):
            target['hiperlinks'].append(hyperlink)

    def getAllYears(self, index_name):
        index_metadata = self.getIndexMetadata(index_name)
        index_table_name = index_metadata['index_table_name']

        # look for layer into the project having the name as:
        # index_name or index_table_name
        index_layer = QgsProject.instance().mapLayersByName(index_name)
        if len(index_layer) == 0:
            index_layer = QgsProject.instance().mapLayersByName(index_table_name)
        if (len(index_layer) == 0) or not index_layer[0].isValid():
            raise QgsProcessingException(self.tr('Index layer: "{}" or "{}" not loaded into project or invalid, load all indexes table before!').format(index_name, index_table_name))
        index_layer = index_layer[0]

        # get all years from all available records
        years = []
        for feature in index_layer.getFeatures():
            year = feature.attribute(YEAR_COLUMN)
            years.append(year)
        
        return years


    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        # need this to allwo callbaks to push messages or warnings
        self.feedback = feedback

        json_config_file = self.parameterAsFile(
            parameters,
            self.INPUT,
            context
        )

        self.indexes_metadata = self.parameterAsSource(
            parameters,
            self.METADATA,
            context
        )
        if self.indexes_metadata is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.METADATA))

        # set ouput vector/table 
        thefields = QgsFields()
        thefields.append(QgsField('min_date', QVariant.Date))
        thefields.append(QgsField('max_date', QVariant.Date))
        thefields.append(QgsField('json', QVariant.String))

        (sink, dest_id) = self.parameterAsSink(parameters,
                                               self.OUTPUT,
                                               context,
                                               thefields,
                                               QgsWkbTypes.NoGeometry)
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))
        
        # Check json config
        feedback.pushInfo(self.tr('Check JSON config validity'))
        try:
            with open(json_config_file, 'r') as f:
                json_config = json.load(f)
        except Exception as ex:
            raise QgsProcessingException(self.tr('Malformed JSON config: {}').format(str(ex)))

        # get the highest level of index and it's years
        highest_level_index = json_config['name']
        years = self.getAllYears(highest_level_index)
        self.feedback.pushInfo(self.tr('Years available for index: "{}" => {}').format(highest_level_index, years))

        # loop for each leaf to add parameter get as from configuration
        for year in years:
            self.feedback.pushInfo(self.tr('** Generating for year: {}').format(year))

            feature = QgsFeature()

            # create a deep copy of the config to work on (it will be modifed every loop)
            year_config = dict(copy.deepcopy(json_config))

            # the modifier is set to a fixed year
            year_callback = lambda key, index: self.name_callback(key, index, year)
            actions = {'name': year_callback}

            # now generate sunburst data modifing year_config
            sunburt_data_generator = Walker(year_config, actions)
            sunburt_data_generator.introspect()
            
            # create min_date and max_date values
            min_date = '{}-01-01 00:00:00'.format(year)
            max_date = '{}-01-01 00:00:00'.format(year+1)

            # add the new record if the output layer
            attrs = []
            attrs.append(min_date)
            attrs.append(max_date)
            attrs.append(json.dumps(year_config, ensure_ascii=False))
            feature.setAttributes(attrs)
            sink.addFeature(feature, QgsFeatureSink.FastInsert)

        # return
        return {self.OUTPUT: dest_id}
