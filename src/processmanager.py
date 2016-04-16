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


from gi.repository import GObject
from queue import Queue
import threading

NUM_THREADS = 4


class Manager(GObject.GObject):
    __gsignals__ = {
        'start_process': (
            GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (object,)),
        'element_processed': (
            GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (object,)),
        'error_processing_element': (
            GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (object,)),
        'end_process': (
            GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (object,)),
        }

    def __init__(self, elements, processor):
        GObject.GObject.__init__(self)
        self.elements = elements
        self.processor = processor

    def process(self):
        total = len(self.elements)
        if total > 0:
            print(self.elements)
            workers = []
            self.emit('start_process', None)
            print('1.- Starting process creating workers')
            cua = Queue(maxsize=total+1)
            total_workers = total if NUM_THREADS > total else NUM_THREADS
            for i in range(total_workers):
                worker = Worker(i, cua, self.processor)
                worker.connect('processed', self.on_element_processed)
                worker.connect('error', self.on_error_processing_element)
                worker.start()
                workers.append(worker)
            print('2.- Puting task in the queue')
            for element in self.elements:
                cua.put(element)
            print('3.- Block until all tasks are done')
            cua.join()
            print('4.- Stopping workers')
            for i in range(total_workers):
                cua.put(None)
            for worker in workers:
                worker.join()
            print('5.- The End')
            self.emit('end_process', None)

    def on_error_processing_element(self, data1, data2):
        self.emit('error_processing_element', None)

    def on_element_processed(self, data1, data2):
        self.emit('element_processed', None)


class Worker(GObject.GObject, threading.Thread):
    __gsignals__ = {
        'processed': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (object,)),
        'error': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (object,)),
        }

    def __init__(self, worker_id, cua, process):
        threading.Thread.__init__(self)
        GObject.GObject.__init__(self)
        self.setDaemon(True)
        self.id = worker_id
        self.cua = cua
        self.process = process

    def run(self):
        working = True
        while working:
            element = self.cua.get()
            print('*--', self.id, '--*')
            if element is None:
                working = False
                break
            try:
                self.process(element)
                self.emit('processed', element)
            except Exception as e:
                print(e)
                self.emit('error', None)
            self.cua.task_done()
