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


import asyncio
import random
import time
import yaml
import arrow
import re

from dataclasses import dataclass
from enum import Enum
from typing import List


from server import database
from server.constants import MusicEffect
from server.evidence import EvidenceList
from server.exceptions import AreaError


class AreaManager:
	"""Holds the list of all areas."""
	@dataclass
	class Timer:
		set: bool = False
		started: bool = False
		static: arrow.Arrow = None
		target: arrow.Arrow = None
		schedule: asyncio.Future = None
	class Area:
		"""Represents a single instance of an area."""
		def __init__(self,
					 area_id,
					 server,
					 name,
					 background,
					 bg_lock=False,
					 evidence_mod='FFA',
					 locking_allowed=False,
					 iniswap_allowed=True,
					 showname_changes_allowed=True,
					 shouts_allowed=True,
					 jukebox=False,
					 abbreviation='',
					 non_int_pres_only=False,
					 is_hub=False,
					 hubid=0,
					 hubtype='default',
					 desc=''):
			self.timetomove = 0
			self.desc = ''
			self.is_hub = is_hub
			self.hubid = hubid
			self.hubtype = hubtype
			self.hub = None
			self.subareas = []
			self.sub = False
			self.cur_subid = 1
			self.iniswap_allowed = iniswap_allowed
			self.clients = set()
			self.invite_list = {}
			self.id = area_id
			self.name = name
			self.background = background
			self.bg_lock = bg_lock
			self.server = server
			self.next_message_time = 0
			self.hp_def = 10
			self.hp_pro = 10
			self.doc = 'No document.'
			self.status = 'IDLE'
			self.judgelog = []
			self.current_music = ''
			self.current_music_player = ''
			self.current_music_player_ipid = -1
			self.evi_list = EvidenceList()
			self.is_recording = False
			self.is_restricted = False
			self.recorded_messages = []
			self.statement = 0
			self.connections = []
			self.evidence_mod = evidence_mod
			self.locking_allowed = locking_allowed
			self.showname_changes_allowed = showname_changes_allowed
			self.shouts_allowed = shouts_allowed
			self.abbreviation = abbreviation
			self.music_looper = None
			self.cards = dict()
			self.custom_list = dict()
			self.cmusic_list = []
			self.cmusic_listname = ''
			self.hidden = False
			self.password = ''
			self.allowmusic = True
			self.areapair = dict()
			self.poslock = []
			self.last_speaker = None
			self.last_ooc = ''
			self.spies = set()
			self.loop = False
			self.webblock = False
			self.ambiance = ''
			self.timers = [AreaManager.Timer() for _ in range(4)]

			self.is_locked = self.Locked.FREE
			self.blankposting_allowed = True
			self.non_int_pres_only = non_int_pres_only
			self.jukebox = jukebox
			self.jukebox_votes = []
			self.jukebox_prev_char_id = -1

			self.owners = []

		class Locked(Enum):
			"""Lock state of an area."""
			FREE = 1,
			SPECTATABLE = 2,
			LOCKED = 3

		def new_client(self, client):
			"""Add a client to the area."""
			self.clients.add(client)
			lobby = self.server.area_manager.default_area()
			if self == lobby:
				for area in self.server.area_manager.areas:
					if area.is_hub:
						area.sub_arup_players()
						for sub in area.subareas:
							if sub.is_restricted and len(sub.clients) > 0:
								sub.conn_arup_players()
			if client.char_id != -1:
				database.log_room('area.join', client, self)
				if client.ambiance != self.ambiance:
					client.ambiance = self.ambiance
					client.send_command("MC", self.ambiance, -1, "", 1, 1, int(MusicEffect.FADE_OUT),)
				if self.loop:
					client.send_command("MC", 'None', -1, "", 0, 0, int(MusicEffect.FADE_OUT),)
					client.current_music = self.current_music
				else:
					if client.current_music != self.current_music:
						client.send_command("MC", self.current_music, -1, "", 1, 0, int(MusicEffect.FADE_OUT),)
						client.current_music = self.current_music
				
			if self.desc != '':
				client.send_ooc(self.desc)
				
			# Update the timers
			timer = self.server.area_manager.timer
			if timer.set:
				s = int(not timer.started)
				current_time = timer.static
				if timer.started:
					current_time = timer.target - arrow.get()
				int_time = int(current_time.total_seconds()) * 1000
				# Unhide the timer
				client.send_command('TI', 0, 2)
				# Start the timer
				client.send_command('TI', 0, s, int_time)
			else:
				# Stop the timer
				client.send_command('TI', 0, 3, 0)
				# Hide the timer
				client.send_command('TI', 0, 1)

			for timer_id, timer in enumerate(self.timers):
				# Send static time if applicable
				if timer.set:
					s = int(not timer.started)
					current_time = timer.static
					if timer.started:
						current_time = timer.target - arrow.get()
					int_time = int(current_time.total_seconds()) * 1000
					# Start the timer
					client.send_command('TI', timer_id+1, s, int_time)
					# Unhide the timer
					client.send_command('TI', timer_id+1, 2)
					client.send_ooc(f'Timer {timer_id+1} is at {current_time}')
				else:
					# Stop the timer
					client.send_command('TI', timer_id+1, 1, 0)
					# Hide the timer
					client.send_command('TI', timer_id+1, 3)

		def remove_client(self, client):
			"""Remove a disconnected client from the area."""
			self.clients.remove(client)
			if self.sub:
				for othersub in self.hub.subareas:
					if othersub.is_restricted:
						if self in othersub.connections:
							othersub.conn_arup_players()
			elif self.is_hub:
				for sub in self.subareas:
					if sub.is_restricted:
						sub.conn_arup_players()
			if len(self.clients) == 0:
				if len(self.owners) == 0 and not self.is_hub:
					self.change_status('IDLE')
			if client.char_id != -1:
				database.log_room('area.leave', client, self)

		def unlock(self):
			"""Mark the area as unlocked."""
			self.is_locked = self.Locked.FREE
			self.blankposting_allowed = True
			self.invite_list = {}
			if self.sub:
				for othersub in self.hub.subareas:
					if othersub.is_restricted:
						if self in othersub.connections:
							othersub.conn_arup_lock()
				else:
					self.hub.sub_arup_lock()
			elif self.is_hub:
				self.sub_arup_lock()
				self.server.area_manager.send_arup_lock()
			else:
				self.server.area_manager.send_arup_lock()
			self.broadcast_ooc('This area is open now.')
			
		def lock(self):
			"""Mark the area as locked."""
			self.is_locked = self.Locked.LOCKED
			for i in self.clients:
				self.invite_list[i.id] = None
			for i in self.owners:
				self.invite_list[i.id] = None
			if self.sub:
				for othersub in self.hub.subareas:
					if othersub.is_restricted:
						if self in othersub.connections:
							othersub.conn_arup_lock()
				else:
					self.hub.sub_arup_lock()
			elif self.is_hub:
				self.sub_arup_lock()
				self.server.area_manager.send_arup_lock()
			else:
				self.server.area_manager.send_arup_lock()
			self.broadcast_ooc('This area is locked now.')

		def spectator(self):
			"""Mark the area as spectator-only."""
			self.is_locked = self.Locked.SPECTATABLE
			for i in self.clients:
				self.invite_list[i.id] = None
			for i in self.owners:
				self.invite_list[i.id] = None
			if self.sub:
				if self.is_restricted:
					self.conn_arup_lock()
				else:
					self.hub.sub_arup_lock()
			elif self.is_hub:
				self.sub_arup_lock()
				self.server.area_manager.send_arup_lock()
			else:
				self.server.area_manager.send_arup_lock()
			self.broadcast_ooc('This area is spectatable now.')

		def is_char_available(self, char_id):
			"""
			Check if a character is available for use.
			:param char_id: character ID
			"""
			return char_id not in [x.char_id for x in self.clients]

		def get_rand_avail_char_id(self):
			"""Get a random available character ID."""
			avail_set = set(range(len(
				self.server.char_list))) - {x.char_id
											for x in self.clients}
			if len(avail_set) == 0:
				raise AreaError('No available characters.')
			return random.choice(tuple(avail_set))

		def send_command(self, cmd, *args):
			"""
			Broadcast an AO-compatible command to all clients in the area.
			"""
			for c in self.clients:
				c.send_command(cmd, *args)

		def send_owner_command(self, cmd, *args):
			"""
			Send an AO-compatible command to all owners of the area
			that are not currently in the area.
			"""
			for c in self.owners:
				if c not in self.clients and c.listen:
					c.send_command(cmd, *args)
			for spy in self.spies:
				if spy not in self.clients and spy not in self.owners:
					spy.send_command(cmd, *args)

		def broadcast_ooc(self, msg):
			"""
			Broadcast an OOC message to all clients in the area.
			:param msg: message
			"""
			self.send_command('CT', self.server.config['hostname'], msg, '1')
			self.send_owner_command(
				'CT',
				'[' + self.abbreviation + ']' + self.server.config['hostname'],
				msg, '1')

		def set_next_msg_delay(self, msg_length):
			"""
			Set the delay when the next IC message can be send by any client.
			:param msg_length: estimated length of message (ms)
			"""
			delay = min(3000, 100 + 60 * msg_length)
			self.next_message_time = round(time.time() * 1000.0 + delay)

		def is_iniswap(self, client, preanim, anim, char, sfx):
			"""
			Determine if a client is performing an INI swap.
			:param client: client attempting the INI swap.
			:param preanim: name of preanimation
			:param anim: name of idle/talking animation
			:param char: name of character

			"""
			if self.iniswap_allowed:
				return False
			#if '..' in preanim or '..' in anim or '..' in char:
				# Prohibit relative paths
			#	return True
			if char.lower() != client.char_name.lower():
				for char_link in self.server.allowed_iniswaps:
					# Only allow if both the original character and the
					# target character are in the allowed INI swap list
					if client.char_name in char_link and char in char_link:
						return False
			return not self.server.char_emotes[char].validate(preanim, anim, sfx)

			#if self.music_looper:
			#	self.music_looper.cancel()
			#self.music_looper = asyncio.get_event_loop().call_later(
			#	vote_picked.length, lambda: self.start_jukebox())

		def play_music(self, name, cid, length=0, effects=0):
			"""
			Play a track.
			:param name: track name
			:param cid: origin character ID
			:param length: track length (Default value = -1)
			"""
			if self.music_looper:
				self.music_looper.cancel()
			if self.loop or name.startswith('/custom'):
				if length != 0:
					self.music_looper = asyncio.get_event_loop().call_later(length, lambda: self.play_music(name, -1, length, effects))
				else:
					length = 1
			else:
				if length != 0:
					length = 1
			self.send_command('MC', name, cid, '', length, 0, effects)

		def play_msequence(self, file, index=0):
			now = 0
			with open(file, 'r', encoding='utf-8') as chars:
				sequence = yaml.safe_load(chars)
			for item in sequence:
				if index == now:
					index += 1
					name = item['name']
					length = item['length']
					if self.music_looper:
						self.music_looper.cancel()
					self.send_command('MC', name, -1, '', length, 0, int(MusicEffect.FADE_OUT))
					self.music_looper = asyncio.get_event_loop().call_later(length, lambda: self.play_msequence(file, index))
					return
				now += 1
			index = 0
			for item in sequence:
				index += 1
				if item['type'] != 'intro':
					name = item['name']
					length = item['length']
					if self.music_looper:
						self.music_looper.cancel()
					self.send_command('MC', name, -1, '', length, 0, int(MusicEffect.FADE_OUT))
					self.music_looper = asyncio.get_event_loop().call_later(length, lambda: self.play_msequence(file, index))
					return
			return

		def play_music_shownamed(self, name, cid, showname, length=0, effects=0):
			"""
			Play a track, but show showname as the player instead of character
			ID.
			:param name: track name
			:param cid: origin character ID
			:param showname: showname of origin user
			:param length: track length (Default value = -1)
			"""
			if self.music_looper:
				self.music_looper.cancel()
			if self.loop or name.startswith('/custom'):
				if length != 0:
					self.music_looper = asyncio.get_event_loop().call_later(length, lambda: self.play_music(name, -1, length, effects))
				else:
					length = 1
			else:
				if length != 0:
					length = 1
			self.send_command('MC', name, cid, showname, length, 0, effects)

		def music_shuffle(self, arg, client, track=-1):
			"""
			Shuffles through tracks randomly, either from entire music list or specific category.
			"""
			arg = arg
			client = client
			if len(arg) != 0:
				index = 0
				for item in self.server.music_list:
					if item['category'] == arg:
						for song in item['songs']:
							index += 1
				if index == 0:
					client.send_ooc('Category/music not found.')
					return
				else:
					music_set = set(range(index))
					trackid = random.choice(tuple(music_set))
					while trackid == track:
						trackid = random.choice(tuple(music_set))
					index = 0
					for item in self.server.music_list:
						if item['category'] == arg:
							for song in item['songs']:
								if index == trackid:
									self.play_music_shownamed(song['name'], client.char_id, '{} Shuffle'.format(arg))
									self.music_looper = asyncio.get_event_loop().call_later(song['length'], lambda: self.music_shuffle(arg, client, trackid))
									self.add_music_playing(client, song['name'])
									database.log_room('play', client, self, message=song['name'])
									return
								else:
									index += 1
			else:
				index = 0
				for item in self.server.music_list:
					for song in item['songs']:
						index += 1
				if index == 0:
					client.send_ooc('Category/music not found.')
					return
				else:
					music_set = set(range(index))
					trackid = random.choice(tuple(music_set))
					while trackid == track:
						trackid = random.choice(tuple(music_set))
					index = 0
					for item in self.server.music_list:
						for song in item['songs']:
							if index == trackid:
								self.play_music_shownamed(song['name'], client.char_id, 'Random Shuffle')
								self.music_looper = asyncio.get_event_loop().call_later(song['length'], lambda: self.music_shuffle(arg, client, trackid))
								self.add_music_playing(client, song['name'])
								database.log_room('play', client, self, message=song['name'])
								return
							else:
								index += 1

		def musiclist_shuffle(self, client, track=-1):
			client = client
			index = 0
			for item in client.area.cmusic_list:
				if 'songs' in item:
					for song in item['songs']:
						index += 1
				else:
					index += 1
			if index == 0:
				client.send_ooc('Area musiclist empty.')
				return
			else:
				music_set = set(range(index))
				trackid = random.choice(tuple(music_set))
				while trackid == track:
					trackid = random.choice(tuple(music_set))
				index = 0
				for item in client.area.cmusic_list:
					if 'songs' in item:
						for song in item['songs']:
							if index == trackid:
								if song['length'] <= 5:
									client.send_ooc('Track seems to have too little or no length, shuffle canceled.')
									return
								self.play_music_shownamed(song['name'], client.char_id, 'Custom Shuffle')
								self.music_looper = asyncio.get_event_loop().call_later(song['length'], lambda: self.musiclist_shuffle(client, trackid))
								self.add_music_playing(client, song['name'])
								database.log_room('play', client, self, message=song['name'])
								return
							else:
								index += 1
					else:
						if index == trackid:
							if item['length'] <= 5:
								client.send_ooc('Track seems to have too little or no length, shuffle canceled.')
								return
							self.play_music_shownamed(item['name'], client.char_id, 'Custom Shuffle')
							self.music_looper = asyncio.get_event_loop().call_later(item['length'], lambda: self.musiclist_shuffle(client, trackid))
							self.add_music_playing(client, item['name'])
							database.log_room('play', client, self, message=item['name'])
							return
						else:
							index += 1

		def can_send_message(self, client):
			"""
			Check if a client can send an IC message in this area.
			:param client: sender
			"""
			if self.cannot_ic_interact(client):
				client.send_ooc(
					'This is a locked area - ask the CM to speak.')
				return False
			return (time.time() * 1000.0 - self.next_message_time) > 0

		def cannot_ic_interact(self, client):
			"""
			Check if this room is locked to a client.
			:param client: sender
			"""
			return self.is_locked != self.Locked.FREE and not client.is_mod and not client.id in self.invite_list

		def change_hp(self, side, val):
			"""
			Set the penalty bars.
			:param side: 1 for defense; 2 for prosecution
			:param val: value from 0 to 10
			"""
			if not 0 <= val <= 10:
				raise AreaError('Invalid penalty value.')
			if not 1 <= side <= 2:
				raise AreaError('Invalid penalty side.')
			if side == 1:
				self.hp_def = val
			elif side == 2:
				self.hp_pro = val
			self.send_command('HP', side, val)

		def change_background(self, bg):
			"""
			Set the background.
			:param bg: background name
			:raises: AreaError if `bg` is not in background list
			"""
			if bg.lower() not in (name.lower()
								  for name in self.server.backgrounds):
				raise AreaError('Invalid background name.')
			self.background = bg
			self.send_command('BN', self.background)
		
		def change_cbackground(self, bg):
			"""
			Set the background.
			:param bg: background name
			:raises: AreaError if `bg` is not in background list
			"""
			self.background = bg
			self.send_command('BN', self.background)

		def change_status(self, value):
			"""
			Set the status of the room.
			:param value: status code
			"""
			allowed_values = ('idle', 'rp', 'casing', 'looking-for-players',
							  'lfp', 'recess', 'gaming')
			if value.lower() not in allowed_values:
				raise AreaError(
					f'Invalid status. Possible values: {", ".join(allowed_values)}'
				)
			if value.lower() == 'lfp':
				value = 'looking-for-players'
			self.status = value.upper()
			if self.sub:
				if self.hub.hubtype == 'arcade' or self.hub.hubtype == 'courtroom':
					if value == 'looking-for-players':
						self.hub.status = value.upper()
					else:
						lfp = False
						idle = True
						recess = True
						for area in self.hub.subareas:
							if area.status == 'LOOKING-FOR-PLAYERS':
								lfp = True
							if area.status != 'IDLE':
								idle = False
							if area.status == 'RP' or area.status == 'CASING' or area.status == 'GAMING':
								recess = False
						if lfp == False and not value.lower() == 'idle' and not value.lower() == 'recess':
							self.hub.status = value.upper()
						if value.lower() == 'idle' and idle == True:
							self.hub.status = value.upper()
						if value.lower() == 'recess' and recess == True:
							self.hub.status = value.upper()
						if self.hub.status == 'LOOKING-FOR-PLAYERS' and value.lower() == 'recess' or self.hub.status == 'LOOKING-FOR-PLAYERS' and value.lower() == 'idle':
							if lfp == False:
								for area in self.hub.subareas:
									if area.status == 'CASING':
										self.hub.status = 'CASING'	
										break
									elif area.status == 'GAMING':
										self.hub.status = 'GAMING'
										break
									elif area.status == 'RP':
										self.hub.status = 'RP'
										break					
					self.server.area_manager.send_arup_status()
				if self.is_restricted:
					self.conn_arup_status()
				else:
					self.hub.sub_arup_status()
				
			elif self.is_hub:
				self.sub_arup_status()
				self.server.area_manager.send_arup_status()
			else:
				self.server.area_manager.send_arup_status()
		
		def hub_status(self, value):
			"""
			Set the status of all areas in a hub.
			:param value: status code
			"""
			allowed_values = ('idle', 'rp', 'casing', 'looking-for-players',
							  'lfp', 'recess', 'gaming')
			if value.lower() not in allowed_values:
				raise AreaError(
					f'Invalid status. Possible values: {", ".join(allowed_values)}'
				)
			if value.lower() == 'lfp':
				value = 'looking-for-players'
			self.status = value.upper()
			for area in self.subareas:
				area.status = value.upper()
				if area.is_restricted:
					self.conn_arup_status()
			self.sub_arup_status()
			self.server.area_manager.send_arup_status()

		def change_doc(self, doc='No document.'):
			"""
			Set the doc link.
			:param doc: doc link (Default value = 'No document.')
			"""
			self.doc = doc

		def add_to_judgelog(self, client, msg):
			"""
			Append an event to the judge log (max 10 items).
			:param client: event origin
			:param msg: event message
			"""
			if len(self.judgelog) >= 10:
				self.judgelog = self.judgelog[1:]
			self.judgelog.append(
				f'{client.char_name} ({client.ip}) {msg}.')

		def add_music_playing(self, client, name):
			"""
			Set info about the current track playing.
			:param client: player
			:param name: track name
			"""
			self.current_music_player = client.char_name
			self.current_music_player_ipid = client.ipid
			self.current_music = name

		def add_music_playing_shownamed(self, client, showname, name):
			"""
			Set info about the current track playing.
			:param client: player
			:param showname: showname of player
			:param name: track name
			"""
			self.current_music_player = f'{showname} ({client.char_name})'
			self.current_music_player_ipid = client.ipid
			self.current_music = name

		def get_evidence_list(self, client):
			"""
			Get the evidence list of the area.
			:param client: requester
			"""
			client.evi_list, evi_list = self.evi_list.create_evi_list(client)
			return evi_list

		def broadcast_evidence_list(self):
			"""
			Broadcast an updated evidence list.
			LE#<name>&<desc>&<img>#<name>
			"""
			for client in self.clients:
				client.send_command('LE', *self.get_evidence_list(client))

		def get_cms(self):
			"""
			Get a list of CMs.
			:return: message
			"""
			msg = ''
			for i in self.owners:
				if not i.ghost:
					msg += f'[{str(i.id)}] {i.char_name}, '
			if len(msg) > 2:
				msg = msg[:-2]
			return msg

		def get_mods(self):
			mods = set()
			for client in self.clients:
				if client.is_mod:
					mods.add(client)
			return mods
	
		def get_sub(self, name):
			for area in self.subareas:
				if area.name == name:
					return area
			raise AreaError('Area not found.')
			
		def get_music(self, client):
			song_list = []
			music_list = self.server.music_list
			for item in music_list:
				song_list.append(item['category'])
				for song in item['songs']:
					song_list.append(song['name'])
			if len(self.cmusic_list) != 0:
				for item in self.cmusic_list:
					song_list.append(item['category'])
					if len(item['songs']) != 0:
						for song in item['songs']:
							song_list.append(song['name'])
			return song_list

		def conn_arup_players(self):
			players_list = [0]
			lobby = self.server.area_manager.default_area()
			players_list.append(len(lobby.clients))
			if self.hub.hidden:
				players_list.append(-1)
			else:
				players_list.append(len(self.hub.clients))
			if self.hidden:
				players_list.append(-1)
			else:
				players_list.append(len(self.clients))
			for link in self.connections:
				if link != lobby and link != self.hub:
					if link.hidden:
						players_list.append(-1)
					else:
						players_list.append(len(link.clients))
			self.server.send_conn_arup(players_list, self)	

		def conn_arup_status(self):
			"""Broadcast ARUP packet containing area statuses."""
			status_list = [1]
			lobby = self.server.area_manager.default_area()
			status_list.append(lobby.status)
			status_list.append(self.hub.status)
			status_list.append(self.status)
			for link in self.connections:
				if link != lobby and link != self.hub:
					status_list.append(link.status)
			self.server.send_conn_arup(status_list, self)
			
		def conn_arup_cms(self):
			"""Broadcast ARUP packet containing area CMs."""
			cms_list = [2]
			lobby = self.server.area_manager.default_area()
			if len(lobby.owners) == 0:
				cms_list.append('FREE')
			else:
				cms_list.append(lobby.get_cms())
			if len(self.hub.owners) == 0:
				cms_list.append('FREE')
			else:
				cms_list.append(self.hub.get_cms())
			if len(self.owners) == 0:
				cms_list.append('FREE')
			else:
				cms_list.append(self.get_cms())
			for link in self.connections:
				if link != lobby and link != self.hub:
					cm = 'FREE'
					if len(link.owners) > 0:
						cm = link.get_cms()
					cms_list.append(cm)
			self.server.send_conn_arup(cms_list, self)
			
		def conn_arup_lock(self):
			"""Broadcast ARUP packet containing the lock status of each area."""
			lock_list = [3]
			lobby = self.server.area_manager.default_area()
			lock_list.append(lobby.is_locked.name)
			lock_list.append(self.hub.is_locked.name)
			lock_list.append(self.is_locked.name)
			for link in self.connections:
				if link != lobby and link != self.hub:
					lock_list.append(link.is_locked.name)
			self.server.send_hub_arup(lock_list, self)

		def sub_arup_players(self, client=None):
			"""Broadcast ARUP packet containing player counts."""
			players_list = [0]
			lobby = self.server.area_manager.default_area()
			players_list.append(len(lobby.clients))
			players_list.append(len(self.clients))
			for area in self.subareas:
				if area.hidden == True:
					players_list.append(-1)
				else:
					index = 0
					for c in area.clients:
						if not c.ghost and not c.hidden:
							index += 1
					players_list.append(index)
			if client != None:
				client.send_self_arup(players_list)
			else:
				self.server.send_hub_arup(players_list, self)

		def sub_arup_status(self, client=None):
			"""Broadcast ARUP packet containing area statuses."""
			status_list = [1]
			lobby = self.server.area_manager.default_area()
			status_list.append(lobby.status)
			status_list.append(self.status)
			for area in self.subareas:
				status_list.append(area.status)
			if client != None:
				client.send_self_arup(status_list)
			else:
				self.server.send_hub_arup(status_list, self)

		def sub_arup_cms(self, client=None):
			"""Broadcast ARUP packet containing area CMs."""
			cms_list = [2]
			lobby = self.server.area_manager.default_area()
			if len(lobby.owners) == 0:
				cms_list.append('FREE')
			else:
				cms_list.append(lobby.get_cms())
			if len(self.owners) == 0:
				cms_list.append('FREE')
			else:
				cms_list.append(self.get_cms())
			for area in self.subareas:
				cm = 'FREE'
				if len(area.owners) > 0:
					cm = area.get_cms()
				cms_list.append(cm)
			if client != None:
				client.send_self_arup(cms_list)
			else:
				self.server.send_hub_arup(cms_list, self)

		def sub_arup_lock(self, client=None):
			"""Broadcast ARUP packet containing the lock status of each area."""
			lock_list = [3]
			lobby = self.server.area_manager.default_area()
			lock_list.append(lobby.is_locked.name)
			lock_list.append(self.is_locked.name)
			for area in self.subareas:
				lock_list.append(area.is_locked.name)
			if client != None:
				client.send_self_arup(lock_list)
			else:
				self.server.send_hub_arup(lock_list, self)

		def broadcast_hub(self, client, msg):
			char_name = client.char_name
			ooc_name = '{}[{}][{}]'.format('<dollar>H', client.area.abbreviation, char_name)
			if client.area.sub:
				if client in client.area.hub.owners:
					ooc_name += '[CM]'
				self.server.send_all_cmd_pred('CT', ooc_name, msg, pred=lambda x: x.area in client.area.hub.subareas)
				self.server.send_all_cmd_pred('CT', ooc_name, msg, pred=lambda x: x.area is client.area.hub)
			else:
				if client in client.area.owners:
					ooc_name += '[CM]'
				self.server.send_all_cmd_pred('CT', ooc_name, msg, pred=lambda x: x.area in client.area.subareas)
				self.server.send_all_cmd_pred('CT', ooc_name, msg, pred=lambda x: x.area is client.area)
		
		class JukeboxVote:
			"""Represents a single vote cast for the jukebox."""
			def __init__(self, client, name, length, showname):
				self.client = client
				self.name = name
				self.length = length
				self.chance = 1
				self.showname = showname

	def __init__(self, server):
		self.server = server
		self.cur_id = 0
		self.areas = []
		self.load_areas()
		self.timer = AreaManager.Timer()

	def load_areas(self):
		"""Create all areas from a YAML file."""
		with open('config/areas.yaml', 'r') as chars:
			areas = yaml.safe_load(chars)
		for item in areas:
			if 'evidence_mod' not in item:
				item['evidence_mod'] = 'FFA'
			if 'locking_allowed' not in item:
				item['locking_allowed'] = False
			if 'iniswap_allowed' not in item:
				item['iniswap_allowed'] = True
			if 'showname_changes_allowed' not in item:
				item['showname_changes_allowed'] = True
			if 'shouts_allowed' not in item:
				item['shouts_allowed'] = True
			if 'jukebox' not in item:
				item['jukebox'] = False
			if 'noninterrupting_pres' not in item:
				item['noninterrupting_pres'] = False
			if 'abbreviation' not in item:
				item['abbreviation'] = self.abbreviate(item['area'])
			if 'is_hub' not in item:
				item['is_hub'] = False
			if 'hub_id' not in item:
				item['hub_id'] = 0
			if 'hubtype' not in item:
				item['hubtype'] = 'default'
			self.areas.append(
				self.Area(self.cur_id, self.server, item['area'],
						  item['background'], item['bglock'],
						  item['evidence_mod'], item['locking_allowed'],
						  item['iniswap_allowed'],
						  item['showname_changes_allowed'],
						  item['shouts_allowed'], item['jukebox'],
						  item['abbreviation'], item['noninterrupting_pres'], item['is_hub'], item['hub_id'], item['hubtype']))
			self.cur_id += 1

	def default_area(self):
		"""Get the default area."""
		return self.areas[0]

	def get_area_by_name(self, name, client=None):
		"""Get an area by name."""
		for area in self.areas:
			if area.name == name:
				return area
			if area.is_hub:
				if client != None:
					if client.area == area or client.area.hub == area:
						for sub in area.subareas:
							if sub.name == name:
								return sub
		raise AreaError('Area not found.')
	
	def get_area_by_abbreviation(self, abbreviation):
		"""Get an area by name."""
		for area in self.areas:
			if area.abbreviation == abbreviation:
				return area
			if area.is_hub:
				for sub in area.subareas:
					if sub.abbreviation == abbreviation:
						return sub
		raise AreaError('Area not found.')

	def get_area_by_id(self, num):
		"""Get an area by ID."""
		for area in self.areas:
			if area.id == num:
				return area
		raise AreaError('Area not found.')

	def abbreviate(self, name):
		"""Abbreviate the name of a room."""
		if name.lower().startswith("courtroom"):
			return "CR" + name.split()[-1]
		elif name.lower().startswith("area"):
			return "A" + name.split()[-1]
		elif len(name.split()) > 1:
			return "".join(item[0].upper() for item in name.split())
		elif len(name) > 3:
			return name[:3].upper()
		else:
			return name.upper()

	def send_remote_command(self, areas, cmd, *args):
		"""
		Broadcast an AO-compatible command to a specified
		list of areas and their owners.
		:param area_ids: list of area IDs
		:param cmd: command name
		:param *args: command arguments
		"""
		for area in areas:
			area.send_command(cmd, *args)
			area.send_owner_command(cmd, *args)

	def send_arup_players(self):
		"""Broadcast ARUP packet containing player counts."""
		players_list = [0]
		for area in self.areas:
			if area.hidden == True:
				players_list.append(-1)
			else:
				index = 0
				for client in area.clients:
					if not client.ghost and not client.hidden:
						index += 1
				if area.is_hub:
					for sub in area.subareas:
						for client in sub.clients:
							if not client.ghost and not client.hidden:
								index += 1
				players_list.append(index)
		self.server.send_arup(players_list)

	def send_arup_status(self, client=None):
		"""Broadcast ARUP packet containing area statuses."""
		status_list = [1]
		for area in self.areas:
			status_list.append(area.status)
		if client != None:
			client.send_self_arup(status_list)
		else:
			self.server.send_arup(status_list)

	def send_arup_cms(self, client=None):
		"""Broadcast ARUP packet containing area CMs."""
		cms_list = [2]
		for area in self.areas:
			cm = 'FREE'
			if len(area.owners) > 0:
				cm = area.get_cms()
			cms_list.append(cm)
		if client != None:
			client.send_self_arup(cms_list)
		else:
			self.server.send_arup(cms_list)

	def send_arup_lock(self, client=None):
		"""Broadcast ARUP packet containing the lock status of each area."""
		lock_list = [3]
		for area in self.areas:
			lock_list.append(area.is_locked.name)
		if client != None:
			client.send_self_arup(lock_list)
		else:
			self.server.send_arup(lock_list)
		
	def mods_online(self):
		num = 0
		for area in self.areas:
			num += len(area.get_mods())
			if area.is_hub and len(area.subareas) > 0:
				for sub in area.subareas:
					num += len(sub.get_mods())
		return num