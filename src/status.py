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

import threading
import time


class TimeUpdater(threading.Thread):

    def __init__(self, process):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.is_updating = False
        self.process = process

    def run(self):
        self.is_updating = True
        while self.is_updating:
            self.process()
            time.sleep(1.0)

    def stop(self):
        self.is_updating = False
