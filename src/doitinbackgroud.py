#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# doitinbackgroud.py
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


import gi
try:
    gi.require_version('GLib', '2.0')
    gi.require_version('GObject', '2.0')
except Exception as e:
    print(e)
    exit(-1)
from gi.repository import GLib
from gi.repository import GObject
import os
import requests
import pprint
from progreso import Progreso
from concurrent import futures


def download(element, diib):
    if element is not None:
        diib.emit('start_one', element['name'])
        print('===============================')
        pprint.pprint(element)
        print('===============================')
        url = element['format']['url']
        adir = element['dir']
        aname = element['name']
        aext = element['format']['ext']
        headers = element['format']['http_headers']
        dest_file = os.path.join(adir, '%s.%s' % (aname, aext))
        try:
            r = requests.get(url, stream=True, headers=headers)
            with open(dest_file, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            # return dest_file
        except Exception as e:
            print('Error downloading...', e)
    else:
        diib.emit('start_one', '')
    diib.emit('end_one', 1.0)


class DoItInBackground(GObject.GObject):
    __gsignals__ = {
        'started': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (int,)),
        'ended': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (bool,)),
        'start_one': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (str,)),
        'end_one': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (float,)),
    }

    def __init__(self, title, parent, elements):
        GObject.GObject.__init__(self)
        self.elements = elements
        self.stopit = False
        self.ok = True
        self.progreso = Progreso(title, parent)
        self.progreso.set_total_size(len(elements))
        self.progreso.connect('i-want-stop', self.stop)
        self.connect('start_one', self.progreso.set_element)
        self.connect('end_one', self.progreso.increase)
        self.connect('ended', self.progreso.close)
        self.downloaders = []

    def emit(self, *args):
        GLib.idle_add(GObject.GObject.emit, self, *args)

    def stop(self, *args):
        if len(self.downloaders) > 0:
            for downloader in self.downloaders:
                downloader.cancel()
                self.emit('end_one', 1.0)

    def run(self):
        try:
            executor = futures.ThreadPoolExecutor(max_workers=4)
            for element in self.elements:
                downloader = executor.submit(download, element, self)
                self.downloaders.append(downloader)
            self.progreso.run()
        except Exception as e:
            self.ok = False
            print(e)
        self.emit('ended', self.ok)
