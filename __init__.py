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
 This script initializes the plugin, making it known to QGIS.
"""

__author__ = 'testInvisEdit'
__date__ = '2020-04-09'
__copyright__ = '(C) 2020 by testInvisEdit'


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load testInvisEdit class from file testInvisEdit.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .testInvisEdit import testInvisEditPlugin
    return testInvisEditPlugin()
