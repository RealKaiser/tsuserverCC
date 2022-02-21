"""
tsuserverCC, an Attorney Online server.
Copyright (C) 2022 Kaiser <kaiserkaisie@gmail.com>

Derivative of tsuserverOLE, an Attorney Online server.
Copyright (C) 2021 KillerSteel <killermagnum5@gmail.com

Derivative of tsuserverCC, an Attorney Online server.
Copyright (C) 2020 Kaiser <kaiserkaisie@gmail.com>

Derivative of tsuserver3, an Attorney Online server. 
Copyright (C) 2016 argoneus <argoneuscze@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.
 
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.
 
You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import time
import asyncio

class Timer:

    def __init__(self):
        self._start_time = None
        self.elapsed_time = None
        self.started = False
        self.alarmtime = None
        self.alarmtimeset = None
        self.alarmtype = None

    def start(self):
        self._start_time = time.perf_counter()
        self.started = True

    def nostop(self):
        if self.started == False:
            self._start_time = time.perf_counter()
        elif self.elapsed_time == None:
            self.elapsed_time = time.perf_counter() - self._start_time
        else:
            self._start_time = time.perf_counter() - self.elapsed_time
				
    def stop(self):
        self.elapsed_time = time.perf_counter() - self._start_time
        self._start_time = None
        return self.elapsed_time

    def check(self):
        if self._start_time == None:
            return self.elapsed_time
        else:
            self.elapsed_time = time.perf_counter() - self._start_time
            return self.elapsed_time

    def setalarm(self, ttime, type, client):
        self.alarmtime = ttime
        self.alarmtimeset = time.perf_counter()
        self.alarmtimeset += ttime
        self.alarmtype = type
        if type == 'hours':
            ttime = ttime / 60
            ttime = ttime / 60
        if type == 'minutes':
            ttime = ttime / 60
        asyncio.get_event_loop().call_later(self.alarmtime, lambda: self.resetalarm(client, ttime, type))

    def resetalarm(self, client, ttime, type):
        self.alarmtime = None
        client.send_ooc(f'Alarm, {ttime:0.0f} {type} have passed!')