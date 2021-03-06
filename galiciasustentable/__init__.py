# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GaliciaSustentable
                                 A QGIS plugin
 GaliciaSustentable processing provider
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
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
 This script initializes the plugin, making it known to QGIS.
"""

__author__ = 'Luigi Pirelli / GaliciaSustentable'
__date__ = '2020-04-14'
__copyright__ = '(C) 2020 by Luigi Pirelli / GaliciaSustentable'


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load GaliciaSustentable class from file GaliciaSustentable.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from .galiciasustentable import GaliciaSustentablePlugin
    return GaliciaSustentablePlugin(iface)
