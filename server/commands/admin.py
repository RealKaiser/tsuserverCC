import shlex

import arrow
import pytimeparse

from server import database
from server.webhooks import Webhooks
from server.constants import TargetType
from server.exceptions import ClientError, ServerError, ArgumentError

from . import mod_only

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
    'ooc_cmd_ghost'
]

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
    for a in client.server.area_manager.areas:
        for c in a.clients:
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
        raise ArgumentError('Vote either "yay" or"nay". Check the server poll by using no argument.')

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

def ooc_cmd_permit(client, arg):
    if not client.is_mod:
        raise ClientError('You are not authorized.')
    else:
        if len(arg) > 0:
            arg = arg.split(' ')
        for id in arg:
            try:
                id = int(id)
                c = client.server.client_manager.get_targets(client, TargetType.ID, id, False)[0]
                if c.permission == False:
                    c.permission = True
                    client.send_ooc(f'{c.char_name} has been granted permission.')
                    c.send_ooc('You have been granted special permissions.')
                    return
                else:
                    c.permission = False
                    client.send_ooc(f'{c.char_name}\'s permissions have been revoked.')
                    c.send_ooc('Your special permissions have been revoked.')
                    return
            except:
                client.send_ooc(f'{id} does not look like a valid ID.')

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


@mod_only()
def ooc_cmd_kick(client, arg):
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
            database.log_misc('kick', client, target=c, data={'reason': reason})
            w.kick(char=c.char_name, ipid=c.ipid, reason=reason)
            client.send_ooc("{} was kicked.".format(
                c.char_name))
            c.send_command('KK', 'Kicked: ' + reason)
            c.disconnect()
    else:
        client.send_ooc(
            f'No targets with the IPID {ipid} were found.')


def ooc_cmd_ban(client, arg):
    """
    Ban a user. If a ban ID is specified instead of a reason,
    then the IPID is added to an existing ban record.
    Ban durations are 6 hours by default.
    Usage: /ban <ipid> "reason" ["<N> <minute|hour|day|week|month>(s)|perma"]
    Usage 2: /ban <ipid> <ban_id>
    """
    kickban(client, arg, False)


def ooc_cmd_banhdid(client, arg):
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
                c.send_command('KB', 'Banned: ' + reason)
                c.disconnect()
                database.log_misc('ban', client, target=c, data={'reason': reason})
            client.send_ooc(f'{len(targets)} clients were kicked.')
        client.send_ooc(f'{ipid} was banned. Ban ID: {ban_id}')


@mod_only()
def ooc_cmd_unban(client, arg):
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
def ooc_cmd_warn(client, arg):
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
            c.send_command('BEEP')
    else:
        client.send_ooc(
            f'No targets with the IPID {ipid} were found.')

@mod_only()
def ooc_cmd_unwarn(client, arg):
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


def ooc_cmd_login(client, arg):
    """
    Login as a moderator.
    Usage: /login <password>
    """
    if len(arg) == 0:
        raise ArgumentError('You must specify the password.')
    login_name = None
    try:
        login_name = client.auth_mod(arg)
    except ClientError:
        database.log_misc('login.invalid', client)
        raise
    if client.area.evidence_mod == 'HiddenCM':
        client.area.broadcast_evidence_list()
    client.send_ooc('Logged in as a moderator.')
    database.log_misc('login', client, data={'profile': login_name})


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
        client.send_area_info(-1, True)
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
    client.mod_profile_name = None
    if client.area.evidence_mod == 'HiddenCM':
        client.area.broadcast_evidence_list()
    client.send_ooc('you\'re not a mod now')


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
def ooc_cmd_oocunmute(client, arg):
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
def ooc_cmd_bans(client, _arg):
    """
    Get the 5 most recent bans.
    Usage: /bans
    """
    msg = 'Last 5 bans:\n'
    for ban in database.recent_bans():
        time = arrow.get(ban.ban_date).humanize()
        msg += f'{time}: {ban.banned_by_name} ({ban.banned_by}) issued ban ' \
               f'{ban.ban_id} (\'{ban.reason}\')\n'
    client.send_ooc(msg)

@mod_only()
def ooc_cmd_baninfo(client, arg):
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
        msg = f'Ban ID: {ban.ban_id}\n'
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
        
def ooc_cmd_warns(client, arg):
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
            msg += f'------\n'
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
def ooc_cmd_warnsby(client, arg):
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
            msg += f'------\n'
            msg += f'Warn ID: {warn.warn_id}\n'
            msg += f'Reason: "{warn.reason}"\n'
            msg += f'Issued by: {warn.warned_by_name} ({warn.warned_by})\n'
            warn_date = arrow.get(warn.warn_date)
            msg += f'Warned on: {warn_date.format()} ({warn_date.humanize()})\n'
        msg += f'------'
        client.send_ooc(msg)
        
@mod_only()
def ooc_cmd_warninfo(client, arg):
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
            msg = f'Warn ID: {warn.warn_id}\n'
            msg += f'IPID warned: {warn.ipid}\n'
            msg += f'Reason: "{warn.reason}"\n'
            msg += f'Issued by: {warn.warned_by_name} ({warn.warned_by})\n'

            warn_date = arrow.get(warn.warn_date)
            msg += f'Warned on: {warn_date.format()} ({warn_date.humanize()})'
            client.send_ooc(msg)