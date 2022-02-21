from server import database
from server.constants import TargetType
from server.exceptions import ClientError, ArgumentError, AreaError

from . import mod_only

# List with all OOC commands in this file.
# If you wish to add a new OOC command, insert it here.
# Otherwise, it won't work.

__all__ = [
	'ooc_cmd_a',
	'ooc_cmd_s',
	'ooc_cmd_g',
	'ooc_cmd_gm',
	'ooc_cmd_m',
	'ooc_cmd_lm',
	'ooc_cmd_h',
	'ooc_cmd_announce',
	'ooc_cmd_toggleglobal',
	'ooc_cmd_need',
	'ooc_cmd_toggleadverts',
	'ooc_cmd_pm',
	'ooc_cmd_mutepm',
	'ooc_cmd_call',
	'ooc_cmd_acceptcall',
	'ooc_cmd_endcall',
	'ooc_cmd_holdcall',
	'ooc_cmd_listenall'
]

def ooc_cmd_listenall(client, arg):
	if len(arg) > 0:
		raise ArgumentError('This doesn\'t take arguments.')
	if client.listen:
		client.listen = False
		client.send_ooc('You will no longer receive messages from RCM\'d areas.')
	else:
		client.listen = True
		client.send_ooc('You will now receive messages from RCM\'d areas.')

def ooc_cmd_call(client, arg):
	if len(arg) == 0:
		if len(client.calling) > 0 and client.incall:
			msg = 'You are calling with:'
			for c in client.calling:
				msg += f'\n[{c.id}] {c.name}'
			#msg += '\nUse /call to allow users to see your messages.'
			return client.send_ooc(msg)
		else:
			raise ArgumentError('Requires arguments. Try /call <id>.')
	if len(client.calling) > 0:
		raise ArgumentError('You are already calling or attempting a call, end it with /endcall before attempting again.')
	try:
		targets = client.server.client_manager.get_targets(client, TargetType.ID, int(arg), False)
	except:
		raise ArgumentError('That doesn\'t seem like a valid ID.')
	caller = targets[0]
	if len(caller.calling) > 0:
		raise ArgumentError('This person is already calling someone.')
	caller.calling.append(client)
	caller.send_ooc(f'[{client.id}] {client.char_name}: {client.name} is calling you, use /acceptcall to take call or /endcall to reject.')
	client.send_ooc(f'Calling [{caller.id}] {caller.char_name}.')
	
def ooc_cmd_acceptcall(client, arg):
	if len(arg) > 0:
		raise ArgumentError('This command does not take arguments.')
	if len(client.calling) == 0:
		raise ArgumentError('No call to accept.')
	if client.incall:
		raise ArgumentError('You are already in a call.')
	caller = client.calling[0]
	if caller.incall:
		client.calling.clear()
		raise ArgumentError('They are already in a call.')
	caller.calling.append(client)
	client.incall = True
	caller.incall = True
	callarea = client.server.area_manager.Area(caller.ipid, client.server, name=f'{caller.name}\'s Call', background='', bg_lock=False, evidence_mod='CM', locking_allowed=True, iniswap_allowed=True, showname_changes_allowed=True, shouts_allowed=True, jukebox=False, abbreviation=f'C{caller.ipid}', non_int_pres_only=False)
	client.call = callarea
	caller.call = callarea
	callarea.owners.append(client)
	callarea.owners.append(caller)
	
	client.send_ooc(f'Started call with {caller.name}. Use /endcall to end.')
	caller.send_ooc(f'Started call with {client.name}. Use /endcall to end.')
	
def ooc_cmd_endcall(client, arg):
	if len(arg) > 0:
		raise ArgumentError('This command does not take arguments.')
	if len(client.calling) == 0:
		raise ArgumentError('No call to end.') 
	caller = client.calling[0]
	client.calling.clear()
	client.incall = False
	if len(caller.calling) > 0:
		if caller.calling[0] == client:
			caller.incall = False
			caller.calling.clear()
			if client.call != None:
				callarea = client.call
				callarea.owners.clear()
				client.call = None
				caller.call = None
	
	
	client.send_ooc(f'Call with {caller.name} was ended/rejected.')
	caller.send_ooc(f'Call with {client.name} was ended/rejected.')
	
def ooc_cmd_holdcall(client, arg):
	if len(arg) > 0:
		raise ArgumentError('This command does not take arguments.')
	if client.call == None:
		raise ArgumentError('No call to hold.')
	if client.incall:
		client.incall = False
		client.send_ooc('Call put on hold, you are now speaking outside of call.')
	else:
		client.incall = True
		client.send_ooc('Call resumed, you are now speaking in the call.')


def ooc_cmd_a(client, arg):
	"""
	Send a message to an area that you are a CM in.
	Usage: /a <area> <message>
	"""
	if len(arg) == 0:
		raise ArgumentError('You must specify an area.')
	arg = arg.split(' ')

	try:
		area = client.server.area_manager.get_area_by_abbreviation(arg[0])
	except AreaError:
		raise

	message_areas_cm(client, [area], ' '.join(arg[1:]))


def ooc_cmd_s(client, arg):
	"""
	Send a message to all areas that you are a CM in.
	Usage: /s <message>
	"""
	areas = []
	for a in client.server.area_manager.areas:
		if client in a.owners:
			areas.append(a)
		if a.is_hub:
			for sub in a.subareas:
				if client in sub.owners:
					areas.append(sub)
	if not areas:
		client.send_ooc('You aren\'t a CM in any area!')
		return
	message_areas_cm(client, areas, arg)


def message_areas_cm(client, areas, message):
	for a in areas:
		if not client in a.owners:
			client.send_ooc(f'You are not a CM in {a.name}!')
			return
		a.send_command('CT', client.name, message)
		a.send_owner_command('CT', client.name, message)
		database.log_room('chat.cm', client, a, message=message)


def ooc_cmd_g(client, arg):
	"""
	Broadcast a message to all areas.
	Usage: /g <message>
	"""
	if client.muted_global:
		raise ClientError('Global chat toggled off.')
	if len(arg) == 0:
		raise ArgumentError("You can't send an empty message.")
	client.server.broadcast_global(client, arg)
	database.log_room('chat.global', client, client.area, message=arg)

def ooc_cmd_h(client, arg):
	if len(arg) == 0:
		raise ArgumentError('You can\'t send an empty message.')
	if not client.area.is_hub and not client.area.sub:
		raise ClientError('Must be in a hub.')
	client.area.broadcast_hub(client, arg)

@mod_only()
def ooc_cmd_gm(client, arg):
	"""
	Broadcast a message to all areas, speaking officially.
	Usage: /gm <message>
	"""
	if client.muted_global:
		raise ClientError('You have the global chat muted.')
	if len(arg) == 0:
		raise ArgumentError("Can't send an empty message.")
	client.server.broadcast_global(client, arg, True)
	database.log_room('chat.global-mod', client, client.area, message=arg)


@mod_only()
def ooc_cmd_m(client, arg):
	"""
	Send a message to all online moderators.
	Usage: /m <message>
	"""
	if len(arg) == 0:
		raise ArgumentError("You can't send an empty message.")
	client.server.send_modchat(client, arg)
	database.log_room('chat.mod', client, client.area, message=arg)


@mod_only()
def ooc_cmd_lm(client, arg):
	"""
	Send a message to all moderators in the current area.
	Usage: /lm <message>
	"""
	if len(arg) == 0:
		raise ArgumentError("Can't send an empty message.")
	client.area.send_command(
		'CT', '{}[MOD][{}]'.format(client.server.config['hostname'],
								   client.char_name), arg)
	database.log_room('chat.local-mod', client, client.area, message=arg)


@mod_only()
def ooc_cmd_announce(client, arg):
	"""
	Make a server-wide announcement.
	Usage: /announce <message>
	"""
	if len(arg) == 0:
		raise ArgumentError("Can't send an empty message.")
	client.server.send_all_cmd_pred(
		'CT', '{}'.format(client.server.config['hostname']),
		f'=== Announcement ===\r\n{arg}\r\n==================', '1')
	database.log_room('chat.announce', client, client.area, message=arg)


def ooc_cmd_toggleglobal(client, arg):
	"""
	Mute global chat.
	Usage: /toggleglobal
	"""
	if len(arg) != 0:
		raise ArgumentError("This command doesn't take any arguments")
	client.muted_global = not client.muted_global
	glob_stat = 'on'
	if client.muted_global:
		glob_stat = 'off'
	client.send_ooc(f'Global chat turned {glob_stat}.')


def ooc_cmd_need(client, arg):
	"""
	Broadcast a need for a specific role in a case.
	Usage: /need <message>
	"""
	if client.muted_adverts:
		raise ClientError('You have advertisements muted.')
	if len(arg) == 0:
		raise ArgumentError("You must specify what you need.")
	client.server.broadcast_need(client, arg)
	database.log_room('chat.announce.need', client, client.area, message=arg)


def ooc_cmd_toggleadverts(client, arg):
	"""
	Mute advertisements.
	Usage: /toggleadverts
	"""
	if len(arg) != 0:
		raise ArgumentError("This command doesn't take any arguments")
	client.muted_adverts = not client.muted_adverts
	adv_stat = 'on'
	if client.muted_adverts:
		adv_stat = 'off'
	client.send_ooc(f'Advertisements turned {adv_stat}.')


def ooc_cmd_pm(client, arg):
	"""
	Send a private message to another online user. These messages are not
	logged by the server owner.
	Usage: /pm <id|ooc-name|char-name> <message>
	"""
	args = arg.split()
	key = ''
	msg = None
	if len(args) < 2:
		raise ArgumentError('Not enough arguments. use /pm <target> <message>. Target should be ID, OOC-name or char-name. Use /getarea for getting info like "[ID] char-name".')
	try:
		targets = client.server.client_manager.get_targets(client, TargetType.ID, int(args[0]), False)
		key = TargetType.ID
	except:
		try:
			targets = client.server.client_manager.get_targets(client, TargetType.OOC_NAME, args[0], True)
			key = TargetType.OOC_NAME
		except:
			raise ArgumentError('No targets found.')
	try:
		if key == TargetType.ID:
			msg = ' '.join(args[1:])
		else:
			if key == TargetType.CHAR_NAME:
				msg = arg[len(targets[0].char_name) + 1:]
			if key == TargetType.OOC_NAME:
				msg = arg[len(targets[0].name) + 1:]
	except:
		raise ArgumentError(
			'Not enough arguments. Use /pm <target> <message>.')
	c = targets[0]
	if c.pm_mute:
		raise ClientError('This user muted all pm conversation')
	else:
		if c.is_mod:
			c.send_ooc(
				'PM from {} (ID: {}, IPID: {}) in {} ({}): {}'.format(client.name, client.id, client.ipid, client.area.name,client.char_name, msg))
		else:
			c.send_ooc('PM from {} (ID: {}) in {} ({}): {}'.format(client.name, client.id, client.area.name, client.char_name, msg))
		client.send_ooc('PM sent to {}. Message: {}'.format(args[0], msg))

def ooc_cmd_mutepm(client, arg):
	"""
	Mute private messages.
	Usage: /mutepm
	"""
	if len(arg) != 0:
		raise ArgumentError("This command doesn't take any arguments")
	client.pm_mute = not client.pm_mute
	client.send_ooc('You stopped receiving PMs' if client.
							 pm_mute else 'You are now receiving PMs')
