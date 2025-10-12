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

import random
import re
import asyncio
from enum import Enum

from server import database
from server.constants import TargetType
from server.exceptions import ClientError, ServerError, ArgumentError

class Party:
	def __init__(self, server, name, leader, party_id, locked=True):
		self.server = server
		self.name = name
		self.leader = leader
		self.users = set()
		self.id = party_id
		self.invite_list = {}
		self.lock = locked
		self.users.add(leader)
		self.notepad = ''
		self.votes = set()
		self.voters = []
		self.playerid = []
		self.rolesvisible = False
		
	def add_user(self, client):
		self.users.add(client)

	def mg_roles(self, roles):
		players = len(self.users)
		players = players - 1
		userrange = range(players)
		index = 0
		self.playerid = []
		for user in self.users:
			if user != self.leader:
				self.playerid.append(index)
				self.playerid[index] = user
				index += 1
		keymaster = self.playerid[random.choice(userrange)]
		keymaster.partyrole = 'Keymaster'
		keymaster.votepower = 0
		loop = True
		while loop:
			sage = self.playerid[random.choice(userrange)]
			if sage.partyrole == '':
				sage.partyrole = 'Sage'
				sage.votepower = 0
				break
		while loop:
			sac = self.playerid[random.choice(userrange)]
			if sac.partyrole == '':
				sac.partyrole = 'Sacrifice'
				sac.votepower = 1
				break
		index = 0
		customroles = len(roles)
		freeplayers = players - 3
		if customroles >= freeplayers:
			raise ArgumentError('Not enough players to hand out roles!')
		while index < customroles:
			if customroles == 0:
				break
			role = self.playerid[random.choice(userrange)]
			if role.partyrole == '':
				role.partyrole = roles[index]
				role.votepower = 0
				index += 1
		for user in self.users:
			if user != self.leader and user.partyrole == '':
				user.partyrole = 'Commoner'
				user.votepower = 0
		self.playerid = []
		msg = 'All roles handed out!'
		return msg

class Vote:
    def __init__(self, name):
        self.name = name
        self.number = 0
        self.voters = set()