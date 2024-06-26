from server import database
from server.constants import TargetType
from server.exceptions import ClientError, ArgumentError, AreaError

from . import mod_only

# List with all OOC commands in this file.
# If you wish to add a new OOC command, insert it here.
# Otherwise, it won't work.

__all__ = [
	'ooc_cmd_bg',
	'ooc_cmd_bglock',
	'ooc_cmd_allowiniswap',
	'ooc_cmd_allowblankposting',
	'ooc_cmd_forcenonintpres',
	'ooc_cmd_status',
	'ooc_cmd_area',
	'ooc_cmd_getarea',
	'ooc_cmd_bgslist',
	'ooc_cmd_ga',
	'ooc_cmd_getareas',
	'ooc_cmd_gas',
	'ooc_cmd_lock',
	'ooc_cmd_unlock',
	'ooc_cmd_spectatable',
	'ooc_cmd_invite',
	'ooc_cmd_uninvite',
	'ooc_cmd_uninviteall',
	'ooc_cmd_iclock',
	'ooc_cmd_areakick',
	'ooc_cmd_connect',
	'ooc_cmd_biconnect',
	'ooc_cmd_connectlist',
	'ooc_cmd_disconnect',
	'ooc_cmd_bidisconnect',
	'ooc_cmd_clearconnect',
	'ooc_cmd_hubclearconnect',
	'ooc_cmd_hidecount',
	'ooc_cmd_rename',
	'ooc_cmd_shouts',
	'ooc_cmd_allclients',
	'ooc_cmd_poslock',
	'ooc_cmd_password',
	'ooc_cmd_addarea',
	'ooc_cmd_addareas',
	'ooc_cmd_removearea',
	'ooc_cmd_clearhub',
	'ooc_cmd_savehub',
	'ooc_cmd_loadhub',
	'ooc_cmd_hubstatus',
	'ooc_cmd_gethubs',
	'ooc_cmd_areadesc',
	'ooc_cmd_clearareadesc',
	'ooc_cmd_movetime'
]

def ooc_cmd_movetime(client, arg):
	if len(arg) == 0:
		if client.area.timetomove == 0:
			return client.send_ooc('This area has no time requirement to move to it, add a time in seconds as argument to set one.')
		else:
			return client.send_ooc(f'This area requires {client.area.timetomove} seconds to move to.')
	if client not in client.area.owners:
		if client.area.sub and client not in client.area.hub.owners:
			raise ClientError("You aren't CM or this area or its hub.")
	if client.area.sub or client.area.is_hub:
		if client.area.hub.hubtype != 'default':
			raise AreaError('Cannot change move time in this hub.')
	try:
		amount = int(arg)
	except ValueError:
		raise ArgumentError('Not a valid number of seconds.')
	if amount < 0:
		raise ArgumentError('Cannot use a negative number.')
	if amount > 60:
		raise ArgumentError('Cannot set requirement higher than a minute.')
	if amount == 0:
		if client.area.is_hub:
			hub = client.area
			for sub in hub.subareas:
				sub.timetomove = 0
			client.send_ooc('Movement time requirement for hub cleared')
		elif client.area.sub:
			client.area.timetomove = 0
			client.send_ooc('Movement time requirement for this area cleared')
	else:
		if client.area.is_hub:
			hub = client.area
			for sub in hub.subareas:
				sub.timetomove = amount
			client.send_ooc(f'Movement time requirement for hub set to {arg} seconds.')
		elif client.area.sub:
			client.area.timetomove = amount
			client.send_ooc(f'Movement time requirement for this area set to {arg} seconds.')
	

def ooc_cmd_areadesc(client, arg):
	if len(arg) == 0:
		if client.area.desc == '':
			client.send_ooc('This area has no set description, add an argument to set its description.')
		else:
			client.send_ooc(client.area.desc)
	else:
		if client not in client.area.owners:
			raise ClientError("You aren't a CM of this area.")
		if len(arg) > 255:
			raise ArgumentError('Description is too long, try something shorter.')
		setdesc = '=== Area Description ===\r\n'
		setdesc += arg
		client.area.desc = setdesc
		client.send_ooc('Area description set, it will be shown to each new client to the area.')
		
def ooc_cmd_clearareadesc(client, arg):
	if len(arg) != 0:
		raise ArgumentError('This command has no arguments.')
	if client not in client.area.owners:
		raise ClientError("You aren't a CM of this area.")
	else:
		client.area.desc = ''
		return client.send_ooc('Area description cleared')

def ooc_cmd_poslock(client, arg: str) -> None:
	if len(arg) == 0:
		if len(client.area.poslock) > 0:
			msg = 'This area is poslocked to:'
			pos = ' '.join(str(l) for l in client.area.poslock)
			msg += f' {pos}'
			msg += '.'
			client.send_ooc(msg)
			return
		else:
			raise ArgumentError('This area isn\'t poslocked.')
	elif client not in client.area.owners and not client.is_mod:
		raise ClientError('You must be a CM.')
	if arg == 'clear':
		client.area.poslock.clear()
		client.area.broadcast_ooc('Poslock cleared.')
		client.area.change_cbackground(client.area.background)
	else:
		client.area.poslock.clear()
		args = arg.split()
		args = sorted(set(args),key=args.index)
		for pos in args:
			pos = pos.lower()
			if pos == 'none' or pos == 'clear':
				continue
			client.area.poslock.append(pos)

		pos = ' '.join(str(l) for l in client.area.poslock)
		client.area.broadcast_ooc(f'Locked pos into {pos}.')
		client.area.send_command('SD', '*'.join(client.area.poslock))

def ooc_cmd_allclients(client, arg: str) -> None:
	if not client.is_mod:
		raise ArgumentError('You must be authorized to do that.')
	msg = 'Connected clients:'
	for c in client.server.client_manager.clients:
		msg += f'\n{c.name}'
	client.send_ooc(msg)

def ooc_cmd_shouts(client, arg: str) -> None:
	if client not in client.area.owners and not client.is_mod:
		raise ClientError('You must be a CM.')
	if client.area.shouts_allowed:
		client.area.shouts_allowed = False
		client.area.broadcast_ooc('Shouts have been disallowed in this area.')
	else:
		client.area.shouts_allowed = True
		client.area.broadcast_ooc('Shouts have been allowed in this area.')

def ooc_cmd_hidecount(client, arg: str) -> None:
	if client not in client.area.owners and not client.is_mod:
		raise ClientError('You must be a CM.')
	if len(arg) > 0:
		raise ArgumentError('This command takes no arguments.')
	if client.area.hidden == False:
		client.area.hidden = True
		client.server.area_manager.send_arup_players()
		if client.area.is_hub:
			for sub in client.area.subareas:
				sub.hidden = True
		client.area.broadcast_ooc('The playercount for this area has been hidden.')
	else:
		client.area.hidden = False
		client.server.area_manager.send_arup_players()
		if client.area.is_hub:
			for sub in client.area.subareas:
				sub.hidden = False
			client.area.sub_arup_players()
		client.area.broadcast_ooc('The playercount for this area has been revealed.')
	
def ooc_cmd_savehub(client, arg: str) -> None:
	if not client.area.is_hub:
		raise ClientError('You must be in a hub.')
	if not client in client.area.owners and not client.is_mod:
		raise ClientError('You must be CM to save a hub.')
	if len(arg) > 20:
		raise ArgumentError('That name is too long!')
	if '/' in arg or "\\" in arg or '..' in arg:
		raise ArgumentError('Contains bad characters')
	client.server.hub_manager.savehub(client, arg)
	
def ooc_cmd_loadhub(client, arg: str) -> None:
	if not client.area.is_hub:
		raise ClientError('You must be in a hub.')
	if not client in client.area.owners and not client.is_mod:
		raise ClientError('You must be CM to save a hub.')
	if '/' in arg or "\\" in arg or '..' in arg:
		raise ArgumentError('Contains bad characters')
	client.server.hub_manager.loadhub(client, arg)

def ooc_cmd_addarea(client, arg: str) -> None:
	if not client.area.is_hub and not client.area.sub:
		raise ClientError('You can only create areas in hubs.')
	if not client in client.area.owners and not client.is_mod:
		if client.area.is_hub:
			if not client.area.hubtype == 'arcade' and not client.area.hubtype == 'user' and not client.area.hubtype == 'courtroom':
				raise ClientError('You must be CM to create an area.')
		else:
			if not client.area.hub.hubtype == 'arcade' and not client.area.hub.hubtype == 'user' and not client.area.hubtype == 'courtroom':
				raise ClientError('You must be CM to create an area.')
	if len(arg) > 25:
		raise ArgumentError('That name is too long!')
	for character in arg:
		if not character.isalnum():
			if not character == ':' and not character == '!' and not character == '-' and not character == '?' and not character == ' ':
				raise ArgumentError('Try to exclude special characters while renaming.')
	for a in client.server.area_manager.areas:
		if arg == a.name:
			raise ArgumentError('This name is already taken.')
	if client.area.is_hub:
		for a in client.area.subareas:
			if arg == a.name:
				raise ArgumentError('This name is already taken.')
	else:
		for a in client.area.hub.subareas:
			if arg == a.name:
				raise ArgumentError('This name is already taken.')
	client.server.hub_manager.addsub(client, arg)
	
def ooc_cmd_addareas(client, arg: str) -> None:
	if not client.area.is_hub and not client.area.sub:
		raise ClientError('You can only create areas in hubs.')
	if not client in client.area.owners and not client.is_mod:
		if client.area.is_hub:
			raise ClientError('You must be CM to create areas.')
		else:
			raise ClientError('You must be CM to create areas.')
	try:
		amount = int(arg)
	except ValueError:
		raise ArgumentError('Not a valid number.')
	if amount < 1:
		raise ArgumentError('Must input at least 1 or more.')
	client.server.hub_manager.addmoresubs(client, amount)

def ooc_cmd_removearea(client, arg: str) -> None:
	if client not in client.area.owners and not client.is_mod:
		raise ClientError('You must be CM.')
	if len(arg) > 0:
		raise ArgumentError('This command takes no arguments.')
	if client.area.sub:
		client.server.hub_manager.removesub(client)
	else:
		lobby = client.server.area_manager.default_area()
		destroyed = client.area
		if destroyed == lobby:
			raise ArgumentError('Can\'t destroy lobby!')
		if not client.is_mod and destroyed.is_hub != False:
			raise ArgumentError('Can\'t destroy a hub!')
		destroyedclients = set()
		for c in destroyed.clients:
			if c in destroyed.owners:
				destroyed.owners.remove(c)
			destroyedclients.add(c)
		for c in destroyedclients:
			if c in destroyed.clients:
				c.change_area(lobby)
				c.send_ooc(f'You were moved to {lobby.name} from {destroyed.name} because it was destroyed.')
		client.server.area_manager.areas.remove(client.area)
		area_list = []
		for area in client.server.area_manager.areas:
			area_list.append(area.name)
		client.server.send_all_cmd_pred('FA', *area_list, pred=lambda x: not x.area.is_hub and not x.area.sub)
		client.server.area_manager.send_arup_cms()
		client.server.area_manager.send_arup_players()
		client.server.area_manager.send_arup_lock()
		client.server.area_manager.send_arup_status()

def ooc_cmd_clearhub(client, arg: str) -> None:
	if not client.area.is_hub:
		raise ClientError('Must be in a hub to clear a hub.')
	if client not in client.area.owners and not client.is_mod:
		raise ClientError('You must be CM.')
	if len(arg) > 0:
		raise ArgumentError('This command takes no arguments.')
	client.server.hub_manager.clearhub(client)

def ooc_cmd_rename(client, arg: str) -> None:
	if client not in client.area.owners and not client.is_mod:
		raise ClientError('You must be a CM.')
	if not client.area.is_hub and not client.area.sub and not client.is_mod:
		raise ClientError('Area must be hub or in a hub.')
	if len(arg) == 0:
		if client.area.is_hub:
			client.area.name = f'Hub {client.area.hubid}'
			area_list = []
			lobby = client.server.area_manager.default_area()
			area_list.append(lobby.name)
			area_list.append(client.area.name)
			for a in client.area.subareas:
				area_list.append(a.name)
			client.server.send_all_cmd_pred('FA', *area_list, pred=lambda x: x.area == client.area or x.area in client.area.subareas)
			
			area_list = []
			for area in client.server.area_manager.areas:
				area_list.append(area.name)
			client.server.send_all_cmd_pred('FA', *area_list, pred=lambda x: not x.area.is_hub and not x.area.sub)
			client.server.area_manager.send_arup_cms()
			client.server.area_manager.send_arup_players()
			client.server.area_manager.send_arup_lock()
			client.server.area_manager.send_arup_status()
			client.area.sub_arup_players()
			client.area.sub_arup_cms()
			client.area.sub_arup_status()
			client.area.sub_arup_lock()
			return
		else:
			raise ClientError('Area must be hub or in a hub.')
	if len(arg) > 30:
		raise ArgumentError('That name is too long!')
	# hellish check against special characters
	for character in arg:
		if not character.isalnum():
			if not character == ':' and not character == '!' and not character == '-' and not character == '?' and not character == ' ':
				raise ArgumentError('Try to exclude special characters while renaming.')
	for a in client.server.area_manager.areas:
		if arg == a.name:
			raise ArgumentError('This name is already taken.')
	if client.area.is_hub:
		for a in client.area.subareas:
			if arg == a.name:
				raise ArgumentError('This name is already taken.')
	else:
		for a in client.area.hub.subareas:
			if arg == a.name:
				raise ArgumentError('This name is already taken.')
	if client.area.is_hub:
		if client.area.hubtype == 'default':
			client.area.name = f'Hub {client.area.hubid}: {arg}'
		else:
			client.area.name = f'{arg}'
		area_list = []
		lobby = client.server.area_manager.default_area()
		area_list.append(lobby.name)
		area_list.append(client.area.name)
		for a in client.area.subareas:
			area_list.append(a.name)
		client.server.send_all_cmd_pred('FA', *area_list, pred=lambda x: x.area == client.area or x.area in client.area.subareas)
		
		area_list = []
		for area in client.server.area_manager.areas:
			area_list.append(area.name)
		client.server.send_all_cmd_pred('FA', *area_list, pred=lambda x: not x.area.is_hub and not x.area.sub)
		client.server.area_manager.send_arup_cms()
		client.server.area_manager.send_arup_players()
		client.server.area_manager.send_arup_lock()
		client.server.area_manager.send_arup_status()
		client.area.sub_arup_players()
		client.area.sub_arup_cms()
		client.area.sub_arup_status()
		client.area.sub_arup_lock()
	elif client.area.sub:
		client.area.name = arg
		area_list = []
		lobby = client.server.area_manager.default_area()
		area_list.append(lobby.name)
		area_list.append(client.area.hub.name)
		for a in client.area.hub.subareas:
			area_list.append(a.name)
		client.server.send_all_cmd_pred('FA', *area_list, pred=lambda x: x.area == client.area.hub or x.area in client.area.hub.subareas)
		client.area.hub.sub_arup_players()
		client.area.hub.sub_arup_cms()
		client.area.hub.sub_arup_status()
		client.area.hub.sub_arup_lock()
	else:
		client.area.name = arg
		for area in client.server.area_manager.areas:
			area_list.append(area.name)
		client.area.abbreviation = client.server.area_manager.abbreviate(client.area.name)
		client.server.send_all_cmd_pred('FA', *area_list, pred=lambda x: not x.area.is_hub and not x.area.sub)
		client.server.area_manager.send_arup_cms()
		client.server.area_manager.send_arup_players()
		client.server.area_manager.send_arup_lock()
		client.server.area_manager.send_arup_status()
		client.area.sub_arup_players()
		client.area.sub_arup_cms()
		client.area.sub_arup_status()
		client.area.sub_arup_lock()
	client.send_ooc('Area renamed!')

def ooc_cmd_bg(client, arg: str) -> None:
	"""
	Set the background of a room.
	Usage: /bg <background>
	"""
	if len(arg) == 0:
		client.send_ooc(f'Current background is "{client.area.background}".')
		return
	if not client.is_mod and client.area.bg_lock == True:
		raise AreaError("This area's background is locked")
	try:
		client.area.change_background(arg)
	except AreaError:
		msg = 'custom/'
		msg += arg
		try:
			client.area.change_cbackground(msg)
		except AreaError:
			raise
	client.area.broadcast_ooc(
		f'{client.char_name} changed the background to {arg}.')
	database.log_room('bg', client, client.area, message=arg)

def ooc_cmd_bglock(client, arg: str) -> None:
	"""
	Toggle whether or not non-moderators are allowed to change
	the background of a room.
	Usage: /bglock
	"""
	if client not in client.area.owners and not client.is_mod:
		raise ClientError('You must be a CM.')
	if len(arg) != 0:
		raise ArgumentError('This command has no arguments.')
	# XXX: Okay, what?
	if client.area.bg_lock == True:
		client.area.bg_lock = False
	else:
		client.area.bg_lock = True
	client.area.broadcast_ooc(
		'{} [{}] has set the background lock to {}.'.format(
			client.char_name, client.id, client.area.bg_lock))
	database.log_room('bglock', client, client.area, message=client.area.bg_lock)


@mod_only()
def ooc_cmd_allowiniswap(client, arg: str) -> None:
	"""
	Toggle whether or not users are allowed to swap INI files in character
	folders to allow playing as a character other than the one chosen in
	the character list.
	Usage: /allow_iniswap
	"""
	if client not in client.area.owners and not client.is_mod:
		raise ClientError('You must be a CM.')
	client.area.iniswap_allowed = not client.area.iniswap_allowed
	answer = 'allowed' if client.area.iniswap_allowed else 'forbidden'
	client.send_ooc(f'Iniswap is {answer}.')
	database.log_room('iniswap', client, client.area, message=client.area.iniswap_allowed)


def ooc_cmd_allowblankposting(client, arg: str) -> None:
	"""
	Toggle whether or not in-character messages purely consisting of spaces
	are allowed.
	Usage: /allowblankposting
	"""
	if client not in client.area.owners and not client.is_mod:
		raise ClientError('You must be a CM.')
	client.area.blankposting_allowed = not client.area.blankposting_allowed
	answer = 'allowed' if client.area.blankposting_allowed else 'forbidden'
	client.area.broadcast_ooc(
		'{} [{}] has set blankposting in the area to {}.'.format(
			client.char_name, client.id, answer))
	database.log_room('blankposting', client, client.area, message=client.area.blankposting_allowed)


def ooc_cmd_forcenonintpres(client, arg: str) -> None:
	"""
	Toggle whether or not all pre-animations lack a delay before a
	character begins speaking.
	Usage: /forcenonintpres
	"""
	if client not in client.area.owners and not client.is_mod:
		raise ClientError('You must be a CM.')
	client.area.non_int_pres_only = not client.area.non_int_pres_only
	answer = 'non-interrupting only' if client.area.non_int_pres_only else 'non-interrupting or interrupting as you choose'
	client.area.broadcast_ooc(
		'{} [{}] has set pres in the area to be {}.'.format(
			client.char_name, client.id, answer))
	database.log_room('force_nonint_pres', client, client.area, message=client.area.non_int_pres_only)


def ooc_cmd_status(client, arg: str) -> None:
	"""
	Show or modify the current status of a room.
	Usage: /status <idle|rp|casing|looking-for-players|lfp|recess|gaming>
	"""
	if len(arg) == 0:
		client.send_ooc(f'Current status: {client.area.status}')
	elif 'CM' not in client.area.evidence_mod and not client.is_mod:
		raise ClientError('You can\'t change the status of this area')
	if client.area.is_hub and not client in client.area.owners and not client.is_mod:
		raise ClientError('Must be CM.')
	else:
		try:
			client.area.change_status(arg)
			client.area.broadcast_ooc('{} changed status to {}.'.format(
				client.char_name, client.area.status))
			database.log_room('status', client, client.area, message=arg)
		except AreaError:
			raise
	
def ooc_cmd_hubstatus(client, arg: str) -> None:
	"""
	Changes a hub and all it's subareas to specified status.
	Usage: /hubstatus <idle|rp|casing|looking-for-players|lfp|recess|gaming>
	"""
	if 'CM' not in client.area.evidence_mod:
		raise ClientError('You can\'t change the status of this area')
	if client.area.is_hub and not client in client.area.owners:
		raise ClientError('Must be CM.')
	else:
		try:
			client.area.hub_status(arg)
			client.area.broadcast_ooc('{} changed status to {}.'.format(client.char_name, client.area.status))
			for sub in client.area.subareas:
				sub.broadcast_ooc('{} changed status to {}.'.format(client.char_name, client.area.status))
			database.log_room('hubstatus', client, client.area, message=arg)
		except AreaError:
			raise

def ooc_cmd_area(client, arg: str) -> None:
	"""
	List areas, or go to another area/room.
	Usage: /area [id]
	"""
	args = arg.split()
	if len(args) == 0:
		client.send_area_list()
		return
	if len(args) == 1:
		try:
			area = client.server.area_manager.get_area_by_name(arg, client)
			client.change_area(area)
		except:
			try:
				area = client.server.area_manager.get_area_by_abbreviation(arg)
				client.change_area(area)
			except (AreaError, ClientError):
				raise
		client.send_ooc(f'Area changed to {area.name}')
	if len(args) > 1:
		index = 0
		nameceiling = len(args) - 2
		lastitem = len(args) - 1
		while index < nameceiling:
			if index == 0:
				fullname = args[index]
			fullname += args[index]
			index += 1
		try:
			area = client.server.area_manager.get_area_by_name(arg, client)
		except:
			try:
				area = client.server.area_manager.get_area_by_name(fullname, client)
			except:
				try:
					area = client.server.area_manager.get_area_by_abbreviation(args[0])
				except (AreaError):
					raise
		if area.password != '':
			if area.password == args[lastitem]:
				area.invite_list[client.id] = None
				client.send_ooc('Password accepted.')
		try:
			client.change_area(area)
		except (AreaError, ClientError):
				raise
		client.send_ooc(f'Area changed to {area.name}')

def ooc_cmd_connect(client, arg: str) -> None:
	"""
	Connects areas together. One way.
	"""
	args = arg.split()
	if client not in client.area.owners and not client.is_mod:
		raise ClientError('You must be a CM.')
	if not client.area.sub:
		raise ClientError('Must be in a hub subarea.')
	elif len(args) == 0:
		raise ArgumentError('You must specify at least one area, use /connect <abbreviation>')
	else:
		for area in client.area.hub.subareas:
			if area.abbreviation in args:
				if area in client.area.connections:
					raise ArgumentError(f'Already connected to {area.name}.')
				if area == client.area:
					raise ArgumentError('Can\'t connect an area to itself.')
				if len(client.area.connections) == 0:
					client.area.connections.append(client.server.area_manager.default_area())
					client.area.connections.append(client.area.hub)
				client.area.connections.append(area)
				client.send_ooc('Area connected!')
				client.area.is_restricted = True
				return
	raise ArgumentError('Area not found. Use an area\'s abbreviation')

def ooc_cmd_biconnect(client, arg: str) -> None:
	"""
	Connects areas together. Two-way.
	"""
	args = arg.split()
	if client not in client.area.owners and not client.is_mod:
		raise ClientError('You must be a CM.')
	if not client.area.sub:
		raise ClientError('Must be in a hub subarea.')
	elif len(args) == 0:
		raise ArgumentError('You must specify an area, use /connect <area id>')
	else:
		for area in client.area.hub.subareas:
			if area.abbreviation in args:
				if area in client.area.connections:
					raise ArgumentError(f'Already connected to {area.name}.')
				if client.area in area.connections:
					raise ArgumentError(f'{area.name} is already connected to this area. Use /connect instead if you want to establish a connection from this area.')
				if area == client.area:
					raise ArgumentError('Can\'t connect an area to itself.')
				if len(client.area.connections) == 0:
					client.area.connections.append(client.server.area_manager.default_area())
					client.area.connections.append(client.area.hub)
				if len(area.connections) == 0:
					area.connections.append(client.server.area_manager.default_area())
					area.connections.append(client.area.hub)
				client.area.connections.append(area)
				area.connections.append(client.area)
				client.send_ooc('Area connected!')
				client.area.is_restricted = True
				area.is_restricted = True
				return
	raise ArgumentError('Area not found. Use an area\'s abbreviation')

def ooc_cmd_connectlist(client, arg: str) -> None:
	"""
	Shows what areas the current area is connected to.
	"""
	if len(arg) > 0:
		raise ArgumentError('This command takes no arguments.')
	if len(client.area.connections) == 0:
		raise AreaError('This area has no connections.')
	msg = f'[{client.area.abbreviation}]{client.area.name} is connected to: '
	index = 0
	for connection in client.area.connections:
		if index > 0:
			msg += ', '
		msg += f'[{connection.abbreviation}]{connection.name}'
		index += 1
	msg += '.'
	client.send_ooc(msg)

def ooc_cmd_clearconnect(client, arg: str) -> None:
	"""
	Removes all connections to other areas. One-way.
	"""
	if len(arg) > 0:
		raise ArgumentError('This command takes no arguments.')
	if client not in client.area.owners and not client.is_mod:
		raise ClientError('You must be a CM.')
	client.area.connections.clear()
	client.area.is_restricted = False
	client.area.broadcast_ooc(f'All {client.area.name} connections cleared.')

def ooc_cmd_hubclearconnect(client, arg: str) -> None:
	"""
	Removes all connections to other areas. One-way.
	"""
	if len(arg) > 0:
		raise ArgumentError('This command takes no arguments.')
	if not client.area.is_hub:
		raise ClientError('Must be in a hub.')
	if client not in client.area.owners and not client.is_mod:
		raise ClientError('You must be a CM.')
	for area in client.area.subareas:
		area.connections.clear()
		area.is_restricted = False
	client.area.broadcast_ooc(f'All connections in hub cleared.')

def ooc_cmd_disconnect(client, arg: str) -> None:
	"""
	Removes a one-way connection to an area.
	"""
	args = arg.split()
	if client not in client.area.owners and not client.is_mod:
		raise ClientError('You must be a CM.')
	if not client.area.sub:
		raise ClientError('Must be in a hub subarea.')
	if len(args) == 0:
		raise ArgumentError('You must specify an area, use /disconnect <abbreviation>')
	if len(client.area.connections) < 3:
		for area in client.area.connections:
			if area != area.hub and area != client.server.area_manager.default_area() and area.abbreviation in args:
				client.area.connections.remove(area)
				client.send_ooc('Area disconnected!')
	else:
		raise ArgumentError('No areas to disconnect from, use /clearconnect to unrestrict the area.')

def ooc_cmd_bidisconnect(client, arg: str) -> None:
	"""
	Removes two-way connection between areas.
	"""
	args = arg.split()
	if client not in client.area.owners and not client.is_mod:
		raise ClientError('You must be a CM.')
	if not client.area.sub:
		raise ClientError('Must be in a hub subarea.')
	if len(args) == 0:
		raise ArgumentError('You must specify an area, use /disconnect <abbreviation>')
	if len(client.area.connections) < 3:
		for area in client.area.connections:
			if area != area.hub and area != client.server.area_manager.default_area() and area.abbreviation in args:
				client.area.connections.remove(area)
				if client.area in area.connections:
					area.connections.remove(client.area)
				client.send_ooc('Area disconnected!')

def ooc_cmd_bgslist(client, arg: str) -> None:
	"""
	Sends a list of the backgrounds available over 
	OOC.

	Calls send_server_bgs to create a list off
	the backgrounds.yaml file.

	Sends an OOC message in-client with every 
	background in the server.

	Usage: /bgslist 

	Parameters:

	client = An instance of the class Client
	arg = The name of the OOC Command: bgslist.

	Preconditions: None.

	"""
	bgslist = client.send_server_bgs()
	client.send_ooc('Backgrounds list:\n'+'\n'.join(bgslist))
	
def ooc_cmd_getarea(client, arg: str) -> None:
	"""
	Show information about the current area.
	Usage: /getarea
	"""
	client.send_area_info(client.area, False)
	
def ooc_cmd_ga(client, arg: str) -> None:
	"""
	Show information about the current area.
	Usage: /getarea
	"""
	client.send_area_info(client.area, False)

def ooc_cmd_getareas(client, arg: str) -> None:
	"""
	Show information about all areas.
	Usage: /getareas
	"""
	client.send_area_info(client.area, True)
	
def ooc_cmd_gas(client, arg: str) -> None:
	"""
	Show information about all areas.
	Usage: /getareas
	"""
	client.send_area_info(client.area, True)
	
def ooc_cmd_gethubs(client, arg: str) -> None:
	"""
	Show information about all areas.
	Usage: /getareas
	"""
	client.send_area_info(client.area, True, True)

def ooc_cmd_lock(client, arg: str) -> None:
	"""
	Prevent users from joining the current area.
	Usage: /lock <optional password>
	"""
	if not client.area.locking_allowed and not client.is_mod:
		client.send_ooc('Area locking is disabled in this area.')
	elif client.area.is_locked == client.area.Locked.LOCKED:
		client.send_ooc('Area is already locked.')
	elif client in client.area.owners or client.is_mod:
		if not client.is_mod and client.area.sub:
			if client.area.hub.hubtype == 'courtroom' or client.area.hub.hubtype == 'arcade':
				raise ArgumentError('You may not lock areas in this hub, either use /spectatable or contact a moderator.')
		args = arg.split()
		if len(args) == 0:
			client.area.lock()
		elif len(args) == 1:
			client.area.password = args[0]
			client.area.lock()
			client.send_ooc(f'Area locked with password "{args[0]}".')
		else:
			raise ArgumentError('Too many arguments, use /lock <password> or no arguments.')
	else:
		raise ClientError('Only CM can lock the area.')

def ooc_cmd_password(client, arg: str) -> None:
	if client not in client.area.owners and not client.is_mod:
		raise ClientError('You must be CM')
	if client.area.is_locked == client.area.Locked.FREE:
		raise ClientError('There is no password as the area is unlocked.')
	args = arg.split()
	if len(args) == 0:
		if client.area.password != '':
			client.send_ooc(f'Area password: "{client.area.password}".')
		else:
			raise AreaError('This area does not have a password, set one with /password <password>.')
	elif len(args) == 1:
		client.area.password = args[0]
		client.send_ooc(f'Area password changed to "{args[0]}".')
	else:
		raise ArgumentError('Too many arguments, use /password <password> or no argument.')
		
	
def ooc_cmd_unlock(client, arg: str) -> None:
	"""
	Allow anyone to freely join the current area.
	Usage: /unlock
	"""
	if client.area.is_locked == client.area.Locked.FREE:
		raise ClientError('Area is already unlocked.')
	elif client in client.area.owners or client.is_mod:
		client.area.unlock()
		client.area.password = ''
		client.send_ooc('Area is unlocked.')
	else:
		raise ClientError('Only CM can unlock area.')


def ooc_cmd_spectatable(client, arg: str) -> None:
	"""
	Allow users to join the current area, but only as spectators.
	Usage: /spectatable
	"""
	if not client.area.locking_allowed:
		client.send_ooc('Area locking is disabled in this area.')
	elif client.area.is_locked == client.area.Locked.SPECTATABLE:
		client.send_ooc('Area is already spectatable.')
	elif client in client.area.owners or client.is_mod:
		client.area.spectator()
	else:
		raise ClientError('Only CM can make the area spectatable.')
		

def ooc_cmd_invite(client, arg: str) -> None:
	"""
	Allow a particular user to join a locked or spectator-only area.
	Usage: /invite <id>
	"""
	if not arg:
		raise ClientError('You must specify a target. Use /invite <id>')
	elif client.area.is_locked == client.area.Locked.FREE:
		raise ClientError('Area isn\'t locked.')
	elif client not in client.area.owners and not client.is_mod:
		raise ClientError ('You are not a CM.')
	try:
		c = client.server.client_manager.get_targets(client, TargetType.ID,
													 int(arg), False)[0]
		client.area.invite_list[c.id] = None
		client.send_ooc('{} is invited to your area.'.format(c.char_name))
		c.send_ooc(f'You were invited and given access to {client.area.name}.')
		database.log_room('invite', client, client.area, target=c)
	except:
		raise ClientError('You must specify a target. Use /invite <id>')

def ooc_cmd_uninvite(client, arg: str) -> None:
	"""
	Revoke an invitation for a particular user.
	Usage: /uninvite <id>
	"""
	if client.area.is_locked == client.area.Locked.FREE:
		raise ClientError('Area isn\'t locked.')
	elif not arg:
		raise ClientError('You must specify a target. Use /uninvite <id>')
	elif client not in client.area.owners and not client.is_mod:
		raise ClientError ('You are not a CM.')
	arg = arg.split(' ')
	targets = client.server.client_manager.get_targets(client, TargetType.ID,
														 int(arg[0]), True)
	if targets:
		try:
			for c in targets:
				client.send_ooc(
					"You have removed {} from the whitelist.".format(
						c.char_name))
				c.send_ooc(
					"You were removed from the area whitelist.")
				database.log_room('uninvite', client, client.area, target=c)
				if client.area.is_locked != client.area.Locked.FREE:
					client.area.invite_list.pop(c.id)
		except AreaError:
			raise
		except ClientError:
			raise
	else:
		client.send_ooc("No targets found.")


def ooc_cmd_uninviteall(client, arg: str) -> None:
	"""
	Revoke invitations for all new users.
	Usage: /uninviteall
	"""
	if len(arg) > 0:
		raise ArgumentError('This command takes no arguments.')
	if client.area.is_locked == client.area.Locked.FREE:
		raise ClientError('Area isn\'t locked.')
	if client not in client.area.owners and not client.is_mod:
		raise ClientError('You are not a CM.')
	else:
		client.area.invite_list = {}
		for c in client.area.owners:
			client.area.invite_list[c.id] = None
		if client.area.is_locked == client.area.Locked.LOCKED:
			for c in client.area.clients:
				client.area.invite_list[c.id] = None
			client.send_ooc("Invitelist cleared.")
		else:
			client.area.broadcast_ooc("IClock enabled.")

def ooc_cmd_iclock(client, arg: str) -> None:
	if client not in client.area.owners and not client.is_mod:
		raise ClientError('You are not a CM.')
	if len(arg) > 0:
		raise ArgumentError('This takes no arguments.')
	if (client.area.is_locked != client.area.Locked.FREE 
		and client.area.is_locked != client.area.Locked.LOCKED):
		return ooc_cmd_uninviteall(client, arg)
	else:
		if client.area.is_locked != client.area.Locked.LOCKED:
			client.area.spectator()
			client.area.invite_list = {}
		else:
			client.area.invite_list = {}
		for c in client.area.owners:
			client.area.invite_list[c.id] = None
		client.area.broadcast_ooc("IClock enabled.")

def ooc_cmd_areakick(client, arg: str) -> None:
	"""
	Remove a user from the current area and move them to another area.
	Usage: /area_kick <id> [destination]
	"""
	if client not in client.area.owners and not client.is_mod:
		raise ClientError('You must be a CM.')
	elif (
		client.area.is_locked == 
		client.area.Locked.FREE 
		and not client.is_mod
		):
		raise ClientError('Area isn\'t locked.')
	elif not arg:
		raise ClientError(
			('You must specify a target. Use /areakick <id> [destination #]')
			)
	elif arg[0] == '*':
		targets = (
			[c for c in client.area.clients 
			if c != client and c != client.area.owners]
			)
	else:
		targets = None
		arg = arg.split()
		if not client.is_mod and len(arg) > 1:
			raise ClientError('You must be a mod to kick people to a specific area.')
	if targets is None:
		try:
			targets = client.server.client_manager.get_targets\
				(client, TargetType.ID, int(arg[0]), False)
			for c in targets:
				if len(arg) == 1:
					area = client.server.area_manager.get_area_by_id(int(0))
					output = 0
				else:
					try:
						area = client.server.area_manager.get_area_by_id(
							int(arg[1]))
						output = arg[1]
					except AreaError:
						raise
				client.send_ooc(
					"Attempting to kick {} to area {}.".format(
						c.char_name, output))
				if c.area.id != client.area.id and not client.is_mod:
					client.send_ooc(f'{c.char_name} is not in this area.')
					return
				c.change_area(area)
				c.send_ooc(
					f"You were kicked from the area to area {output}.")
				database.log_room\
					('area_kick', client, client.area, target=c, message=output)
				if client.area.is_locked != client.area.Locked.FREE:
					client.area.invite_list.pop(c.id)
		except AreaError:
			raise
		except ClientError:
			raise
	elif targets:
		try:
			for c in targets:
				if len(arg) == 1:
					area = client.server.area_manager.get_area_by_id(int(0))
					output = 0
				else:
					try:
						area = client.server.area_manager.get_area_by_id(
							int(arg[1]))
						output = arg[1]
					except AreaError:
						raise
				client.send_ooc(
					"Attempting to kick {} to area {}.".format(c.char_name, output))
				c.change_area(area)
				c.send_ooc(
					f"You were kicked from the area to area {output}.")
				database.log_room\
					('area_kick', client, client.area, target=c, message=output)
				if client.area.is_locked != client.area.Locked.FREE:
					client.area.invite_list.pop(c.id)
		except AreaError:
			raise
		except ClientError:
			raise
	else:
		client.send_ooc("No targets found.")