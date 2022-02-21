from server import database
from server.constants import TargetType
from server.exceptions import ClientError, ArgumentError

from . import mod_only

__all__ = [
	'ooc_cmd_disemvowel',
	'ooc_cmd_undisemvowel',
	'ooc_cmd_shake',
	'ooc_cmd_notepad',
	'ooc_cmd_partynote',
	'ooc_cmd_clearpartynote',
	'ooc_cmd_digitalroot',
	'ooc_cmd_knock',
	'ooc_cmd_tutturu',
	'ooc_cmd_gimp',
	'ooc_cmd_unshake'
]

def ooc_cmd_tutturu(client, arg):
	if not client.is_mod:
		raise ArgumentError('No fun allowed.')
	client.area.send_command('MS', 1, '-', 'Mayuri', '/hat/happy', 'Tutturu♪',
									  'wit', 'tutturu', 1, 398, 0,
									  0, 0,
									  0, 1, 0, 'Mayuri', -1,
									  '', '', 10,
									  0, 0, 0)
	client.area.broadcast_ooc(f'Tutturu♪ {client.name}!')

def ooc_cmd_knock(client, arg):
	args = arg.split()
	try:
		area = client.server.area_manager.get_area_by_abbreviation(args[0])
	except ValueError:
		raise ArgumentError('Argument must be an area\'s abbreviation.')
	client.send_ooc(f'You knocked on {area.name}\'s door.')
	area.broadcast_ooc(f'{client.name} knocked on the area\'s door!')

def ooc_cmd_digitalroot(client, arg):
	num = int(arg)
	if num < 1:
		raise ArgumentError('That does not seem to be a valid number.')
	num = (num - 1) % 9 + 1
	client.send_ooc(f'The digital root of {arg} is {num}.')

@mod_only()
def ooc_cmd_disemvowel(client, arg):
	"""
	Remove all vowels from a user's IC chat.
	Usage: /disemvowel <id>
	"""
	if len(arg) == 0:
		raise ArgumentError('You must specify a target.')
	try:
		targets = client.server.client_manager.get_targets(
			client, TargetType.ID, int(arg), False)
	except:
		raise ArgumentError('You must specify a target. Use /disemvowel <id>.')
	if targets:
		for c in targets:
			database.log_room('disemvowel', client, client.area, target=c)
			c.disemvowel = True
		client.send_ooc(f'Disemvowelled {len(targets)} existing client(s).')
	else:
		client.send_ooc('No targets found.')

@mod_only()
def ooc_cmd_gimp(client, arg):
	"""
	Remove all vowels from a user's IC chat.
	Usage: /disemvowel <id>
	"""
	if len(arg) == 0:
		raise ArgumentError('You must specify a target.')
	try:
		targets = client.server.client_manager.get_targets(
			client, TargetType.ID, int(arg), False)
	except:
		raise ArgumentError('You must specify a target. Use /gimp <id>.')
	if targets:
		for c in targets:
			if c.gimp:
				database.log_room('ungimp', client, client.area, target=c)
				c.gimp = False
				client.send_ooc(f'Ungimped {c.char_name}.')
			else:
				database.log_room('gimp', client, client.area, target=c)
				c.gimp = True
				client.send_ooc(f'Gimped {c.char_name}.')
	else:
		client.send_ooc('No targets found.')

def ooc_cmd_notepad(client, arg):
	"""
	Adds to the client's notes.
	"""
	notepad = 'Notepad:'
	if len(arg) > 256:
		raise ArgumentError('That note is too large to add to your notes!')
	elif len(arg) == 0:
		if client.notepad == '':
			notepad += '\nNothing is on the notepad.'
			client.send_ooc(notepad)
		else:
			notepad += client.notepad
			client.send_ooc(notepad)
	else:
		if len(client.notepad) > 2000:
			raise ArgumentError('Your notes exceed the maximum of 2000 characters!')
		else:
			client.notepad += f'\n{arg}'
			client.send_ooc('Note added.')

def ooc_cmd_partynote(client, arg):
	"""
	Adds to the client's notes.
	"""
	notepad = 'Party Notepad:'
	if not client.in_party:
		raise ClientError('You aren\'t in a party.')
	if len(arg) > 256:
		raise ArgumentError('That note is too large to add to your notes!')
	elif len(arg) == 0:
		if client.party.notepad == '':
			notepad += '\nNothing is on the notepad.'
			client.send_ooc(notepad)
		else:
			notepad += client.party.notepad
			client.send_ooc(notepad)
	else:
		if len(client.party.notepad) > 4000:
			raise ArgumentError('Your notes exceed the maximum of 4000 characters!')
		else:
			client.party.notepad += f'\n{arg}'
			for user in client.party.users:
				user.send_ooc(f'{client.name} added a note to the party notepad.')

def ooc_cmd_clearpartynote(client, arg):
	"""
	Clears the client's notes.
	"""
	if not client.in_party:
		raise ClientError('You aren\'t in a party.')
	if client.party.leader != client:
		raise ClientError('You aren\'t the Party Leader.')
	if len(arg) > 0:
		raise ArgumentError('This command takes no arguments.')
	else:
		client.party.notepad = ''
		for user in client.party.users:
			user.send_ooc(f'Party notepad was cleared.')

def ooc_cmd_clearnotepad(client, arg):
	"""
	Clears the client's notes.
	"""
	if len(arg) > 0:
		raise ArgumentError('This command takes no arguments.')
	else:
		client.notepad = ''
		client.send_ooc('Notes cleared.')

@mod_only()
def ooc_cmd_undisemvowel(client, arg):
	"""
	Give back the freedom of vowels to a user.
	Usage: /undisemvowel <id>
	"""
	if len(arg) == 0:
		raise ArgumentError('You must specify a target.')
	try:
		targets = client.server.client_manager.get_targets(
			client, TargetType.ID, int(arg), False)
	except:
		raise ArgumentError(
			'You must specify a target. Use /undisemvowel <id>.')
	if targets:
		for c in targets:
			database.log_room('undisemvowel', client, client.area, target=c)
			c.disemvowel = False
		client.send_ooc(f'Undisemvowelled {len(targets)} existing client(s).')
	else:
		client.send_ooc('No targets found.')


@mod_only()
def ooc_cmd_shake(client, arg):
	"""
	Scramble the words in a user's IC chat.
	Usage: /shake <id>
	"""
	if len(arg) == 0:
		raise ArgumentError('You must specify a target.')
	try:
		targets = client.server.client_manager.get_targets(
			client, TargetType.ID, int(arg), False)
	except:
		raise ArgumentError('You must specify a target. Use /shake <id>.')
	if targets:
		for c in targets:
			database.log_room('shake', client, client.area, target=c)
			c.shaken = True
		client.send_ooc(f'Shook {len(targets)} existing client(s).')
	else:
		client.send_ooc('No targets found.')


@mod_only()
def ooc_cmd_unshake(client, arg):
	"""
	Give back the freedom of coherent grammar to a user.
	Usage: /unshake <id>
	"""
	if len(arg) == 0:
		raise ArgumentError('You must specify a target.')
	try:
		targets = client.server.client_manager.get_targets(
			client, TargetType.ID, int(arg), False)
	except:
		raise ArgumentError('You must specify a target. Use /unshake <id>.')
	if targets:
		for c in targets:
			database.log_room('unshake', client, client.area, target=c)
			c.shaken = False
		client.send_ooc(f'Unshook {len(targets)} existing client(s).')
	else:
		client.send_ooc('No targets found.')
