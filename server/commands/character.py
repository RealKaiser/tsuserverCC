import random

from server import database
from server.constants import TargetType
from server.exceptions import ClientError, ServerError, ArgumentError, AreaError

from . import mod_only

# List with all OOC commands in this file.
# If you wish to add a new OOC command, insert it here.
# Otherwise, it won't work.

__all__ = [
	'ooc_cmd_switch',
	'ooc_cmd_pos',
	'ooc_cmd_forcepos',
	'ooc_cmd_charselect',
	'ooc_cmd_randomchar',
	'ooc_cmd_rc',
	'ooc_cmd_charcurse',
	'ooc_cmd_uncharcurse',
	'ooc_cmd_charids',
	'ooc_cmd_reload',
	'ooc_cmd_visible',
	'ooc_cmd_narrator',
	'ooc_cmd_addfiles',
	'ooc_cmd_removefiles',
	'ooc_cmd_files',
	'ooc_cmd_kickother'
]

def ooc_cmd_addfiles(client, arg: str) -> None:
	"""
	Add a client's files link.
	Usage: /addcustom <link>
	"""
	if len(arg) == 0:
		raise ArgumentError('You must specify a link. Use /addcustom <link>.')
	if len(arg) > 200:
		raise ArgumentError('That link is too long.')
	client.files = arg
	client.area.broadcast_ooc('{} added a link for their files.'.format(client.char_name))

def ooc_cmd_removefiles(client, arg: str) -> None:
	"""
	Removes a client's files link.
	Usage: /removecustom
	"""
	if len(arg) > 0:
		raise ArgumentError('This command takes no arguments.')
	client.files = ''
	client.area.broadcast_ooc('{} removed link for their files.'.format(client.char_name))

def ooc_cmd_files(client, arg: str) -> None:
	"""
	Shows the files list
	Usage: /files
	"""
	if len(arg) > 0:
		raise ArgumentError('This command takes no arguments.')
	msg = 'Files List:'
	list = ''
	for c in client.area.clients:
		if c.files != '':
			if c.showname != '':
				list += f'\n{c.showname} ({c.charname}): {c.files}'
			else:
				list += f'\n{c.charname}: {c.files}'
	if list != '':
		msg += list
	else:
		msg = 'No players in the area have set their files'
	client.send_ooc(msg)

def ooc_cmd_narrator(client, arg):
	if len(arg) > 0:
		raise ArgumentError('This command takes no arguments.')
	if client not in client.area.owners and not client.is_mod:
		raise ClientError('You must be a CM.')
	if client.narrator:
		client.narrator = False
		client.send_ooc('You are no longer speaking as Narrator.')
	else:
		client.narrator = True
		client.send_ooc('You are now speaking as Narrator.')

def ooc_cmd_visible(client, arg):
	if len(arg) > 0:
		raise ArgumentError('This command takes no arguments.')
	if client.visible:
		client.visible = False
		client.send_ooc('You are no longer visible, your emotes won\'t be shown.')
	else:
		client.visible = True
		client.send_ooc('You are now visible, your emotes will be shown.')

def ooc_cmd_switch(client, arg):
	"""
	Switch to another character. If moderator and the specified character is
	currently being used, the current user of that character will be
	automatically reassigned a character.
	Usage: /switch <name>
	"""
	if len(arg) == 0:
		raise ArgumentError('You must specify a character name.')
	try:
		cid = client.server.get_char_id_by_name(arg)
	except ServerError:
		raise
	try:
		client.change_character(cid, client.is_mod)
	except ClientError:
		raise
	client.send_ooc('Character changed.')


def ooc_cmd_pos(client, arg):
	"""
	Set the place your character resides in the room.
	Usage: /pos <name>
	"""
	if len(arg) == 0:
		client.change_position('', True)
		client.send_ooc('Position reset.')
	else:
		client.change_position(arg)


def ooc_cmd_forcepos(client, arg):
	"""
	Set the place another character resides in the room.
	Usage: /forcepos <pos> <target>
	"""
	args = arg.split()

	if client not in client.area.owners and not client.is_mod:
		raise ClientError ('You are not a CM.')
	elif len(args) < 1:
		raise ArgumentError('Not enough arguments. Use /forcepos <pos> <target>. Target should be ID. Use /getarea for getting info like "[ID] char-name".')

	targets = []

	pos = args[0]
	if len(args) > 1:
		for id in args:
			if id != pos:
				try:
					c = client.server.client_manager.get_targets(client, TargetType.ID, int(id), True)
					targets.append(c[0])
				except:
					raise ArgumentError(f'{id} does not seem to be a valid ID. Make sure you enter the pos first and then IDs after.')
		if len(targets) == 0:
			raise ArgumentError('No targets found.')
	else:
		for c in client.area.clients:
			targets.append(c)

	for t in targets:
		try:
			t.change_position(pos)
			t.area.broadcast_evidence_list()
			t.send_ooc(f'Forced into /pos {pos}.')
			database.log_room('forcepos', client, client.area, target=t, message=pos)
		except ClientError:
			raise

	client.area.broadcast_ooc('{} forced {} client(s) into /pos {}.'.format(client.char_name, len(targets), pos))


def ooc_cmd_charselect(client, arg):
	"""
	Enter the character select screen, or force another user to select
	another character.
	Usage: /charselect [id]
	"""
	if not arg:
		client.char_select()
	else:
		force_charselect(client, arg)


@mod_only()
def force_charselect(client, arg):
	try:
		client.server.client_manager.get_targets(client, TargetType.ID,
			int(arg), False)[0].char_select()
	except:
		raise ArgumentError('Wrong arguments. Use /charselect <target\'s id>')


def ooc_cmd_randomchar(client, arg):
	"""
	Select a random character.
	Usage: /randomchar
	"""
	if len(arg) != 0:
		raise ArgumentError('This command has no arguments.')
	if len(client.charcurse) > 0:
		free_id = random.choice(client.charcurse)
	else:
		try:
			free_id = client.area.get_rand_avail_char_id()
		except AreaError:
			raise
	try:
		client.change_character(free_id)
	except ClientError:
		raise
	client.send_ooc('Randomly switched to {}'.format(
		client.char_name))
		
def ooc_cmd_rc(client, arg):
	"""
	Select a random character.
	Usage: /randomchar
	"""
	if len(arg) != 0:
		raise ArgumentError('This command has no arguments.')
	if len(client.charcurse) > 0:
		free_id = random.choice(client.charcurse)
	else:
		try:
			free_id = client.area.get_rand_avail_char_id()
		except AreaError:
			raise
	try:
		client.change_character(free_id)
	except ClientError:
		raise
	client.send_ooc('Randomly switched to {}'.format(
		client.char_name))

@mod_only()
def ooc_cmd_charcurse(client, arg):
	"""
	Lock a user into being able to choose only from a list of characters.
	Usage: /charcurse <id> [charids...]
	"""
	if len(arg) == 0:
		raise ArgumentError(
			'You must specify a target (an ID) and at least one character ID. Consult /charids for the character IDs.'
		)
	elif len(arg) == 1:
		raise ArgumentError(
			'You must specific at least one character ID. Consult /charids for the character IDs.'
		)
	args = arg.split()
	try:
		targets = client.server.client_manager.get_targets(
			client, TargetType.ID, int(args[0]), False)
	except:
		raise ArgumentError(
			'You must specify a valid target! Make sure it is a valid ID.')
	if targets:
		for c in targets:
			log_msg = ''
			part_msg = ' [' + str(c.id) + '] to'
			for raw_cid in args[1:]:
				try:
					cid = int(raw_cid)
					c.charcurse.append(cid)
					part_msg += ' ' + str(client.server.char_list[cid]) + ','
					log_msg += ' ' + str(client.server.char_list[cid]) + ','
				except:
					ArgumentError('' + str(raw_cid) +
								  ' does not look like a valid character ID.')
			part_msg = part_msg[:-1]
			part_msg += '.'
			log_msg = log_msg[:-1]
			c.char_select()
			database.log_room('charcurse', client, client.area, target=c, message=log_msg)
			client.send_ooc('Charcursed' + part_msg)
	else:
		client.send_ooc('No targets found.')


@mod_only()
def ooc_cmd_uncharcurse(client, arg):
	"""
	Remove the character choice restrictions from a user.
	Usage: /uncharcurse <id>
	"""
	if len(arg) == 0:
		raise ArgumentError('You must specify a target (an ID).')
	args = arg.split()
	try:
		targets = client.server.client_manager.get_targets(
			client, TargetType.ID, int(args[0]), False)
	except:
		raise ArgumentError(
			'You must specify a valid target! Make sure it is a valid ID.')
	if targets:
		for c in targets:
			if len(c.charcurse) > 0:
				c.charcurse = []
				database.log_room('uncharcurse', client, client.area, target=c)
				client.send_ooc(f'Uncharcursed [{c.id}].')
				c.char_select()
			else:
				client.send_ooc(f'[{c.id}] is not charcursed.')
	else:
		client.send_ooc('No targets found.')


@mod_only()
def ooc_cmd_charids(client, arg):
	"""
	Show character IDs corresponding to each character name.
	Usage: /charids
	"""
	if len(arg) != 0:
		raise ArgumentError("This command doesn't take any arguments")
	msg = 'Here is a list of all available characters on the server:'
	for c in range(0, len(client.server.char_list)):
		msg += '\n[' + str(c) + '] ' + client.server.char_list[c]
	client.send_ooc(msg)


def ooc_cmd_reload(client, arg):
	"""
	Reload a character to its default position and state.
	Usage: /reload
	"""
	if len(arg) != 0:
		raise ArgumentError("This command doesn't take any arguments")
	try:
		client.reload_character()
	except ClientError:
		raise
	client.send_ooc('Character reloaded.')

def ooc_cmd_kickother(client, arg):
	other = False
	targets = client.server.client_manager.get_targets(client, TargetType.IPID, client.ipid, False)
	for target in targets:
		if target != client:
			other = True
			target.disconnect()
	targets = client.server.client_manager.get_targets(client, TargetType.HDID, client.hdid, False)
	for target in targets:
		if target != client:
			other = True
			target.disconnect()
	if not other:
		client.send_ooc('No other instances of clients found.')
		return
	temp = set()
	for c in client.server.client_manager.clients:
		temp.add(c)
	for c in temp:
		if c.ipid == client.ipid and c != client:
			client.server.client_manager.remove_client(c)
		elif c.hdid == client.hdid and c != client:
			client.server.client_manager.remove_client(c)
	client.send_ooc('Kicked other instances of client.')
