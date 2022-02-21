import shlex
import os
import arrow
import pytimeparse
import yaml

from heapq import heappop, heappush
from server import database
from server.webhooks import Webhooks
from server.constants import TargetType
from server.exceptions import ClientError, ServerError, ArgumentError

from . import mod_only

# List with all OOC commands in this file.
# If you wish to add a new OOC command, insert it here.
# Otherwise, it won't work.

__all__ = [
	'ooc_cmd_motd',
	'ooc_cmd_help',
	'ooc_cmd_kick',
	'ooc_cmd_ban',
	'ooc_cmd_banhdid',
	'ooc_cmd_unban',
	'ooc_cmd_warn',
	'ooc_cmd_unwarn',
	'ooc_cmd_mute',
	'ooc_cmd_unmute',
	'ooc_cmd_login',
	'ooc_cmd_refresh',
	'ooc_cmd_online',
	'ooc_cmd_mods',
	'ooc_cmd_unmod',
	'ooc_cmd_oocmute',
	'ooc_cmd_oocunmute',
	'ooc_cmd_bans',
	'ooc_cmd_warninfo',
	'ooc_cmd_warns',
	'ooc_cmd_warnsby',
	'ooc_cmd_permit',
	'ooc_cmd_baninfo',
	'ooc_cmd_setserverpoll',
	'ooc_cmd_serverpoll',
	'ooc_cmd_clearserverpoll',
	'ooc_cmd_allowmusic',
	'ooc_cmd_ghost',
	'ooc_cmd_addmod',
	'ooc_cmd_removemod',
	'ooc_cmd_spy',
	'ooc_cmd_geoiprefresh',
	'ooc_cmd_about'
]

def ooc_cmd_geoiprefresh(client, arg):
	if not client.is_admin:
		raise ArgumentError('You must be authorized to do that.')
	client.server.load_ipranges()

"""
Command: /spy
Usage: Spy on an area (act as if you were its CM),
see IC and OOC messages in these rooms.
Arguments: None, 'here', 'clear', area abbreviations
Specifics: Leans on 'spying' list in client_manager, 'spies' list and
send_owner_command in area_manager. 'send_owner_command' is called
as part of both the IC and OOC message handlers in aoprotocol.py.
"""
def ooc_cmd_spy(client, arg: str) -> None:
	# Check if the user's a mod.
	if not client.is_mod:
		raise ArgumentError('You must be authorized to do that.')
	# No arguments (just /spy being used), tell me the users I'm
	# spying on.
	if len(arg) == 0:
		msg = 'Spying on:'
		for a in client.spying:
			msg += f'\n[{a.abbreviation}]'
		return client.send_ooc(msg)
	# 'here' as argument, add me as a spy to the area I'm in.
	elif arg == 'here':
		if client not in client.area.spies:
			client.area.spies.add(client)
			client.spying.append(client.area)
		return client.send_ooc('You are now spying on this area.')
	# 'clear' as argument, clear out my spying list.
	elif arg == 'clear':
		spyl = []
		for a in client.spying:
			spyl.append(a)
		for b in spyl:
			b.spies.remove(client)
			client.spying.remove(b)
		return client.send_ooc('All spying cleared.')
	# Entered area name abbreviations as arguments.
	else:
		try:
			# Try adding them to 'spyhere'.
			spyhere = client.server.area_manager.get_area_by_abbreviation(arg)
		except:
			raise ArgumentError('Area not recognized.')
		# Add me as a spy in the spyhere list.
		# Add the spyhere list entries to my spying entry.

		# 'spies' is in area_manager as part of 'send_owner_command'
		spyhere.spies.add(client)

		# 'spying' is in client_manager as a variable intializer.
		client.spying.append(spyhere)
		return client.send_ooc(f'You are now spying in {spyhere.name}.')

def ooc_cmd_allowmusic(client, arg):
	if client not in client.area.owners and not client.is_mod:
		raise ClientError('You are not a CM!')
	if client.area.allowmusic:
		client.area.allowmusic = False
		client.area.broadcast_ooc('Music changes have been disallowed in this area!')
	else:
		client.area.allowmusic = True
		client.area.broadcast_ooc('Music changes have been allowed in this area.')

def ooc_cmd_setserverpoll(client, arg):
	if not client.is_mod:
		raise ClientError('You are not authorized.')
	client.server.poll = f'=== Server Poll ===\n{arg}\n===================\nVote "yay" or "nay" with /serverpoll.'
	client.server.pollyay = []
	client.server.pollnay = []
	for c in client.server.client_manager.clients:
		c.send_ooc('A new server poll has been set. Check /serverpoll.')

def ooc_cmd_serverpoll(client, arg):
	poll = client.server.poll
	yay = client.server.pollyay
	nay = client.server.pollnay
	if poll == '':
		raise ClientError('There is currently no server poll running.')
	if len(yay) == 0:
		if len(nay) != 0:
			poll += f'\n===================\nThere are currently no yays and {len(nay)} nays.\nThe nays have a majority of {len(nay)} vote(s).'
	elif len(nay) == 0:
		if len(yay) != 0:
			poll += f'\n===================\nThere are currently {len(yay)} yays and no nays.\nThe yays have a majority of {len(yay)} vote(s).'
	else:
		if len(nay) > len(yay):
			majority = len(nay) - len(yay)
			poll += f'\n===================\nThere are currently {len(yay)} yays and {len(nay)} nays.\nThe nays have a majority of {majority} vote(s).'
		if len(nay) < len(yay):
			majority = len(yay) - len(nay)
			poll += f'\n===================\nThere are currently {len(yay)} yays and {len(nay)} nays.\nThe yays have a majority of {majority} vote(s).'
		if len(nay) == len(yay):
			poll += f'\n===================\nThere are currently {len(yay)} yays and {len(nay)} nays.\nThe yays and the nays are tied.'
	hdid = client.hdid
	ipid = client.ipid
	if len(arg) == 0:
		client.send_ooc(poll)
	elif arg == 'yay':
		if hdid in yay:
			raise ClientError('You have already voted yay on this poll.')
		elif hdid in nay:
			yay.append(hdid)
			nay.remove(hdid)
			client.send_ooc('You switched your vote from nay to yay.')
		else:
			yay.append(hdid)
			client.send_ooc('You voted yay on the server poll.')
	elif arg == 'nay':
		if hdid in nay:
			raise ClientError('You have already voted nay on this poll.')
		elif hdid in yay:
			nay.append(hdid)
			yay.remove(hdid)
			client.send_ooc('You switched your vote from yay to nay.')
		else:
			nay.append(hdid)
			client.send_ooc('You voted nay on the server poll.')
	else:
		raise ArgumentError\
			('Vote either "yay" or"nay". Check the server poll by using no argument.')

def ooc_cmd_clearserverpoll(client, arg):
	if not client.is_mod:
		raise ClientError('You are not authorized.')
	client.server.poll = ''
	client.server.pollyay = []
	client.server.pollnay = []
	for a in client.server.area_manager.areas:
		for c in a.clients:
			c.send_ooc('The server poll was cleared.')

def ooc_cmd_ghost(client, arg):
	if not client.is_mod:
		raise ClientError('You are not authorized.')
	elif client.ghost:
		client.ghost = False
		client.send_ooc('You are no longer a ghost.')
	else:
		client.ghost = True
		client.send_ooc('You are now a ghost.')

def ooc_cmd_permit(client, arg: str) -> None: 
	if not client.is_mod:
		raise ClientError('You are not authorized.')
	else:
		if len(arg) > 0:
			arg = arg.split(' ')
		for id in arg:
			try:
				id = int(id)
				c = client.server.client_manager.get_targets\
					(client, TargetType.ID, id, False)[0]
			except:
				client.send_ooc(f'{id} does not look like a valid ID.')
			if len(client.hdid) != 32:
				raise ArgumentError('That does not seem to be a webAO client.')
			permfile = 'config/webaoperms.yaml'
			new = not os.path.exists(permfile)
			if not new:
				with open(permfile, 'r') as chars:
					perms = yaml.safe_load(chars)
			else:
				perms = []
			if c.ipid in perms:
				perms.remove(c.ipid)
				c.permission = False
				client.send_ooc('Permission removed.')
			else:
				perms.append(c.ipid)
				c.permission = True
				client.send_ooc('Permission added.')
			if not new:
				os.remove(permfile)
			with open(permfile, 'w', encoding='utf-8') as dump:
				yaml.dump(perms, dump)
			client.server.webperms = perms

def ooc_cmd_addmod(client, arg: str) -> None: 
	"""
	Registers target as a moderator, allowing them to login.
	"""
	args = arg.split(' ')
	if not client.is_admin:
		raise ClientError('You are not authorized.')
	if len(arg) == 0:
		raise ArgumentError('This command requires arguments.')
	if len(args) < 2:
		raise ArgumentError\
			('This command requires ID and a set name as arguments.')
	try:
		id = int(args[0])
		c = client.server.client_manager.get_targets\
			(client, TargetType.ID, id, False)[0]
		modfile = 'config/moderation.yaml'
	except:
		client.send_ooc(f'{id} does not look like a valid ID.')
	new = not os.path.exists(modfile)
	if not new:
		with open(modfile, 'r') as chars:
			mods = yaml.safe_load(chars)
	else:
		mods = []
	status = 'mod'
	if len(args) > 2:
		if args[2].lower() == 'admin':
			status = 'admin'
	mods.append({'name': args[1], 'status': status, 'ipid': c.ipid})
	if not new:
		os.remove(modfile)
	with open(modfile, 'w', encoding='utf-8') as dump:
		yaml.dump(mods, dump)
	
			
def ooc_cmd_removemod(client, arg: str) -> None:
	if not client.is_admin:
		raise ClientError('You are not authorized.')
	if len(arg) == 0:
		raise ArgumentError('This command requires arguments.')
	modfile = 'config/moderation.yaml'
	new = not os.path.exists(modfile)
	rem = None
	if not new:
		with open(modfile, 'r') as chars:
			mods = yaml.safe_load(chars)
		for item in mods:
			if item['name'].lower() == arg.lower():
				rem = item
			elif item['ipid'].lower() == arg.lower():
				rem = item
		if rem != None:
			mods.remove(rem)
			os.remove(modfile)
			with open(modfile, 'w', encoding='utf-8') as dump:
				yaml.dump(mods, dump)
		else:
			raise ArgumentError('No mod found by that name.')
	else:
		raise ArgumentError('There is no moderation file!')

def ooc_cmd_motd(client, arg):
	"""
	Show the message of the day.
	Usage: /motd
	"""
	if len(arg) != 0:
		raise ArgumentError("This command doesn't take any arguments")
	client.send_motd()


def ooc_cmd_help(client, arg):
	"""
	Show help for a command, or show general help.
	Usage: /help
	"""
	if len(arg) != 0:
		raise ArgumentError('This command has no arguments.')
	help_url = 'https://github.com/RealKaiser/tsuserverCC'
	help_msg = f'The commands available on this server can be found here: {help_url}'
	client.send_ooc(help_msg)

def ooc_cmd_about(client, arg):
	"""
	Shows information about the latest version
	of the server's content and its maintainers.
	Usage: /about
	"""

	release_url = "https://docs.google.com/document/d/1FlV3UsJJNA-tMCUpvKgWKp49wI9KrUzVUsT_XmX7ANo/edit?usp=sharing"
	
	client.send_ooc(
		f"You can download CC's files from here: {release_url}
		)

@mod_only()
def ooc_cmd_kick(client, arg: str) -> None:
	"""
	Kick a player.
	Usage: /kick <ipid|*|**> [reason]
	Special cases:
	 - "*" kicks everyone in the current area.
	 - "**" kicks everyone in the server.
	"""
	w = Webhooks(client.server)
	if len(arg) == 0:
		raise ArgumentError(
			'You must specify a target. Use /kick <ipid> [reason]')
	elif arg[0] == '*':
		targets = [c for c in client.area.clients if c != client]
	elif arg[0] == '**':
		targets = [c for c in client.server.client_manager.clients if c != client]
	else:
		targets = None

	args = list(arg.split(' '))
	if targets is None:
		raw_ipid = args[0]
		try:
			ipid = int(raw_ipid)
		except:
			raise ClientError(f'{raw_ipid} does not look like a valid IPID.')
		targets = client.server.client_manager.get_targets(client, TargetType.IPID,
														ipid, False)

	if targets:
		reason = ' '.join(args[1:])
		if reason == '':
			reason = 'N/A'
		for c in targets:
			if c.is_admin:
				client.send_ooc(f'{c.charname} is an admin, cannot kick them.')
				continue
			database.log_misc('kick', client, target=c, data={'reason': reason})
			w.kick(char=c.char_name, ipid=c.ipid, reason=reason)
			client.send_ooc("{} was kicked.".format(
				c.char_name))
			c.send_command('KK', f'Kicked: "{reason}"')
			c.disconnect()
	else:
		client.send_ooc(
			f'No targets with the IPID {ipid} were found.')


def ooc_cmd_ban(client, arg: str) -> None:
	"""
	Ban a user. If a ban ID is specified instead of a reason,
	then the IPID is added to an existing ban record.
	Ban durations are 6 hours by default.
	Usage: /ban <ipid> "reason" ["<N> <minute|hour|day|week|month>(s)|perma"]
	Usage 2: /ban <ipid> <ban_id>
	"""
	kickban(client, arg, False)


def ooc_cmd_banhdid(client, arg: str) -> None:
	"""
	Ban both a user's HDID and IPID.
	DANGER: Banning webAO users by HDID has unintended consequences.
	Usage: See /ban.
	"""
	kickban(client, arg, True)


@mod_only()
def kickban(client, arg, ban_hdid):
	args = shlex.split(arg)
	w = Webhooks(client.server)
	if len(args) < 2:
		raise ArgumentError('Not enough arguments.')
	elif len(args) == 2:
		reason = None
		ban_id = None
		try:
			ban_id = int(args[1])
			unban_date = None
		except ValueError:
			reason = args[1]
			unban_date = arrow.get().shift(hours=6).datetime
	elif len(args) == 3:
		ban_id = None
		reason = args[1]
		if 'perma' in args[2]:
			unban_date = None
		else:
			duration = pytimeparse.parse(args[2], granularity='hours')
			if duration is None:
				raise ArgumentError('Invalid ban duration.')
			unban_date = arrow.get().shift(seconds=duration).datetime
	else:
		raise ArgumentError(f'Ambiguous input: {arg}\nPlease wrap your arguments '
							 'in quotes.')

	try:
		raw_ipid = args[0]
		ipid = int(raw_ipid)
	except ValueError:
		raise ClientError(f'{raw_ipid} does not look like a valid IPID.')
	modfile = 'config/moderation.yaml'
	new = not os.path.exists(modfile)
	if not new:
		with open(modfile, 'r') as chars:
			mods = yaml.safe_load(chars)
		for item in mods:
			ipids = []
			try:
				ipids = item['ipid'].split()
			except:
				ipids.append(item['ipid'])
			if ipid in ipids:
				if item['status'] == 'admin':
					return client.send_ooc('Can\'t ban an admin.')

	ban_id = database.ban(ipid, reason, ban_type='ipid', banned_by=client,
		ban_id=ban_id, unban_date=unban_date)

	if ipid != None:
		targets = client.server.client_manager.get_targets(
			client, TargetType.IPID, ipid, False)
		if targets:
			for c in targets:
				if ban_hdid:
					database.ban(c.hdid, reason, ban_type='hdid', ban_id=ban_id)
					w.ban(char=c.char_name, ipid=c.ipid, ban_id=ban_id, reason=reason, hdid=c.hdid)
				else:
					w.ban(char=c.char_name, ipid=c.ipid, ban_id=ban_id, reason=reason)
				c.send_command('KB', f'Banned: "{reason}"')
				c.disconnect()
				database.log_misc('ban', client, target=c, data={'reason': reason})
			client.send_ooc(f'{len(targets)} clients were kicked.')
		client.send_ooc(f'{ipid} was banned. Ban ID: {ban_id}')


@mod_only()
def ooc_cmd_unban(client, arg: str) -> None:
	"""
	Unban a list of users.
	Usage: /unban <ban_id...>
	"""
	w = Webhooks(client.server)
	if len(arg) == 0:
		raise ArgumentError(
			'You must specify a target. Use /unban <ban_id...>')
	args = list(arg.split(' '))
	client.send_ooc(f'Attempting to lift {len(args)} ban(s)...')
	for ban_id in args:
		if database.unban(ban_id):
			client.send_ooc(f'Removed ban ID {ban_id}.')
			w.unban(client=client, ban_id=ban_id)
		else:
			client.send_ooc(f'{ban_id} is not on the ban list.')
		database.log_misc('unban', client, data={'id': ban_id})

@mod_only()
def ooc_cmd_warn(client, arg: str) -> None:
	"""
	Warn the given user.
	Usage: /warn <ipid> [reason]
	"""
	w = Webhooks(client.server)
	if len(arg) == 0:
		raise ArgumentError(
			'You must specify a target. Use /warn <ipid> [reason]')
	elif len(arg) == 1:
		raise ArgumentError(
			'You must specify a reason. Use /warn <ipid> [reason]')
	else:
		targets = None
		
	args = list(arg.split(' '))
	if targets is None:
		raw_ipid = args[0]
		try:
			ipid = int(raw_ipid)
		except:
			raise ClientError(f'{raw_ipid} does not look like a valid IPID.')
		targets = client.server.client_manager.get_targets(client, TargetType.IPID,
														ipid, False)
	warn_id = None
	if targets:
		reason = ' '.join(args[1:])
		if reason == '':
			reason = 'N/A'
		for c in targets:
			warn_id = database.warn(target=c, reason=reason, warned_by=client)
			w.warn(char=c.char_name, ipid=c.ipid, warn_id=warn_id, reason=reason)
			client.send_ooc("{} was warned. Warn ID: {}".format(
				c.char_name, warn_id))
			c.send_ooc(f"You were warned by a moderator. (ID: {warn_id}) Reason: {reason}")
			c.send_command('WARN', f'"{reason}" (ID: {warn_id})')
			c.send_command('BEEP')
	else:
		client.send_ooc(
			f'No targets with the IPID {ipid} were found.')

@mod_only()
def ooc_cmd_unwarn(client, arg: str) -> None:
	"""
	Remove a list of warn entries from the database.
	Usage: /unwarn <warn_id ...>
	"""
	w = Webhooks(client.server)
	if len(arg) == 0:
		raise ArgumentError(
			'You must specify a target. Use /unwarn <warn_id...>')
	args = list(arg.split(' '))
	client.send_ooc(f'Attempting to revoke {len(args)} warn(s)...')
	for warn_id in args:
		if database.unwarn(warn_id):
			client.send_ooc(f'Removed warn entry with ID {warn_id}.')
			w.unwarn(client=client,warn_id=warn_id)
		else:
			client.send_ooc(f'No entry exists for warn ID {warn_id}.')
		database.log_misc('unwarn', client, data={'id': warn_id})

@mod_only()
def ooc_cmd_mute(client, arg):
	"""
	Prevent a user from speaking in-character.
	Usage: /mute <ipid>
	"""
	if len(arg) == 0:
		raise ArgumentError('You must specify a target. Use /mute <ipid>.')
	args = list(arg.split(' '))
	client.send_ooc(f'Attempting to mute {len(args)} IPIDs.')
	for raw_ipid in args:
		if raw_ipid.isdigit():
			ipid = int(raw_ipid)
			clients = client.server.client_manager.get_targets(
				client, TargetType.IPID, ipid, False)
			if (clients):
				msg = 'Muted the IPID ' + str(ipid) + '\'s following clients:'
				for c in clients:
					c.is_muted = True
					database.log_misc('mute', client, target=c)
					msg += ' ' + c.char_name + ' [' + str(c.id) + '],'
				msg = msg[:-1]
				msg += '.'
				client.send_ooc(msg)
			else:
				client.send_ooc(
					"No targets found. Use /mute <ipid> <ipid> ... for mute.")
		else:
			client.send_ooc(
				f'{raw_ipid} does not look like a valid IPID.')


@mod_only()
def ooc_cmd_unmute(client, arg):
	"""
	Unmute a user.
	Usage: /unmute <ipid>
	"""
	if len(arg) == 0:
		raise ArgumentError('You must specify a target.')
	args = list(arg.split(' '))
	client.send_ooc(f'Attempting to unmute {len(args)} IPIDs.')
	for raw_ipid in args:
		if raw_ipid.isdigit():
			ipid = int(raw_ipid)
			clients = client.server.client_manager.get_targets(
				client, TargetType.IPID, ipid, False)
			if (clients):
				msg = f'Unmuted the IPID ${str(ipid)}\'s following clients:'
				for c in clients:
					c.is_muted = False
					database.log_misc('unmute', client, target=c)
					msg += ' ' + c.char_name + ' [' + str(c.id) + '],'
				msg = msg[:-1]
				msg += '.'
				client.send_ooc(msg)
			else:
				client.send_ooc(
					"No targets found. Use /unmute <ipid> <ipid> ... for unmute."
				)
		else:
			client.send_ooc(
				f'{raw_ipid} does not look like a valid IPID.')


def ooc_cmd_login(client, arg: str) -> None:
	"""
	Logs the user in as a moderator.

    Calls auth_mod to check whether or not the user's login attempt is 
    valid. 

	Should return a message in-client confirming login and 
	log profile in the server's internal log. 

    Will throw an error and log it if not and send an OOC message in-client
    stating that the user's login attempt was invalid. 

    Usage: /login <password> (The user might not require using a mod pass
    if their profile already exists in the moderation.yaml)

    Parameters:
    client = An instance of the class Client. 
    arg = The mod pass used in order to log in.

    Precondition: arg is a valid mod pass. 
    Otherwise, throws login_invalid error. 


	"""
	login_name = None
	try:
		login_name = client.auth_mod(arg)
	except ClientError:
		client.send_command('AUTH', '0')
		database.log_misc('login.invalid', client)
		raise
    
	client.send_ooc('Logged in as a moderator.')
	client.send_command('AUTH', '1')
	database.log_misc('login', client, data={'profile': login_name})

    # I don't know what this is supposed to be and why it was
	# in the docstring, but I'll leave it here in case it bears
	# any unexpected relevance.
	# - HolyMan

	# if len(arg) == 0:
	#	raise ArgumentError('You must specify the password.')
	# login_name = None
	# try:
	#	login_name = client.auth_mod(arg)
	# except ClientError:
	#	database.log_misc('login.invalid', client)
	#	raise
	# if client.area.evidence_mod == 'HiddenCM':
	#	client.area.broadcast_evidence_list()
	# client.send_ooc('Logged in as a moderator.')
	# database.log_misc('login', client, data={'profile': login_name})


@mod_only()
def ooc_cmd_refresh(client, arg):
	"""
	Reload all moderator credentials, server options, and commands without
	restarting the server.
	Usage: /refresh
	"""
	if len(arg) > 0:
		raise ClientError('This command does not take in any arguments!')
	else:
		try:
			client.server.refresh()

			database.log_misc('refresh', client)
			client.send_ooc('You have reloaded the server.')
		except ServerError:
			raise

def ooc_cmd_online(client, _):
	"""
	Show the number of players online.
	Usage: /online
	"""
	client.send_player_count()


def ooc_cmd_mods(client, arg):
	"""
	Show a list of moderators online.
	Usage: /mods
	"""
	if client.is_mod:
		mods = set()
		add = ''
		for area in client.server.area_manager.areas:
			modshere = area.get_mods()
			if len(modshere) > 0:
				add += f'\n=== {area.name} ===\n[{area.abbreviation}]: [{len(area.clients)} Users][{area.status}]'
				for mod in modshere:
					mods.add(mod)
					add += f'\n[{mod.id}] {mod.char_name} ({mod.ipid}): {mod.name}'
			if area.is_hub and len(area.subareas) > 0:
				for sub in area.subareas:
					if len(modshere) == 0 and len(sub.get_mods()) > 0:
						add += f'\n=== {sub.name} ===\n[{sub.abbreviation}]: [{len(sub.clients)} Users][{sub.status}]'
					for mod in sub.get_mods():
						mods.add(mod)
						add += f'\n[{mod.id}] {mod.char_name} ({mod.ipid}): {mod.name}'
		info = f'Mods online: {len(mods)}'
		info += add
		client.send_ooc(info)
	else:
		mods = client.server.area_manager.mods_online()
		if mods != 0:
			client.send_ooc(f'There are currently {mods} moderators online.')
		else:
			client.send_ooc('There are no moderators online.')

def ooc_cmd_unmod(client, arg):
	"""
	Log out as a moderator.
	Usage: /unmod
	"""
	client.is_mod = False
	client.is_admin = False
	client.mod_profile_name = None
	if client.area.evidence_mod == 'HiddenCM':
		client.area.broadcast_evidence_list()
	client.send_ooc('You\'re not a mod anymore.')
	client.send_command('AUTH', '-1')


@mod_only()
def ooc_cmd_oocmute(client, arg):
	"""
	Prevent a user from talking out-of-character.
	Usage: /ooc_mute <ooc-name>
	"""
	if len(arg) == 0:
		raise ArgumentError(
			'You must specify a target. Use /ooc_mute <ID>.')
	targets = client.server.client_manager.get_targets(client, TargetType.ID,
													 int(arg), False)
	if not targets:
		raise ArgumentError('Targets not found. Use /ooc_mute <ID>.')
	for target in targets:
		target.is_ooc_muted = True
		database.log_room('ooc_mute', client, client.area, target=target)
	client.send_ooc('Muted {} existing client(s).'.format(
		len(targets)))


@mod_only()
def ooc_cmd_oocunmute(client, arg: str) -> None:
	"""
	Allow an OOC-muted user to talk out-of-character.
	Usage: /ooc_unmute <ooc-name>
	"""
	if len(arg) == 0:
		raise ArgumentError(
			'You must specify a target. Use /ooc_unmute <ID>.')
	targets = client.server.client_manager.get_targets(client, TargetType.ID,
													 int(arg), False)
	if not targets:
		raise ArgumentError('Targets not found. Use /ooc_unmute <ID>.')
	for target in targets:
		target.is_ooc_muted = False
		database.log_room('ooc_unmute', client, client.area, target=target)
	client.send_ooc('Unmuted {} existing client(s).'.format(
		len(targets)))

@mod_only()
def ooc_cmd_bans(client, _arg: str) -> None:
	"""
	Get the 5 most recent bans.
	Usage: /bans
	"""
	msg = 'Last 5 bans:\n'
	bandate = None
	for ban in database.recent_bans():
		if ban.ban_date == None or ban.ban_date == "None":
			bandate = "N/A"
		else:
			bandate = ban.ban_date
		time = bandate
		msg += f'{time}: {ban.banned_by_name} ({ban.banned_by}) issued ban ' \
			   f'{ban.ban_id} (\'{ban.reason}\')\n'
	client.send_ooc(msg)

@mod_only()
def ooc_cmd_baninfo(client, arg: str) -> None:
	"""
	Get information about a ban.
	Usage: /baninfo <id> ['ban_id'|'ipid'|'hdid']
	By default, id identifies a ban_id.
	"""
	args = arg.split(' ')
	if len(arg) == 0:
		raise ArgumentError('You must specify an ID.')
	elif len(args) == 1:
		lookup_type = 'ban_id'
	else:
		lookup_type = args[1]

	if lookup_type not in ('ban_id', 'ipid', 'hdid'):
		raise ArgumentError('Incorrect lookup type.')

	ban = database.find_ban(**{lookup_type: args[0]})
	if ban is None:
		client.send_ooc('No ban found for this ID.')
	else:
		msg = f'\nBan ID: {ban.ban_id}\n'
		msg += 'Affected IPIDs: ' + ', '.join([str(ipid) for ipid in ban.ipids]) + '\n'
		msg += 'Affected HDIDs: ' + ', '.join(ban.hdids) + '\n'
		msg += f'Reason: "{ban.reason}"\n'
		msg += f'Banned by: {ban.banned_by_name} ({ban.banned_by})\n'

		ban_date = arrow.get(ban.ban_date)
		msg += f'Banned on: {ban_date.format()} ({ban_date.humanize()})\n'
		if ban.unban_date is not None:
			unban_date = arrow.get(ban.unban_date)
			msg += f'Unban date: {unban_date.format()} ({unban_date.humanize()})'
		else:
			msg += 'Unban date: N/A'
		client.send_ooc(msg)
		
def ooc_cmd_warns(client, arg: str) -> None:
	"""
	Get the warns for a given IPID. Returns the last 5 by default.
	Use with no arguments to view warns for your own IPID (must not be logged in)
	Usage: /warns [count] (logged out)
		   /warns <ipid> [count] (logged in)
	"""
	args = arg.split(' ')
	# TODO: Make this shorter.
	# Or don't. I'm a TODO, not a cop.
	raw_ipid = None
	raw_count = None
	if len(arg) == 0:
		ipid = client.ipid
		count = 5
	elif len(args) == 1 and client.is_mod:
		raw_ipid = args[0]
		count = 5
	else:
		if client.is_mod:
			raw_ipid = args[0]
			raw_count = args[1]
		else:
			ipid = client.ipid
			raw_count = args[0]
	# if it applies, validate the raw input
	if raw_ipid != None:
		try:
			ipid = int(raw_ipid)
		except ValueError:
			raise ClientError(f'{raw_ipid} does not look like a valid IPID.')
	if raw_count != None:
		try:
			count = int(raw_count)
		except ValueError:
			client.send_ooc(f'Unable to parse \'{raw_count}\' as int, defaulting to 5.')
			count = 5
	# this is done to avoid exposing non-mod users to their own IPID
	target = 'your IPID' if ipid == client.ipid and not client.is_mod else f'IPID \'{ipid}\''
	warns = database.list_warns(query=ipid, count=count)
	msg = f'Last {len(warns)} warning(s) for {target}:\n'
	if not warns:
		client.send_ooc(f'No warnings found for {target}. Either it does not exist, or it has never received a warning.')
	else:
		for warn in warns:
			msg += f'\n------\n'
			msg += f'Warn ID: {warn.warn_id}\n'
			msg += f'Reason: "{warn.reason}"\n'
			# just to be safe, don't expose the warned_by IPID to non-mods
			if client.is_mod: warned_by = f'{warn.warned_by_name} ({warn.warned_by})'
			else: warned_by = f'{warn.warned_by_name}'
			msg += f'Issued by: {warned_by}\n'
			warn_date = arrow.get(warn.warn_date)
			msg += f'Warned on: {warn_date.format()} ({warn_date.humanize()})\n'
		msg += f'------'
		client.send_ooc(msg)
		
	
@mod_only()
def ooc_cmd_warnsby(client, arg: str) -> None:
	"""
	Get a list of warns issued by the given IPID. Returns the last 5 by default.
	In the interest of streamlining, "me" resolves to the IPID of the user.
	Usage: /warnsby {ipid | me} [count]
	"""
	args = arg.split(' ')
	raw_ipid = None
	raw_count = None
	if len(arg) == 0:
		raise ArgumentError('Not enough arguments - you must either specify an IPID or use "me" to view your own issued warns.')
	elif len(args) == 1:
		count = 5
	else:
		raw_count = args[1]

	if args[0] == 'me':
		ipid = client.ipid
	else:
		raw_ipid = args[0]
		
	# if it applies, validate the raw input
	if raw_ipid != None:
		try:
			ipid = int(raw_ipid)
		except ValueError:
			raise ClientError(f'{raw_ipid} does not look like a valid IPID.')
	if raw_count != None:
		try:
			count = int(raw_count)
		except ValueError:
			client.send_ooc(f'Unable to parse \'{raw_count}\' as int, defaulting to 5.')
			count = 5

	warns = database.list_warns(query=ipid, count=count, lookup_type='warned_by')
	msg = f'Last {len(warns)} warning(s) issued by IPID \'{ipid}\':\n'
	if not warns:
		client.send_ooc(f'There are no warnings issued by IPID \'{ipid}\'. Either it does not exist, or it has never issued a warning.')
	else:
		for warn in warns:
			msg += f'\n------\n'
			msg += f'Warn ID: {warn.warn_id}\n'
			msg += f'Reason: "{warn.reason}"\n'
			msg += f'Issued by: {warn.warned_by_name} ({warn.warned_by})\n'
			warn_date = arrow.get(warn.warn_date)
			msg += f'Warned on: {warn_date.format()} ({warn_date.humanize()})\n'
		msg += f'------'
		client.send_ooc(msg)
		
@mod_only()
def ooc_cmd_warninfo(client, arg: str) -> None:
	"""
	Get information about a warn.
	Usage: /warninfo <warn_id>
	"""
	args = arg.split(' ')
	if len(arg) == 0:
		raise ArgumentError('You must specify an ID.')

	try:
		warn_id = int(args[0])
	except ValueError:
		raise ClientError(f'{args[0]} does not look like a valid warn ID.')

	warns = database.find_warn(warn_id)
	if not warns:
		client.send_ooc('No warnings found for this ID.')
	else:
		for warn in warns:
			msg = f'\nWarn ID: {warn.warn_id}\n'
			msg += f'IPID warned: {warn.ipid}\n'
			msg += f'Reason: "{warn.reason}"\n'
			msg += f'Issued by: {warn.warned_by_name} ({warn.warned_by})\n'

			warn_date = arrow.get(warn.warn_date)
			msg += f'Warned on: {warn_date.format()} ({warn_date.humanize()})'
			client.send_ooc(msg)