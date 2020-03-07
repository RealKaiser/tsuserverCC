# tsuserverCC, an Attorney Online server.
#
# Copyright (C) 2020 Kaiser <kaiserkaisie@gmail.com>
#
# Derivative of tsuserver3, an Attorney Online server. Copyright (C) 2016 argoneus <argoneuscze@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import logging
import yaml
logger = logging.getLogger('debug')
event_logger = logging.getLogger('events')

class MusicListManager:
    """
    A music list stored on the server that can be loaded into an area.
    """
    def __init__(self):
        self.exist = True

    def loadlist(self, client, arg):
        listname = f'storage/{arg}.yaml'
        new = not os.path.exists(listname)
        if new:
            client.send_ooc('No music list with that name found.')
            return
        else:
            client.area.cmusic_list = dict()
            with open(listname, 'r', encoding='utf-8') as file:
                list = yaml.full_load(file)
                for name, length in list.items():
                    client.area.cmusic_list[name] = length
            client.area.broadcast_ooc(f'Music list {arg} loaded!')

    def storelist(self, client, arg):
        listname = f'storage/{arg}.yaml'
        new = not os.path.exists(listname)
        if not new:
            os.remove(listname)
        with open(listname, 'w', encoding='utf-8') as list:
            yaml.dump(client.area.cmusic_list, list)
        client.send_ooc(f'Music list {arg} stored!')