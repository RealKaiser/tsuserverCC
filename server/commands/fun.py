from server import database
from server.constants import TargetType
from server.exceptions import ClientError, ArgumentError

from . import mod_only

# List with all OOC commands in this file.
# If you wish to add a new OOC command, insert it here.
# Otherwise, it won't work.

__all__ = [
	'ooc_cmd_disemvowel',
	'ooc_cmd_undisemvowel',
	'ooc_cmd_shake',
	'ooc_cmd_digitalroot',
	'ooc_cmd_knock',
	'ooc_cmd_gimp',
	'ooc_cmd_unshake',
]

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
	Replace every message from a user in IC chat with a message from gimp.yaml.
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
