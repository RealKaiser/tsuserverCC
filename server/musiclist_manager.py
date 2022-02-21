"""
tsuserverOLE, an Attorney Online server.
Copyright (C) 2021 KillerSteel <killermagnum5@gmail.com

Derivative of tsuserverCC, an Attorney Online server.
Copyright (C) 2020 Kaiser <kaiserkaisie@gmail.com>

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

import os
import logging
import yaml

class MusicListManager:
	"""
	Handles storing and loading custom music lists for areas.
	"""
	def __init__(self, server):
		self.server = server

	def loadlist(self, client, arg):
		listname = f'storage/musiclist/{arg}.yaml'
		new = not os.path.exists(listname)
		if new:
			client.send_ooc('No music list with that name found.')
			return
		else:
			client.area.cmusic_list = []
			with open(listname, 'r', encoding='utf-8') as chars:
				list = yaml.safe_load(chars)
			client.area.broadcast_ooc(f'Music list {arg} loaded!')
			client.area.cmusic_listname = arg
			client.area.cmusic_list = list
			music = client.area.get_music(client)
			if client.area.is_hub:
				client.server.send_all_cmd_pred('FM', *music, pred=lambda x: x.area == client.area or x.area.hub == client.area)
				for sub in client.area.subareas:
					sub.cmusic_listname = arg
					sub.cmusic_list = list
			else:
				client.server.send_all_cmd_pred('FM', *music, pred=lambda x: x.area == client.area)

		
	def loadsublist(self, area, arg):
		listname = f'storage/musiclist/{arg}.yaml'
		new = not os.path.exists(listname)
		if new:
			return
		else:
			area.cmusic_list = []
			with open(listname, 'r', encoding='utf-8') as chars:
				list = yaml.safe_load(chars)
			area.cmusic_listname = arg
			area.cmusic_list = list

	def storelist(self, client, arg):
		listname = f'storage/musiclist/{arg}.yaml'
		path = 'storage/musiclist'
		new = not os.path.exists(listname)
		newpath = not os.path.exists(path)

		if newpath:
			os.mkdir(path)

		if not new:
			os.remove(listname)

		with open(listname, 'w', encoding='utf-8') as list:
			yaml.dump(client.area.cmusic_list, list)
		client.send_ooc(f'Music list {arg} stored!')
		client.area.cmusic_listname = arg
		if client.area.is_hub:
			for sub in client.area.subareas:
				sub.cmusic_listname = arg