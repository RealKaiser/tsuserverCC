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

class FriendManager:
    """
    Handles storing and loading friend lists for clients and other friend mechanics.
    """
    class FriendList:
        """
        Instance of a client's friend list.
        """
        def __init__(self, client):
            self.client = client
            self.friends = None
            self.loadfriends()

        def loadfriends(self):
            self.friends = dict()
            listname = f'storage/friendlist/{self.client.hdid}.yaml'
            new = not os.path.exists(listname)
            if not new:
                with open(listname, 'r', encoding='utf-8') as file:
                    list = yaml.safe_load(file)
                for hdid, name in list.items():
                    self.friends[hdid] = name

        def addfriend(self, friend_hdid, friend_name):
            listname = f'storage/friendlist/{self.client.hdid}.yaml'
            flistname = f'storage/friendlist/{friend_hdid}.yaml'
            new = not os.path.exists(listname)
            fnew = not os.path.exists(flistname)
            friend_friends = dict()
            if fnew:
                friend_friends[self.client.hdid] = self.client.name
                with open(flistname, 'w', encoding='utf-8') as list:
                    yaml.dump(friend_friends, list)
            else:
                with open(flistname, 'r', encoding='utf-8') as file:
                    list = yaml.safe_load(file)
                for hdid, name in list.items():
                    friend_friends[hdid] = name
                friend_friends[self.client.hdid] = self.client.name
                with open(flistname, 'w', encoding='utf-8') as list:
                    yaml.dump(friend_friends, list)

            self.friends[friend_hdid] = friend_name

            if not new:
                os.remove(listname)
            with open(listname, 'w', encoding='utf-8') as list:
                yaml.dump(self.friends, list)

        def removefriend(self, friend_hdid):
            try:
                listname = f'storage/friendlist/{self.client.hdid}.yaml'
                flistname = f'storage/friendlist/{friend_hdid}.yaml'
                friend_friends = dict()
                self.friends = dict()
            except:
                return self.client.send_ooc('error 1 in friend manager')
            try:
                with open(flistname, 'r', encoding='utf-8') as file:
                    list = yaml.safe_load(file)
            except:
                return self.client.send_ooc('error 1.1 in friend manager')
            try:
                for hdid, name in list.items():
                    friend_friends[hdid] = name
            except:
                return self.client.send_ooc('error 1.2 in friend manager')
            try:
                friend_friends.pop(self.client.hdid, None)
            except:
                return self.client.send_ooc('error 1.3 in friend manager')
            try:
                os.remove(flistname)
                with open(flistname, 'w', encoding='utf-8') as list:
                    yaml.dump(friend_friends, list)
            except:
                return self.client.send_ooc('error 1.4 in friend manager')
            try:
                with open(listname, 'r', encoding='utf-8') as file:
                    list = yaml.safe_load(file)
                for hdid, name in list.items():
                    self.friends[hdid] = name
                self.friends.pop(friend_hdid, None)
                with open(listname, 'w', encoding='utf-8') as list:
                    yaml.dump(self.friends, list)
            except:
                return self.client.send_ooc('error 2 in friend manager')

    def __init__(self, server):
        self.server = server
        self.friendlists = set()
    
    def new_friendlist(self, client):
        client.friendlist = self.FriendList(client)
        self.friendlists.add(client.friendlist)