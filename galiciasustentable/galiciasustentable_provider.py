# -*- coding: utf-8 -*-

"""
/***************************************************************************
 GaliciaSustentable processing provider
                              -------------------
        begin                : 2020-04-14
        copyright            : (C) 2020 by Luigi Pirelli / GaliciaSustentable
        email                : luipir AT gmail DOT com
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

__author__ = 'Luigi Pirelli / GaliciaSustentable'
__date__ = '2020-04-14'
__copyright__ = '(C) 2020 by Luigi Pirelli / GaliciaSustentable'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import shutil
import fnmatch
import logging

from qgis.core import (
    QgsProcessingProvider,
    QgsMessageLog,
    Qgis,
    QgsApplication
)
from qgis.user import expressionspath
from processing.script import ScriptUtils
from processing.tools.system import userFolder, mkdir
from processing.core.ProcessingConfig import ProcessingConfig, Setting

from . import galiciasustentable_constants

PLUGIN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
MODELS_DIR = os.path.abspath(os.path.join(PLUGIN_DIR, 'processing', 'models'))
SCRIPTS_DIR = os.path.abspath(os.path.join(PLUGIN_DIR, 'processing', 'scripts'))
EXPRESSION_DIR = os.path.abspath(os.path.join(PLUGIN_DIR, 'expressions'))

class GaliciaSustentableProvider(QgsProcessingProvider):

    def __init__(self):
        QgsProcessingProvider.__init__(self)

    def load(self):
        ProcessingConfig.settingIcons[self.name()] = self.icon()
        # ProcessingConfig.addSetting(Setting(galiciasustentable_constants.PLUGIN_DOMAIN,
        #                                     galiciasustentable_constants.DEFAULT_OUT_DIR,
        #                                     self.tr('Base path where to store processing results'), ''))
        self.refreshAlgorithms()
        ProcessingConfig.readSettings()

        self.setDefaultSettings()

        return True

    def setDefaultSettings(self):
        """
        Set default setting values if not set, or set them as values stored in QgsSettings ini file
        """
        # read values from stored settings if any
        # defaultOutDir = ProcessingConfig.getSetting(galiciasustentable_constants.DEFAULT_OUT_DIR)

        # save setting in QgsSettings ini file setting default value if not already set a value
        # if not defaultOutDir:
        #     defaultOutDir = ProcessingConfig.getSetting(ProcessingConfig.OUTPUT_FOLDER)
        # ProcessingConfig.setSettingValue(galiciasustentable_constants.DEFAULT_OUT_DIR, defaultOutDir)


    def unload(self):
        self.unloadAllScripts()
        self.unloadAllModels()
        self.unloadAllExpressions()

        # ProcessingConfig.removeSetting(galiciasustentable_constants.DEFAULT_OUT_DIR)
        pass


    def loadAlgorithms(self):
        """
        Loads all algorithms belonging to this provider.
        """
        self.loadAllScripts()
        self.loadAllModels()
        self.loadAllExpressions()

        # add all py algs
        # from .galiciasustentable_algorithm import GaliciaSustentableAlgorithm
        # self.addAlgorithm(GaliciaSustentableAlgorithm())

    def id(self):
        """
        Returns the unique provider id, used for identifying the provider.
        """
        return 'GaliciaSustentable'

    def name(self):
        """
        Returns the provider name
        """
        return self.tr('GaliciaSustentable')

    def icon(self):
        return QgsProcessingProvider.icon(self)

    def longName(self):
        return self.name()

    def loadAllExpressions(self):
        """
        Install custom expressions.
        Method freely inspired by Resource Sharing plugin.
        """
        # Pass silently if the directory does not exist
        if not os.path.exists(EXPRESSION_DIR):
            return

        # Get all the script files in the plugin
        expressions_files = []
        for item in os.listdir(EXPRESSION_DIR):
            file_path = os.path.join(EXPRESSION_DIR, item)
            if fnmatch.fnmatch(file_path, '*.py'):
                expressions_files.append(file_path)

        for expression_file in expressions_files:
            # Install the processing file silently

            # firt trying to create symlink. If error (for filesystem and OS reasons), then copy it
            try:
                destination_file = os.path.join( expressionspath, os.path.basename(expression_file) )
                os.symlink(expression_file, destination_file)
            except OSError as e:
                message = "Could not link expression '" +str(expression_file) + "' trying copying it\n" + str(e)
                QgsMessageLog.logMessage(message,  galiciasustentable_constants.PLUGIN_DOMAIN, level=Qgis.Critical)

                try:
                    shutil.copy(expression_file, expressionspath)
                except OSError as e:
                    message = "Could not copy expression '" +str(expression_file) + "'\n" + str(e)
                    QgsMessageLog.logMessage(message,  galiciasustentable_constants.PLUGIN_DOMAIN, level=Qgis.Critical)



    def loadAllScripts(self):
        """
        Install processing custom scripts.
        Method freely inspired by Resource Sharing plugin.
        """
        # Pass silently if the directory does not exist
        if not os.path.exists(SCRIPTS_DIR):
            return

        # Get all the script files in the plugin
        processing_files = []
        for item in os.listdir(SCRIPTS_DIR):
            file_path = os.path.join(SCRIPTS_DIR, item)
            if fnmatch.fnmatch(file_path, '*.py'):
                processing_files.append(file_path)

        valid = 0
        for processing_file in processing_files:
            # Install the processing file silently

            # firt trying to create symlink. If error (for filesystem and OS reasons), then copy it
            try:
                destination_file = os.path.join( ScriptUtils.defaultScriptsFolder(), os.path.basename(processing_file) )
                os.symlink(processing_file, destination_file)
                valid += 1
            except OSError as e:
                message = "Could not link script '" +str(processing_file) + "' trying copying it\n" + str(e)
                QgsMessageLog.logMessage(message,  galiciasustentable_constants.PLUGIN_DOMAIN, level=Qgis.Critical)

                try:
                    shutil.copy(processing_file, ScriptUtils.defaultScriptsFolder())
                    valid += 1
                except OSError as e:
                    message = "Could not copy script '" +str(processing_file) + "'\n" + str(e)
                    QgsMessageLog.logMessage(message,  galiciasustentable_constants.PLUGIN_DOMAIN, level=Qgis.Critical)

        if valid > 0:
            self.refresh_script_provider()


    def loadAllModels(self):
        """        
        Install processing custom models.
        Method freely inspired by Resource Sharing plugin.
        Copy the models (*.model3) in the models directory of the
        provider to the user's processing model directory and refresh 
        the provider.
        """
        # Return silently if the directory does not exist
        if not os.path.exists(MODELS_DIR):
            return

        # Get all the model files under models
        model_files = []
        for item in os.listdir(MODELS_DIR):
            file_path = os.path.join(MODELS_DIR, item)
            if fnmatch.fnmatch(file_path, '*.model3'):
                model_files.append(file_path)
        valid = 0
        for model_file in model_files:
            # Install the model file silently

            # firt trying to create symlink. If error (for filesystem and OS reasons), then copy it
            try:
                destination_file = os.path.join( self.default_models_folder(), os.path.basename(model_file) )
                os.symlink(model_file, destination_file)
                valid += 1
            except OSError as e:
                message = "Could not link model '" +str(model_file) + "' trying copying it\n" + str(e)
                QgsMessageLog.logMessage(message,  galiciasustentable_constants.PLUGIN_DOMAIN, level=Qgis.Critical)

                try:
                    shutil.copy(model_file, self.default_models_folder())
                    valid += 1
                except OSError as e:
                    message = "Could not copy model '" +str(model_file) + "' trying copying it\n" + str(e)
                    QgsMessageLog.logMessage(message,  galiciasustentable_constants.PLUGIN_DOMAIN, level=Qgis.Critical)

        if valid > 0:
            self.refresh_Model_provider()

    def unloadAllExpressions(self):
        """Uninstall the installed expression."""
        if not os.path.exists(EXPRESSION_DIR):
            return
        # Remove the expressions files that are intalled by the
        # provider
        for item in os.listdir(EXPRESSION_DIR):
            file_path = os.path.join(EXPRESSION_DIR, item)
            if fnmatch.fnmatch(file_path, '*.py'):
                script_path = os.path.join(expressionspath, item)
                if os.path.exists(script_path):
                    os.remove(script_path)
        self.refresh_script_provider()

    def unloadAllScripts(self):
        """Uninstall the processing scripts from processing toolbox."""
        if not os.path.exists(SCRIPTS_DIR):
            return
        # Remove the processing script files that are intalled by the
        # provider
        for item in os.listdir(SCRIPTS_DIR):
            file_path = os.path.join(SCRIPTS_DIR, item)
            if fnmatch.fnmatch(file_path, '*.py'):
                script_path = os.path.join(ScriptUtils.defaultScriptsFolder(), item)
                if os.path.exists(script_path):
                    os.remove(script_path)
        self.refresh_script_provider()

    def unloadAllModels(self):
        """Uninstall the models from processing toolbox."""
        if not os.path.exists(MODELS_DIR):
            return
        # Remove the model files that are present in this collection
        for item in os.listdir(MODELS_DIR):
            file_path = os.path.join(MODELS_DIR, item)
            if fnmatch.fnmatch(file_path, '*.model3'):
                model_path = os.path.join(self.default_models_folder(), item)
                if os.path.exists(model_path):
                    os.remove(model_path)

        self.refresh_Model_provider()

    def default_models_folder(self):
        """Return the default location of the processing models folder."""
        folder = str(os.path.join(userFolder(), 'models'))
        mkdir(folder)
        return os.path.abspath(folder)

    def refresh_script_provider(self):
        """Refresh the processing script provider."""
        script_pr = QgsApplication.processingRegistry().providerById("script")
        if script_pr is not None:
            script_pr.refreshAlgorithms()

    def refresh_Model_provider(self):
        """Refresh the processing model provider."""
        mod_prov = QgsApplication.processingRegistry().providerById("model")
        if (mod_prov is not None):
            mod_prov.refreshAlgorithms()
