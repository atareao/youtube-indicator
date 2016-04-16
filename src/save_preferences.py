#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# save_preferences.py
#
# This file is part of YouTube-Indicator
#
# Copyright (C) 2014
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
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GdkPixbuf
import comun
import urllib.request
from comun import _
import sys
sys.path.insert(1, '/usr/lib/python2.7/dist-packages/')
import youtube_dl
from youtube_dl.extractor.youtube import YoutubeIE
import operator


class SaveDialog(Gtk.Dialog):
    def __init__(self, title, formats=[], url=None):
        #
        Gtk.Dialog.__init__(self,
                            'YouTube Indicator | '+_('Preferences'),
                            None,
                            Gtk.DialogFlags.MODAL |
                            Gtk.DialogFlags.DESTROY_WITH_PARENT,
                            (Gtk.STOCK_CANCEL,
                             Gtk.ResponseType.REJECT,
                             Gtk.STOCK_OK,
                             Gtk.ResponseType.ACCEPT))
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_size_request(300, 400)
        self.connect('close', self.close_application)
        self.set_icon_from_file(comun.ICON)
        #
        vbox0 = Gtk.VBox(spacing=5)
        vbox0.set_border_width(5)
        self.get_content_area().add(vbox0)
        frame2 = Gtk.Frame()
        vbox0.pack_start(frame2, False, False, 0)
        hbox2 = Gtk.HBox(spacing=5)
        hbox2.set_border_width(5)
        frame2.add(hbox2)
        hbox2.pack_start(Gtk.Label(title), False, False, 0)
        if url is not None:
            thumbnail = Gtk.Image()
            response = urllib.request.urlopen(url)
            loader = GdkPixbuf.PixbufLoader()
            loader.write(response.read())
            loader.close()
            original_pixbuf = loader.get_pixbuf()
            width = original_pixbuf.get_width()
            height = original_pixbuf.get_height()
            if width > height:
                new_width = 200
                new_height = 200 * height / width
            else:
                new_height = 200
                new_width = 200 * width / height
            resized_pixbuf = original_pixbuf.scale_simple(
                new_width, new_height, GdkPixbuf.InterpType.BILINEAR)
            thumbnail.set_from_pixbuf(resized_pixbuf)
            frame3 = Gtk.Frame()
            vbox0.pack_start(frame3, False, False, 0)
            hbox3 = Gtk.HBox(spacing=5)
            hbox3.set_border_width(5)
            frame3.add(hbox3)
            hbox3.pack_start(thumbnail, False, False, 0)
        frame1 = Gtk.Frame()
        vbox0.pack_start(frame1, False, False, 0)
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_size_request(300, 200)
        frame1.add(scrolled_window)
        self.checkboxs = {}
        table = Gtk.Table(1, len(formats), False)
        scrolled_window.add(table)
        labels = {}
        label_t = []
        for aformat in formats:
            print(aformat)
            label = aformat['ext']
            if 'width' in aformat.keys() and\
                    aformat['width'] is not None and\
                    'height' in aformat.keys() and\
                    aformat['height'] is not None:
                label += ' (%sx%s)' % (aformat['width'], aformat['height'])
            elif 'width' in aformat.keys() and\
                    aformat['width'] is not None:
                label += ' (%s)' % (aformat['width'])
            elif 'height' in aformat.keys() and\
                    aformat['height'] is not None:
                label += ' (%s)' % (aformat['height'])
            if 'format_note' in aformat.keys() and\
                    aformat['format_note'] is not None:
                label += ' - %s' % (aformat['format_note'])
            if label not in label_t:
                label_t.append(label)
                labels[aformat['format_id']] = label
        sorted_labels = sorted(labels.items(), key=lambda x: x[1])
        for i, key_value in enumerate(sorted_labels):
            self.checkboxs[key_value[0]] = Gtk.CheckButton(key_value[1])
            table.attach(self.checkboxs[key_value[0]], 0, 1, i, i+1)
        self.show_all()

    def close_application(self, event):
        self.hide()

    def get_selected(self):
        selected = []
        for key in self.checkboxs.keys():
            if self.checkboxs[key].get_active():
                selected.append(key)
        return selected


if __name__ == "__main__":
    cm = SaveDialog('filename', ['5', '6', '167'])
    if cm.run() == Gtk.ResponseType.ACCEPT:
            print(cm.get_selected())
    cm.hide()
    cm.destroy()
    exit(0)
