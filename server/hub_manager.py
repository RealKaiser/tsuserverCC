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

import os
import logging
import yaml
from server.exceptions import ClientError, AreaError, ArgumentError

class HubManager:
	"""
	Handles storing and loading areas for hubs.
	"""
	def __init__(self, server):
		self.server = server

	def loadhub(self, client, arg):
		index = 0
		hubname = f'storage/hub/{arg}.yaml'
		hubmusiclist = ''
		new = not os.path.exists(hubname)
		if new:
			client.send_ooc('No hub with that name found.')
			return
		else:
			with open(hubname, 'r') as chars:
				areas = yaml.safe_load(chars)
			self.clearhub(client)
			if len(areas) > 100:
				client.send_ooc('Cannot have more than 100 areas in a hub!')
				return
			for item in areas:
				if 'hub' in item:
					client.area.background = item['background']
					client.area.doc = item['doc']
					client.area.desc = item['desc']
					if item['musiclist'] != '':
						self.server.musiclist_manager.loadlist(client, item['musiclist'])
						hubmusiclist = item['musiclist']
				else:
					newsub = self.server.area_manager.Area(client.area.cur_subid, self.server, item['area'],
							  item['background'], bg_lock=False, evidence_mod='CM', locking_allowed=True, iniswap_allowed=True, 
							  showname_changes_allowed=True, shouts_allowed=True, jukebox=False, abbreviation='', non_int_pres_only=False)
					client.area.subareas.append(newsub)
					for owner in client.area.owners:
						newsub.owners.append(owner)
					newsub.sub = True
					newsub.hub = client.area
					if 'doc' in item:
						newsub.doc = item['doc']
					if 'desc' in item:
						newsub.desc = item['desc']
					if item['musiclist'] != '':
						self.server.musiclist_manager.loadsublist(newsub, item['musiclist'])
					elif hubmusiclist != '':
						self.server.musiclist_manager.loadsublist(newsub, hubmusiclist)
					newsub.abbreviation = f'H{client.area.hubid}S{newsub.id}'
					client.area.cur_subid += 1
					if 'reachable_areas' in item:
						if item['reachable_areas'] != '':
							r_areas = item['reachable_areas'].split(', ')
							newsub.connections = r_areas
							newsub.is_restricted = True
			lobby = client.server.area_manager.default_area()
			for area in client.area.subareas:
				tempcon = []
				for area2 in client.area.subareas:
					for conn in area.connections:
						if area2.name == conn:
							tempcon.append(area2)
				area.connections = tempcon
				if client.area not in area.connections:
					area.connections.append(client.area)
				if lobby not in area.connections:
					area.connections.append(lobby)
			area_list = []
			lobby = self.server.area_manager.default_area()
			area_list.append(lobby.name)
			area_list.append(client.area.name)
			for a in client.area.subareas:
				area_list.append(a.name)
			client.server.send_all_cmd_pred('FA', *area_list, pred=lambda x: x.area == client.area or x.area in client.area.subareas)
			client.area.sub_arup_players()
			client.area.sub_arup_cms()
			client.area.sub_arup_status()
			client.area.sub_arup_lock()
			
			client.send_ooc(f'Hub {arg} loaded!')
		
	def savehub(self, client, arg):
		hubname = f'storage/hub/{arg}.yaml'
		hubpath = 'storage/hub'
		new = not os.path.exists(hubname)
		newhub = not os.path.exists(hubpath)

		if newhub:
			os.mkdir(hubpath)
		
		if not new:
			os.remove(hubname)

		
		hub = []
		hub.append({'area': client.area.name, 'background': client.area.background, 'doc': client.area.doc, 'musiclist': client.area.cmusic_listname, 'reachable_areas': client.area.connections, 'hub': 'true', 'desc': client.area.desc})
		for area in client.area.subareas:
			connections = ''
			if len(area.connections) > 0:
				for connection in area.connections:
					connections += f'{connection.name}, '
				connections = connections[:-2]
			hub.append({'area': area.name, 'background': area.background, 'doc': area.doc, 'musiclist': area.cmusic_listname, 'reachable_areas': connections, 'desc': client.area.desc})
		with open(hubname, 'w', encoding='utf-8') as hubfile:
			yaml.dump(hub, hubfile)
		client.send_ooc(f'Hub {arg} saved!')
	
	def removesub(self, client, area=None):
		if area != None:
			destroyed = area
		else:
			destroyed = client.area
		hub = destroyed.hub
		destroyedclients = set()
		for c in destroyed.clients:
			if c in destroyed.owners:
				destroyed.owners.remove(c)
			destroyedclients.add(c)
		for c in destroyedclients:
			if c in destroyed.clients:
				c.change_area(hub)
				c.send_ooc(f'You were moved to {hub.name} from {destroyed.name} because it was destroyed.')
		if destroyed not in hub.subareas and destroyed.hub.hubtype == 'user':
			return
		hub.subareas.remove(destroyed)
		old_sublist = []
		for sub in hub.subareas:
			old_sublist.append(sub)
		hub.subareas.clear()
		hub.cur_subid = 1
		for sub in old_sublist:
			oldid = sub.id
			sub.id = hub.cur_subid
			if sub.name == f'Area {oldid}':
				sub.name = f'Area {sub.id}'
			if hub.hubtype == 'arcade':
				sub.abbreviation = f'AHS{sub.id}'
			elif hub.hubtype == 'user':
				sub.abbreviation = f'UHS{sub.id}'
			elif hub.hubtype == 'courtroom':
				if sub.name == f'Courtroom {oldid}':
					sub.name = f'Courtroom {sub.id}'
				sub.abbreviation = f'CR{sub.id}'
			else:
				sub.abbreviation = f'H{hub.hubid}S{sub.id}'
			hub.subareas.append(sub)
			hub.cur_subid += 1
		area_list = []
		lobby = self.server.area_manager.default_area()
		area_list.append(lobby.name)
		area_list.append(hub.name)
		for sub in hub.subareas:
			area_list.append(sub.name)
		client.server.send_all_cmd_pred('FA', *area_list, pred=lambda x: x.area == hub or x.area in hub.subareas)
		hub.sub_arup_players()
		hub.sub_arup_cms()
		hub.sub_arup_status()
		hub.sub_arup_lock()
	
	def clearhub(self, client):
		hub = client.area
		destroyedclients = set()
		for sub in hub.subareas:
			for c in sub.clients:
				if c in sub.owners:
					sub.owners.remove(c)
				destroyedclients.add(c)
			for dc in destroyedclients:
				if dc in sub.clients:
					dc.change_area(hub)
					dc.send_ooc(f'You were moved to {hub.name} because the hub was cleared.')
		hub.subareas.clear()
		hub.cur_subid = 1
		hub.desc = ''
		if hub.hubtype == 'default':
			hub.name = f'Hub {hub.hubid}'
		hub.change_status('idle')
		area_list = []
		lobby = client.server.area_manager.default_area()
		area_list.append(lobby.name)
		area_list.append(hub.name)
		client.server.send_all_cmd_pred('FA', *area_list, pred=lambda x: x.area == hub or x.area in hub.subareas)
		area_list = []
		for area in client.server.area_manager.areas:
			area_list.append(area.name)
		client.server.send_all_cmd_pred('FA', *area_list, pred=lambda x: not x.area.is_hub and not x.area.sub)
		client.server.area_manager.send_arup_cms()
		client.server.area_manager.send_arup_players()
		client.server.area_manager.send_arup_lock()
		client.server.area_manager.send_arup_status()
		hub.sub_arup_players()
		hub.sub_arup_cms()
		hub.sub_arup_status()
		hub.sub_arup_lock()

	def addmoresubs(self, client, arg):
		if arg + client.area.cur_subid > 101:
			client.send_ooc('Cannot have more than 100 areas in a hub!')
			return
		index = 0
		while index < arg:
			self.addsub(client, '', True)
			index += 1
		
		area_list = []
		lobby = client.server.area_manager.default_area()
		area_list.append(lobby.name)
		area_list.append(client.area.name)
		for a in client.area.subareas:
			area_list.append(a.name)
		client.server.send_all_cmd_pred('FA', *area_list, pred=lambda x: x.area == client.area or x.area in client.area.subareas)
		
		client.area.sub_arup_players()
		client.area.sub_arup_cms()
		client.area.sub_arup_status()
		client.area.sub_arup_lock()
		client.send_ooc('Areas created!')
		
		
	def addsub(self, client, arg, more=False):
		index = 0
		if client.area.is_hub:
			if client.area.cur_subid > 101:
				raise ClientError('You cannot have more than 100 areas in a hub.')
			elif client.area.hubtype == 'arcade' or client.area.hubtype == 'user' or client.area.hubtype == 'courtroom':
				if client.area.cur_subid > 16:
					raise ClientError('Cannot have more than 15 areas in this hub.')
			new_id = client.area.cur_subid
			client.area.cur_subid += 1
		else:
			if client.area.hub.cur_subid > 101:
				raise ClientError('You cannot have more than 100 areas in a hub.')
			elif client.area.hub.hubtype == 'arcade' or client.area.hub.hubtype == 'user' or client.area.hubtype == 'courtroom':
				if client.area.hub.cur_subid > 16:
					raise ClientError('Cannot have more than 15 areas in this hub.')
			new_id = client.area.hub.cur_subid
			client.area.hub.cur_subid += 1
		if len(arg) == 0:
			newsub = client.server.area_manager.Area(new_id, client.server, name=f'Area {new_id}', background='', bg_lock=False, evidence_mod='CM', locking_allowed=True, iniswap_allowed=True, showname_changes_allowed=True, shouts_allowed=True, jukebox=False, abbreviation='', non_int_pres_only=False)
		else:
			newsub = client.server.area_manager.Area(new_id, client.server, name=arg, background='', bg_lock=False, evidence_mod='CM', locking_allowed=True, iniswap_allowed=True, showname_changes_allowed=True, shouts_allowed=True, jukebox=False, abbreviation='', non_int_pres_only=False)
		newsub.sub = True
		if client.area.is_hub:
			newsub.hub = client.area
			client.area.subareas.append(newsub)
		else:
			newsub.hub = client.area.hub
			client.area.hub.subareas.append(newsub)
		newsub.background = newsub.hub.background
		newsub.cmusic_list = newsub.hub.cmusic_list.copy()
		newsub.cmusic_listname = newsub.hub.cmusic_listname
		if newsub.hub.hubtype == 'arcade':
			newsub.abbreviation = f'AHS{new_id}'
		elif newsub.hub.hubtype == 'user':
			newsub.abbreviation = f'UHS{new_id}'
		elif newsub.hub.hubtype == 'courtroom':
			newsub.abbreviation = f'CR{new_id}'
			if len(arg) == 0:
				newsub.name = f'Courtroom {new_id}'
			newsub.evidence_mod = 'HiddenCM'
		else:
			newsub.abbreviation = f'H{newsub.hub.hubid}S{new_id}'
		
		#client.server.send_all_cmd_pred('CT', '{}'.format(client.server.config['hostname']),f'=== Announcement ===\r\nA new area has been created.\n[{new_id}] {arg}\r\n==================', '1')
		if client.area.is_hub:
			if newsub.hub.hubtype != 'default':
				newsub.owners.append(client)
			else:
				for owner in client.area.owners:
					newsub.owners.append(owner)
		else:
			for owner in client.area.hub.owners:
				newsub.owners.append(owner)
		newsub.status = client.area.status
		if not more:
			area_list = []
			lobby = client.server.area_manager.default_area()
			area_list.append(lobby.name)
			if client.area.is_hub:
				area_list.append(client.area.name)
				for a in client.area.subareas:
					area_list.append(a.name)
			else:
				area_list.append(client.area.hub.name)
				for a in client.area.hub.subareas:
					area_list.append(a.name)
			client.server.send_all_cmd_pred('FA', *area_list, pred=lambda x: x.area == newsub.hub or x.area in newsub.hub.subareas)
			
			newsub.hub.sub_arup_players()
			newsub.hub.sub_arup_cms()
			newsub.hub.sub_arup_status()
			newsub.hub.sub_arup_lock()
	
			client.send_ooc('Area created!')