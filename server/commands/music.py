import random
import asyncio
import shlex
import re

from server import database
from server.constants import TargetType
from server.exceptions import ClientError, ServerError, ArgumentError
from server.constants import TargetType

from . import mod_only

__all__ = [
	'ooc_cmd_currentmusic',
	'ooc_cmd_music',
	'ooc_cmd_jukeboxtoggle',
	'ooc_cmd_jukeboxskip',
	'ooc_cmd_jukebox',
	'ooc_cmd_play',
	'ooc_cmd_hubplay',
	'ooc_cmd_playrandom',
	'ooc_cmd_shuffle',
	'ooc_cmd_blockdj',
	'ooc_cmd_unblockdj',
	'ooc_cmd_addmusic',
	'ooc_cmd_addcategory',
	'ooc_cmd_musiclist',
	'ooc_cmd_storemlist',
	'ooc_cmd_loadmlist',
	'ooc_cmd_clearmusiclist',
	'ooc_cmd_ambiance'
]


def ooc_cmd_ambiance(client, arg):
	if not client.is_mod and client not in client.area.owners:
		raise ClientError('You must be a CM.')
	area = client.area
	if area.ambiance:
		area.ambiance = False
		area.broadcast_ooc('Ambiance for this area has been disabled, music played will loop client-side.')
		if area.is_hub:
			for sub in area.subareas:
				sub.ambiance = False
				sub.broadcast_ooc('Ambiance for this area has been disabled, music played will loop client-side.')
	else:
		area.ambiance = True
		area.broadcast_ooc('Ambiance for this area has been enabled, music played will loop server-side.')
		if area.is_hub:
			for sub in area.subareass:
				sub.ambiance = True
				sub.broadcast_ooc('Ambiance for this area has been enabled, music played will loop server-side.')
		
		
def ooc_cmd_addmusic(client, arg):
	if client not in client.area.owners and not client.is_mod:
		raise ClientError('You must be a CM.')
	args = shlex.split(arg)
	mlist = client.area.cmusic_list
	if len(args) < 2:
		raise ArgumentError('Not enough arguments. Use /addmusic "name" "length in seconds".')
	elif len(args) == 2:
		try:
			length = int(args[1])
		except ValueError:
			raise ClientError(f'Given length does not look like a valid length.')
		if len(mlist) == 0:
			songs = []
			mlist.append({'category': 'CUSTOM'})
			mlist[-1]['songs'] = songs
			mlist[-1]['songs'].append({'name': args[0], 'length': length})
		else:
			mlist[-1]['songs'].append({'name': args[0], 'length': length})
		client.area.broadcast_ooc(f'{args[0]} added to the music list.')
		music = client.area.get_music(client)
		if client.area.is_hub:
			for sub in client.area.subareas:
				sub.cmusic_list = mlist
			client.server.send_all_cmd_pred('FM', *music, pred=lambda x: x.area == client.area or x.area.hub == client.area)
		else:
			client.server.send_all_cmd_pred('FM', *music, pred=lambda x: x.area == client.area)
	else:
		raise ArgumentError('Too many arguments.')

def ooc_cmd_addcategory(client, arg):
	if client not in client.area.owners and not client.is_mod:
		raise ClientError('You must be a CM.')
	if len(arg) > 30:
		raise ArgumentError('That name is too long!')
	mlist = client.area.cmusic_list
	songs = []
	mlist.append({'category': arg})
	mlist[-1]['songs'] = songs
	music = client.area.get_music(client)
	if client.area.is_hub:
		for sub in client.area.subareas:
			sub.cmusic_list = mlist
		client.server.send_all_cmd_pred('FM', *music, pred=lambda x: x.area == client.area or x.area.hub == client.area)
	else:
		client.server.send_all_cmd_pred('FM', *music, pred=lambda x: x.area == client.area)
	client.area.broadcast_ooc(f'Category added to the music list.')

def ooc_cmd_storemlist(client, arg):
	if client not in client.area.owners and not client.is_mod:
		raise ClientError('You must be a CM.')
	if len(arg) < 1:
		raise ArgumentError('Your stored list requires a name!')
	if len(arg) > 12:
		raise ArgumentError('Keep the name of your list to 12 characters or below.')
	if len(client.area.cmusic_list) == 0:
		raise ArgumentError('No list to store!')
	if '/' in arg or "\\" in arg or '..' in arg:
		raise ArgumentError('Contains bad characters')
	client.server.musiclist_manager.storelist(client, arg)

def ooc_cmd_loadmlist(client, arg):
	if client not in client.area.owners and not client.is_mod:
		raise ClientError('You must be a CM.')
	if len(arg) < 1:
		raise ArgumentError('Your stored list requires a name!')
	if len(arg) > 12:
		raise ArgumentError('Keep the name of your list to 12 characters or below.')
	if '/' in arg or "\\" in arg or '..' in arg:
		raise ArgumentError('Contains bad characters')
	client.server.musiclist_manager.loadlist(client, arg)

def ooc_cmd_musiclist(client, arg):
	if len(arg) > 0:
		raise ArgumentError('This command takes no arguments.')
	if len(client.area.cmusic_list) == 0:
		raise ArgumentError('Music list is empty.')
	msg = 'This area has no musiclist.'
	if len(client.area.cmusic_list) != 0:
		msg = 'Music List:'
		for item in client.area.cmusic_list:
			msg += f"\n{item['category']}:"
			if len(item['songs']) != 0:
				for song in item['songs']:
					msg += f"\n{song['name']}"
	client.send_ooc(msg)

def ooc_cmd_clearmusiclist(client, arg):
	if not client.area.name.startswith('Custom'):
		if client not in client.area.owners and not client.is_mod:
			raise ClientError('You must be a CM.')
	if len(arg) > 0:
		raise ArgumentError('This command takes no arguments.')
	client.area.cmusic_list = []
	client.area.cmusic_listname = ''
	client.send_ooc(f'Area music list cleared.')

def ooc_cmd_play(client, arg):
	"""
	Play a track.
	Usage: /play <name>
	"""
	if client not in client.area.owners and not client.is_mod:
		raise ClientError('You must be a CM.')
	args = shlex.split(arg)
	if len(args) < 1:
		raise ArgumentError('Not enough arguments. Use /play "name" "length in seconds".')
	elif len(args) == 2:
		if re.match(r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?", args[0]):
			if '.mp3' not in args[0]:
				raise ArgumentError("Doesn't seem to be an mp3.")
			if '.mp3/' in args[0]:
				raise ArgumentError("Don't be sneaky.")
			name = ''
			length = args[1]
		else:
			name = 'custom/'
			length = args[1]
		name += args[0]
		
		try:
			length = int(args[1])
		except ValueError:
			raise ClientError(f'{length} does not look like a valid length.')
	elif len(args) == 1:
		if re.match(r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?", args[0]):
			if '.mp3' not in args[0]:
				raise ArgumentError("Doesn't seem to be an mp3.")
			if '.mp3/' in args[0]:
				raise ArgumentError("Don't be sneaky.")
			name = ''
			length: 0
		else:
			name = 'custom/'
		name += args[0]
		length = 0
	else:
		raise ArgumentError('Too many arguments. Use /play "name" "length in seconds".')
	client.area.play_music(name, client.char_id, length)
	client.area.add_music_playing(client, args[0])
	database.log_room('play', client, client.area, message=name)
	
def ooc_cmd_hubplay(client, arg):
	"""
	Play a track.
	Usage: /play <name>
	"""
	if client not in client.area.owners and not client.is_mod:
		if client.area.sub:
			if not client in client.area.hub.owners:
				raise ClientError('You must be a CM.')
		else:
			raise ClientError('You must be a CM.')
	if not client.area.is_hub and not client.area.sub:
		raise ClientError('Must be in hub.')
	if len(arg) == 0:
		raise ArgumentError('Not enough arguments. Use /hubplay <name>.')
	elif len(arg) > 0:
		custom = False
		try:
			name, length, mod, custom = client.server.get_song_data(arg, client.client.area)
		except:
			name = arg
			length = -1
			client.send_ooc('Track not found in area\'s music list, playing directly without length.')
		if custom:
			name = f'custom/{arg}'
	if client.area.is_hub:
		for sub in client.area.subareas:
			sub.play_music(name, client.char_id, length)
			sub.add_music_playing(client, arg)
			database.log_room('hubplay', client, sub, message=name)
		return
	elif client.area.sub:
		for sub in client.area.hub.subareas:
			sub.play_music(name, client.char_id, length)
			sub.add_music_playing(client, arg)
			database.log_room('hubplay', client, sub, message=name)
		return

def ooc_cmd_currentmusic(client, arg):
	"""
	Show the current music playing.
	Usage: /currentmusic
	"""
	if len(arg) != 0:
		raise ArgumentError('This command has no arguments.')
	if client.area.current_music == '':
		raise ClientError('There is no music currently playing.')
	if client.is_mod:
		client.send_ooc(
			'The current music is {} and was played by {} ({}).'.format(
				client.area.current_music, client.area.current_music_player,
				client.area.current_music_player_ipid))
	else:
		client.send_ooc(
			'The current music is {} and was played by {}.'.format(
				client.area.current_music, client.area.current_music_player))


def ooc_cmd_music(client, arg):
	"""
	Show the current music playing.
	Usage: /music
	"""
	ooc_cmd_currentmusic(client, arg)

def ooc_cmd_jukeboxtoggle(client, arg):
	"""
	Toggle jukebox mode. While jukebox mode is on, all music changes become
	votes for the next track, rather than changing the track immediately.
	Usage: /jukebox_toggle
	"""
	if len(arg) != 0:
		raise ArgumentError('This command has no arguments.')
	if client not in client.area.owners and not client.is_mod:
		raise ClientError('You must be a CM.')
	client.area.jukebox = not client.area.jukebox
	client.area.jukebox_votes = []
	client.area.broadcast_ooc('{} [{}] has set the jukebox to {}.'.format(
		client.char_name, client.id, client.area.jukebox))
	database.log_room('jukebox_toggle', client, client.area,
		message=client.area.jukebox)


def ooc_cmd_jukeboxskip(client, arg):
	"""
	Skip the current track.
	Usage: /jukebox_skip
	"""
	if len(arg) != 0:
		raise ArgumentError('This command has no arguments.')
	if not client.area.jukebox:
		raise ClientError('This area does not have a jukebox.')
	if len(client.area.jukebox_votes) == 0:
		raise ClientError('There is no song playing right now, skipping is pointless.')
	if client not in client.area.owners and not client.is_mod:
		raise ClientError('You must be a CM.')
	client.area.start_jukebox()
	if len(client.area.jukebox_votes) == 1:
		client.area.broadcast_ooc(
			'{} [{}] has forced a skip, restarting the only jukebox song.'.
			format(client.char_name, client.id))
	else:
		client.area.broadcast_ooc(
			'{} [{}] has forced a skip to the next jukebox song.'.format(
				client.char_name, client.id))
	database.log_room('jukebox_skip', client, client.area)


def ooc_cmd_jukebox(client, arg):
	"""
	Show information about the jukebox's queue and votes.
	Usage: /jukebox
	"""
	if len(arg) != 0:
		raise ArgumentError('This command has no arguments.')
	if not client.area.jukebox:
		raise ClientError('This area does not have a jukebox.')
	if len(client.area.jukebox_votes) == 0:
		client.send_ooc('The jukebox has no songs in it.')
	else:
		total = 0
		songs = []
		voters = dict()
		chance = dict()
		message = ''

		for current_vote in client.area.jukebox_votes:
			if songs.count(current_vote.name) == 0:
				songs.append(current_vote.name)
				voters[current_vote.name] = [current_vote.client]
				chance[current_vote.name] = current_vote.chance
			else:
				voters[current_vote.name].append(current_vote.client)
				chance[current_vote.name] += current_vote.chance
			total += current_vote.chance

		for song in songs:
			message += '\n- ' + song + '\n'
			message += '-- VOTERS: '

			first = True
			for voter in voters[song]:
				if first:
					first = False
				else:
					message += ', '
				message += voter.char_name + ' [' + str(voter.id) + ']'
				if client.is_mod:
					message += '(' + str(voter.ipid) + ')'
			message += '\n'

			if total == 0:
				message += '-- CHANCE: 100'
			else:
				message += '-- CHANCE: ' + str(
					round(chance[song] / total * 100))

		client.send_ooc(
			f'The jukebox has the following songs in it:{message}')

def ooc_cmd_playrandom(client, arg):
	"""
	Plays a random track.
	Usage: /playrandom
	"""
	if len(arg) > 0:
		raise ArgumentError('This command takes no arguments.')
	index = 0
	for item in client.server.music_list:
		for song in item['songs']:
			index += 1
	if index == 0:
		raise ServerError(
				'No music found.')
	else:
		music_set = set(range(index))
		trackid = random.choice(tuple(music_set))
		index = 1
		for item in client.server.music_list:
			for song in item['songs']:
				if index == trackid:
					client.area.play_music(song['name'], client.char_id, song['length'])
					client.area.add_music_playing(client, song['name'])
					database.log_room('play', client, client.area, message=song['name'])
					return
				else:
					index += 1

def ooc_cmd_shuffle(client, arg):
	"""
	Play a track.
	Usage: /play <name>
	"""
	if arg == 'musiclist' or 'custom':
		client.area.musiclist_shuffle(client)
	else:
		client.area.music_shuffle(arg, client)

@mod_only()
def ooc_cmd_blockdj(client, arg):
	"""
	Prevent a user from changing music.
	Usage: /blockdj <id>
	"""
	if len(arg) == 0:
		raise ArgumentError('You must specify a target. Use /blockdj <id>.')
	try:
		targets = client.server.client_manager.get_targets(
			client, TargetType.ID, int(arg), False)
	except:
		raise ArgumentError('You must enter a number. Use /blockdj <id>.')
	if not targets:
		raise ArgumentError('Target not found. Use /blockdj <id>.')
	for target in targets:
		target.is_dj = False
		target.send_ooc(
			'A moderator muted you from changing the music.')
		database.log_room('blockdj', client, client.area, target=target)
		client.send_ooc('blockdj\'d {}.'.format(target.char_name))

@mod_only()
def ooc_cmd_unblockdj(client, arg):
	"""
	Unblock a user from changing music.
	Usage: /unblockdj <id>
	"""
	if len(arg) == 0:
		raise ArgumentError('You must specify a target. Use /unblockdj <id>.')
	try:
		targets = client.server.client_manager.get_targets(
			client, TargetType.ID, int(arg), False)
	except:
		raise ArgumentError('You must enter a number. Use /unblockdj <id>.')
	if not targets:
		raise ArgumentError('Target not found. Use /blockdj <id>.')
	for target in targets:
		target.is_dj = True
		target.send_ooc(
			'A moderator unmuted you from changing the music.')
		database.log_room('unblockdj', client, client.area, target=target)
	client.send_ooc('Unblockdj\'d {}.'.format(
		targets[0].char_name))
