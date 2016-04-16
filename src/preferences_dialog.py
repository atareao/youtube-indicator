#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# preferences_dialog.py
#
# This file is part of PushBullet-Indicator
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
import comun
import os
import shutil
import webbrowser
from comun import _
from configurator import Configuration


def create_or_remove_autostart(create):
    if not os.path.exists(comun.AUTOSTART_DIR):
        os.makedirs(comun.AUTOSTART_DIR)
    if create is True:
        if not os.path.exists(comun.FILE_AUTO_START):
            shutil.copyfile(comun.FILE_AUTO_START_ORIG, comun.FILE_AUTO_START)
    else:
        if os.path.exists(comun.FILE_AUTO_START):
            os.remove(comun.FILE_AUTO_START)


class PreferencesDialog(Gtk.Dialog):
    def __init__(self):
        #
        Gtk.Dialog.__init__(self, 'YouTube Indicator | '+_('Preferences'),
                                  None,
                                  Gtk.DialogFlags.MODAL |
                                  Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                  (Gtk.STOCK_CANCEL,
                                   Gtk.ResponseType.REJECT,
                                   Gtk.STOCK_OK,
                                   Gtk.ResponseType.ACCEPT))
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        # self.set_size_request(400, 230)
        self.connect('close', self.close_application)
        self.set_icon_from_file(comun.ICON)
        #
        vbox0 = Gtk.VBox(spacing=5)
        vbox0.set_border_width(5)
        self.get_content_area().add(vbox0)
        frame1 = Gtk.Frame()
        vbox0.pack_start(frame1, False, True, 1)
        table1 = Gtk.Table(4, 2, False)
        frame1.add(table1)
        label1 = Gtk.Label(_('Capture clipboard'))
        label1.set_alignment(0, 0.5)
        table1.attach(label1, 0, 1, 0, 1, xpadding=5, ypadding=5)
        self.switch1 = Gtk.Switch()
        table1.attach(self.switch1, 1, 2, 0, 1, xpadding=5, ypadding=5,
                      xoptions=Gtk.AttachOptions.SHRINK)
        label2 = Gtk.Label(_('Autostart'))
        label2.set_alignment(0, 0.5)
        table1.attach(label2, 0, 1, 1, 2, xpadding=5, ypadding=5)
        self.switch2 = Gtk.Switch()
        table1.attach(self.switch2, 1, 2, 1, 2, xpadding=5, ypadding=5,
                      xoptions=Gtk.AttachOptions.SHRINK)
        label3 = Gtk.Label(_('Icon light'))
        label3.set_alignment(0, 0.5)
        table1.attach(label3, 0, 1, 2, 3, xpadding=5, ypadding=5)
        self.switch3 = Gtk.Switch()
        table1.attach(self.switch3, 1, 2, 2, 3, xpadding=5, ypadding=5,
                      xoptions=Gtk.AttachOptions.SHRINK)
        self.downloaddir = Gtk.Entry()
        self.downloaddir.set_sensitive(False)
        table1.attach(self.downloaddir, 0, 1, 3, 4, xpadding=5, ypadding=5,
                      xoptions=Gtk.AttachOptions.SHRINK)
        dirbutton = Gtk.Button(_('Select folder'))
        dirbutton.connect('clicked', self.on_dirbutton_clicked)
        table1.attach(dirbutton, 1, 2, 3, 4, xpadding=5, ypadding=5,
                      xoptions=Gtk.AttachOptions.SHRINK)
        #
        self.load_preferences()
        #
        self.show_all()

    def on_dirbutton_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(_('Please choose a folfer'), self,
                                       Gtk.FileChooserAction.SELECT_FOLDER,
                                       (Gtk.STOCK_CANCEL,
                                        Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN,
                                        Gtk.ResponseType.OK))
        dialog.set_default_size(800, 400)
        if dialog.run() == Gtk.ResponseType.OK:
            dialog.hide()
            self.downloaddir.set_text(dialog.get_filename())
        dialog.destroy()

    def close_application(self, event):
        self.hide()

    def messagedialog(self, title, message):
        dialog = Gtk.MessageDialog(None,
                                   Gtk.DialogFlags.MODAL,
                                   Gtk.MessageType.INFO,
                                   buttons=Gtk.ButtonsType.OK)
        dialog.set_markup("<b>%s</b>" % title)
        dialog.format_secondary_markup(message)
        dialog.run()
        dialog.destroy()

    def close_ok(self):
        self.save_preferences()

    def load_preferences(self):
        configuration = Configuration()
        self.switch1.set_active(configuration.get('monitor-clipboard'))
        self.switch2.set_active(os.path.exists(comun.FILE_AUTO_START))
        self.switch3.set_active(configuration.get('theme') == 'light')
        self.downloaddir.set_text(configuration.get('download-dir'))

    def save_preferences(self):
        configuration = Configuration()
        configuration.set('monitor-clipboard', self.switch1.get_active())
        create_or_remove_autostart(self.switch2.get_active())
        if self.switch3.get_active() == True:
            configuration.set('theme', 'light')
        else:
            configuration.set('theme', 'dark')
        configuration.set('download-dir', self.downloaddir.get_text())
        configuration.save()


if __name__ == "__main__":
    cm = PreferencesDialog()
    if cm.run() == Gtk.ResponseType.ACCEPT:
        print(1)
        cm.close_ok()
    cm.hide()
    cm.destroy()
    exit(0)
