#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# comun.py
#
# This file is part of YouTube-Indicator
#
# Copyright (C) 2014 - 2017
# Lorenzo Carbonell Cerezo <lorenzo.carbonell.cerezo@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import locale
import gettext


def is_package():
    return not os.path.dirname(os.path.abspath(__file__)).endswith('src')


PARAMS = {
            'first-time': True,
            'version': '',
            'theme': 'light',
            'autostart': False,
            'monitor-clipboard': True,
            'download-dir': os.path.expanduser('~')
            }


APP = 'youtube-indicator'
APPCONF = APP + '.conf'
APPDATA = APP + '.data'
APPNAME = 'YouTube-Indicator'
CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.config')
CONFIG_APP_DIR = os.path.join(CONFIG_DIR, APP)
CONFIG_FILE = os.path.join(CONFIG_APP_DIR, APPCONF)
DATA_FILE = os.path.join(CONFIG_APP_DIR, APPDATA)
AUTOSTART_DIR = os.path.join(CONFIG_DIR, 'autostart')
FILE_AUTO_START = os.path.join(
    AUTOSTART_DIR, 'youtube-indicator-autostart.desktop')
if not os.path.exists(CONFIG_APP_DIR):
    os.makedirs(CONFIG_APP_DIR)

print(os.path.dirname(os.path.abspath(__file__)))

if is_package():
    ROOTDIR = '/opt/extras.ubuntu.com/youtube-indicator/share/'
    LANGDIR = os.path.join(ROOTDIR, 'locale-langpack')
    APPDIR = os.path.join(ROOTDIR, APP)
    ICONDIR = os.path.join(APPDIR, 'icons')
    SOCIALDIR = os.path.join(APPDIR, 'social')
    CHANGELOG = os.path.join(APPDIR, 'changelog')
    FILE_AUTO_START_ORIG = os.path.join(
        APPDIR, 'youtube-indicator-autostart.desktop')
else:
    ROOTDIR = os.path.dirname(__file__)
    LANGDIR = os.path.join(ROOTDIR, 'template1')
    APPDIR = os.path.join(ROOTDIR, APP)
    ICONDIR = os.path.normpath(os.path.join(ROOTDIR, '../data/icons'))
    SOCIALDIR = os.path.normpath(os.path.join(ROOTDIR, '../data/social'))
    DEBIANDIR = os.path.normpath(os.path.join(ROOTDIR, '../debian'))
    CHANGELOG = os.path.join(DEBIANDIR, 'changelog')
    FILE_AUTO_START_ORIG = os.path.join(
        os.path.normpath(os.path.join(ROOTDIR, '../data')),
        'youtube-indicator-autostart.desktop')
ICON = os.path.join(ICONDIR, 'youtube-indicator.svg')
STATUS_ICON = {}
STATUS_ICON['light'] = os.path.join(ICONDIR, 'youtube-indicator-light.svg')
STATUS_ICON['dark'] = os.path.join(ICONDIR, 'youtube-indicator-dark.svg')
DISABLED_ICON = {}
DISABLED_ICON['light'] = os.path.join(
    ICONDIR, 'youtube-indicator-light-disabled.svg')
DISABLED_ICON['dark'] = os.path.join(
    ICONDIR, 'youtube-indicator-dark-disabled.svg')
DOWNLOADING_ICON = {}
DOWNLOADING_ICON['light'] = os.path.join(
    ICONDIR, 'youtube-indicator-downloading-light.svg')
DOWNLOADING_ICON['dark'] = os.path.join(
    ICONDIR, 'youtube-indicator-downloading-dark.svg')

f = open(CHANGELOG, 'r')
line = f.readline()
f.close()
pos = line.find('(')
posf = line.find(')', pos)
VERSION = line[pos+1:posf].strip()
if not is_package():
    VERSION = VERSION + '-src'
try:
    current_locale, encoding = locale.getdefaultlocale()
    language = gettext.translation(APP, LANGDIR, [current_locale])
    language.install()
    _ = language.gettext
except Exception as e:
    _ = str
