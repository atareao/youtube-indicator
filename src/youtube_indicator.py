#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# pushbullet-indicator.py
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
from gi.repository import GLib
from gi.repository import GdkPixbuf
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify
from gi.repository import GObject
import os
import time
import shlex
import webbrowser
import subprocess
import sys
import dbus
import urllib
import requests

import pprint

from dbus.mainloop.glib import DBusGMainLoop
import concurrent.futures

from configurator import Configuration
from save_preferences import SaveDialog
from preferences_dialog import PreferencesDialog
from comun import _
import comun
from processmanager import Manager
from status import TimeUpdater

sys.path.insert(1, '/usr/lib/python2.7/dist-packages/')
import youtube_dl


NUM_THREADS = 4


def download(element):
    if element is not None:
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
            return dest_file
        except Exception as e:
            print('Error downloading...', e)
        return None


def add2menu(menu, text=None, icon=None,
             conector_event=None, conector_action=None):
    if text is not None:
        menu_item = Gtk.ImageMenuItem.new_with_label(text)
        if icon:
            image = Gtk.Image.new_from_file(icon)
            menu_item.set_image(image)
            menu_item.set_always_show_image(True)
    else:
        if icon is None:
            menu_item = Gtk.SeparatorMenuItem()
        else:
            menu_item = Gtk.ImageMenuItem.new_from_file(icon)
            menu_item.set_always_show_image(True)
    if conector_event is not None and conector_action is not None:
        menu_item.connect(conector_event, conector_action)
    menu_item.show()
    menu.append(menu_item)
    return menu_item


def wait(time_lapse):
    time_start = time.time()
    time_end = (time_start + time_lapse)
    while time_end > time.time():
        while Gtk.events_pending():
            Gtk.main_iteration()
        time.sleep(0.3)


class YouTube_Indicator(GObject.GObject):
    __gsignals__ = {
        'downloading_start': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ()),
        'downloading_end': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ()),
    }

    def __init__(self):
        GObject.GObject.__init__(self)
        self.about_dialog = None
        self.downloading = False
        self.monitor_clipboard = True
        self.frame = 0
        self.last_capture_url = None
        self.last_capture_time = 0
        self.notification = Notify.Notification.new('', '', None)
        #
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.connect('owner-change', self.capture_clipboard)
        #
        self.indicator = appindicator.Indicator.new(
            'YouTube-Indicator',
            comun.ICON,
            appindicator.IndicatorCategory.HARDWARE)
        menu = self.get_menu()
        self.read_preferences()
        #
        self.indicator.set_icon(comun.STATUS_ICON[self.theme])
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.indicator.connect('scroll-event', self.on_scroll)
        #
        self.indicator.set_menu(menu)

    def capture_clipboard(self, data1, data2):
        if self.monitor_clipboard and not self.downloading:
            clipboard = data1
            text = clipboard.wait_for_text()
            if text is not None and (
                    text.startswith('http://') or
                    text.startswith('https://')):
                try:
                    ydl = youtube_dl.YoutubeDL({'outtmpl': '%(id)s%(ext)s'})
                    ydl.add_default_info_extractors()
                    ydl.extract_info(text, download=False)
                    url = text
                    newtime = int(time.time()*100)
                    if self.last_capture_url != url\
                            or self.last_capture_time != newtime:
                        self.last_capture_url = url
                        self.last_capture_time = newtime
                        self.captured_youtube_url(url)
                except Exception as e:
                    print('Capture clipboard error', e)
                    msg = _('Error processing url')
                    self.notification.update('YouTube-Indicator',
                                             msg,
                                             os.path.join(comun.ICON))
                    self.notification.show()

    def on_scroll(self, widget, steps, direcction):
        self.change_status()

    def change_status(self, widget=None):
        self.monitor_clipboard = not self.monitor_clipboard
        if self.monitor_clipboard:
            self.menu_capture.set_label(_('Not capture'))
            self.indicator.set_icon(comun.STATUS_ICON[self.theme])
        else:
            self.menu_capture.set_label(_('Capture'))
            self.indicator.set_icon(comun.DISABLED_ICON[self.theme])

    def captured_youtube_url(self, url):
        while Gtk.events_pending():
            Gtk.main_iteration()
        try:
            ydl = youtube_dl.YoutubeDL({'outtmpl': '%(id)s%(ext)s'})
            # Add all the available extractors
            ydl.add_default_info_extractors()
            result = ydl.extract_info(url, download=False)
        except Exception as e:
            msg = _('Error processing url')
            print('******', str(e), '*********')
            self.notification.update('YouTube-Indicator',
                                     msg,
                                     os.path.join(comun.ICON))
            self.notification.show()
            return
        urls = {}
        print('***********************+')
        pprint.pprint(result)
        print('***********************+')
        if 'thumbnail' not in result.keys():
            result['thumbnail'] = None
        if 'formats' not in result.keys():
            someformats = []
            someformats.append(result)
            result['formats'] = someformats
        cm = SaveDialog(
            result['title'], result['formats'], result['thumbnail'])
        if cm.run() == Gtk.ResponseType.ACCEPT:
            cm.hide()
            while Gtk.events_pending():
                Gtk.main_iteration()
            print('**** Start downloading ****')
            elements = []
            if 'formats' in result.keys() and\
                    result['formats'] is not None:
                for i, aformat in enumerate(result['formats']):
                    if aformat['format_id'] in cm.get_selected():
                        newelement = {}
                        newelement['format'] = aformat
                        newelement['url'] = aformat['url']
                        newelement['dir'] = self.downloaddir
                        newelement['name'] = result['title']+'_%s' % i
                        newelement['ext'] = aformat['ext']
                        elements.append(newelement)
            else:
                pass
            manager = Manager(elements, download)
            manager.connect('start_process', self.on_downloading_start)
            manager.connect('element_processed', self.on_element_processed)
            manager.connect('error_processing_element',
                            self.on_error_processing_element)
            manager.connect('end_process', self.on_downloading_end)
            manager.process()
        cm.destroy()

    def on_error_processing_element(self, data1, data2):
        self.notification.update('YouTube-Indicator',
                                 _('Error downloading file'),
                                 os.path.join(comun.ICON))
        self.notification.show()

    def on_element_processed(self, data1, data2):
        print('element_processed', type(data1), type(data2))
        self.notification.update('YouTube-Indicator',
                                 _('File downloaded'),
                                 os.path.join(comun.ICON))
        self.notification.show()

    def on_downloading_start(self, data1, data2):
        self.downloading = True
        time.sleep(0.1)
        self.indicator.set_icon(comun.DOWNLOADING_ICON[self.theme])
        self.indicator.set_attention_icon(comun.DOWNLOADING_ICON[self.theme])
        while Gtk.events_pending():
            Gtk.main_iteration()
        self.notification.update('YouTube-Indicator',
                                 _('Start downloading file'),
                                 os.path.join(comun.ICON))
        self.notification.show()

    def on_downloading_end(self, data1, data2):
        self.downloading = False
        self.notification.update('YouTube-Indicator',
                                 _('All files downloaded'),
                                 os.path.join(comun.ICON))
        self.notification.show()
        if self.monitor_clipboard:
            self.indicator.set_icon(comun.STATUS_ICON[self.theme])
        else:
            self.indicator.set_icon(comun.DISABLED_ICON[self.theme])

    # ################# main functions ####################

    def read_preferences(self):
        configuration = Configuration()
        self.first_time = configuration.get('first-time')
        self.version = configuration.get('version')
        self.theme = configuration.get('theme')
        self.monitor_clipboard = configuration.get('monitor-clipboard')
        self.downloaddir = configuration.get('download-dir')
        if self.monitor_clipboard:
            self.menu_capture.set_label(_('Not capture'))
            self.indicator.set_icon(comun.STATUS_ICON[self.theme])
        else:
            self.menu_capture.set_label(_('Capture'))
            self.indicator.set_icon(comun.DISABLED_ICON[self.theme])
    # ################## menu creation ######################

    def get_help_menu(self):
        help_menu = Gtk.Menu()
        #
        add2menu(help_menu,
                 text=_('Homepage...'),
                 conector_event='activate',
                 conector_action=lambda x:
                 webbrowser.open(
                    'http://www.atareao.es/apps/youtube-indicator-o-como-\
descargar-videos-de-youtube-a-lo-facil/'))
        add2menu(help_menu,
                 text=_('Get help online...'),
                 conector_event='activate',
                 conector_action=lambda x:
                 webbrowser.open(
                    'https://answers.launchpad.net/youtube-indicator'))
        add2menu(help_menu,
                 text=_('Translate this application...'),
                 conector_event='activate',
                 conector_action=lambda x:
                 webbrowser.open(
                    'https://github.com/atareao/youtube-indicator'))
        add2menu(help_menu,
                 text=_('Report a bug...'),
                 conector_event='activate',
                 conector_action=lambda x:
                 webbrowser.open(
                    'https://github.com/atareao/youtube-indicator/issues'))
        add2menu(help_menu)
        web = add2menu(help_menu,
                       text=_('Homepage'),
                       conector_event='activate',
                       conector_action=lambda x: webbrowser.open(
                        'http://www.atareao.es/apps/youtube-indicator-o-como-\
descargar-videos-de-youtube-a-lo-facil/'))
        twitter = add2menu(help_menu,
                           text=_('Follow us in Twitter'),
                           conector_event='activate',
                           conector_action=lambda x:
                           webbrowser.open(
                            'https://twitter.com/atareao'))
        googleplus = add2menu(
            help_menu,
            text=_('Follow us in Google+'),
            conector_event='activate',
            conector_action=lambda x:
            webbrowser.open(
                'https://plus.google.com/118214486317320563625/posts'))
        facebook = add2menu(help_menu,
                            text=_('Follow us in Facebook'),
                            conector_event='activate',
                            conector_action=lambda x:
                            webbrowser.open(
                                'http://www.facebook.com/elatareao'))
        add2menu(help_menu)
        #
        web.set_image(
            Gtk.Image.new_from_file(
                os.path.join(comun.SOCIALDIR, 'web.svg')))
        web.set_always_show_image(True)
        twitter.set_image(
            Gtk.Image.new_from_file(
                os.path.join(comun.SOCIALDIR, 'twitter.svg')))
        twitter.set_always_show_image(True)
        googleplus.set_image(
            Gtk.Image.new_from_file(
                os.path.join(comun.SOCIALDIR, 'googleplus.svg')))
        googleplus.set_always_show_image(True)
        facebook.set_image(
            Gtk.Image.new_from_file(
                os.path.join(comun.SOCIALDIR, 'facebook.svg')))
        facebook.set_always_show_image(True)

        add2menu(help_menu)
        add2menu(help_menu,
                 text=_('About'),
                 conector_event='activate',
                 conector_action=self.on_about_item)
        #
        help_menu.show()
        return(help_menu)

    def get_menu(self):
        """Create and populate the menu."""
        menu = Gtk.Menu()
        #
        self.menu_capture = Gtk.MenuItem.new_with_label(_('Capture'))
        self.menu_capture.connect('activate', self.change_status)
        self.menu_capture.show()
        menu.append(self.menu_capture)

        #
        separator1 = Gtk.SeparatorMenuItem()
        separator1.show()
        menu.append(separator1)
        #
        menu_preferences = Gtk.MenuItem.new_with_label(_('Preferences'))
        menu_preferences.connect('activate', self.on_preferences_item)
        menu_preferences.show()
        menu.append(menu_preferences)

        menu_help = Gtk.MenuItem.new_with_label(_('Help'))
        menu_help.set_submenu(self.get_help_menu())
        menu_help.show()
        menu.append(menu_help)
        #
        separator2 = Gtk.SeparatorMenuItem()
        separator2.show()
        menu.append(separator2)
        #
        menu_exit = Gtk.MenuItem.new_with_label(_('Exit'))
        menu_exit.connect('activate', self.on_quit_item)
        menu_exit.show()
        menu.append(menu_exit)
        #
        menu.show()
        return(menu)

    def get_about_dialog(self):
        """Create and populate the about dialog."""
        about_dialog = Gtk.AboutDialog()
        about_dialog.set_name(comun.APPNAME)
        about_dialog.set_version(comun.VERSION)
        about_dialog.set_copyright(
            'Copyrignt (c) 2014-2016\nLorenzo Carbonell Cerezo')
        about_dialog.set_comments(_('An indicator for capture YouTube'))
        about_dialog.set_license('''
This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.
''')
        about_dialog.set_website('http://www.atareao.es')
        about_dialog.set_website_label('http://www.atareao.es')
        about_dialog.set_authors([
            'Lorenzo Carbonell <https://launchpad.net/~lorenzo-carbonell>'])
        about_dialog.set_documenters([
            'Lorenzo Carbonell <https://launchpad.net/~lorenzo-carbonell>'])
        about_dialog.set_translator_credits('''
Lorenzo Carbonell <https://launchpad.net/~lorenzo-carbonell>\n
''')
        about_dialog.set_icon(GdkPixbuf.Pixbuf.new_from_file(comun.ICON))
        about_dialog.set_logo(GdkPixbuf.Pixbuf.new_from_file(comun.ICON))
        about_dialog.set_program_name(comun.APPNAME)
        return about_dialog

    def on_preferences_item(self, widget, data=None):
        widget.set_sensitive(False)
        preferences_dialog = PreferencesDialog()
        if preferences_dialog.run() == Gtk.ResponseType.ACCEPT:
            preferences_dialog.hide()
            preferences_dialog.close_ok()
            self.read_preferences()
        preferences_dialog.destroy()
        widget.set_sensitive(True)

    def on_quit_item(self, widget, data=None):
        exit(0)

    def on_about_item(self, widget, data=None):
        if self.about_dialog:
            self.about_dialog.present()
        else:
            self.about_dialog = self.get_about_dialog()
            self.about_dialog.run()
            self.about_dialog.destroy()
            self.about_dialog = None

#################################################################


def main():
    dbus_loop = DBusGMainLoop(set_as_default=True)
    if dbus.SessionBus(mainloop=dbus_loop).request_name(
        'es.atareao.YouTubeIndicator') !=\
            dbus.bus.REQUEST_NAME_REPLY_PRIMARY_OWNER:
        print("application already running")
        exit(0)
    Notify.init('youtube-indicator')
    GLib.threads_init()
    youtube_indicator = YouTube_Indicator()
    Gtk.main()
    exit(0)

if __name__ == "__main__":
    main()
