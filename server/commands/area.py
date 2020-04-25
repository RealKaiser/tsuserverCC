from server import database
from server.constants import TargetType
from server.exceptions import ClientError, ArgumentError, AreaError

from . import mod_only

__all__ = [
    'ooc_cmd_bg',
    'ooc_cmd_custombg',
    'ooc_cmd_bglock',
    'ooc_cmd_allowiniswap',
    'ooc_cmd_allowblankposting',
    'ooc_cmd_forcenonintpres',
    'ooc_cmd_status',
    'ooc_cmd_customstatus',
    'ooc_cmd_area',
    'ooc_cmd_getarea',
    'ooc_cmd_getareas',
    'ooc_cmd_lock',
    'ooc_cmd_unlock',
    'ooc_cmd_spectatable',
    'ooc_cmd_invite',
    'ooc_cmd_uninvite',
    'ooc_cmd_uninviteall',
    'ooc_cmd_iclock',
    'ooc_cmd_areakick',
    'ooc_cmd_addcustom',
    'ooc_cmd_removecustom',
    'ooc_cmd_customlist',
    'ooc_cmd_clearcustomlist',
    'ooc_cmd_connect',
    'ooc_cmd_biconnect',
    'ooc_cmd_connectlist',
    'ooc_cmd_disconnect',
    'ooc_cmd_bidisconnect',
    'ooc_cmd_clearconnect',
    'ooc_cmd_hidecount',
    'ooc_cmd_rename',
    'ooc_cmd_create',
    'ooc_cmd_destroy',
    'ooc_cmd_currentbg',
    'ooc_cmd_shouts',
    'ooc_cmd_allclients',
    'ooc_cmd_poslock',
    'ooc_cmd_password'
]

def ooc_cmd_poslock(client, arg):
    if len(arg) == 0:
        if len(client.area.poslock) > 0:
            msg = 'This area is poslocked to:'
            for pos in client.area.poslock:
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
        client.send_ooc('Poslock cleared.')
    else:
        positions = ('def', 'pro', 'hld', 'hlp', 'jud', 'wit', 'jur', 'sea')
        args = arg.split()
        for pos in args:
            if pos in positions:
                client.area.poslock.append(pos)
                client.send_ooc(f'{pos} added to area\'s poslock.')
            else:
                client.send_ooc(f'{pos} doesn\'t seem to be a valid position.')

def ooc_cmd_allclients(client, arg):
    if not client.is_mod:
        raise ArgumentError('You must be authorized to do that.')
    msg = 'Connected clients:'
    for c in client.server.client_manager.clients:
        msg += f'\n{c.name}'
    client.send_ooc(msg)

def ooc_cmd_shouts(client, arg):
    if client not in client.area.owners and not client.is_mod:
        raise ClientError('You must be a CM.')
    if len(arg) == 0:
        client.area.poslock = []
        client.send_ooc('Area poslock cleared.')

def ooc_cmd_shouts(client, arg):
    if client not in client.area.owners and not client.is_mod:
        raise ClientError('You must be a CM.')
    if client.area.shouts_allowed:
        client.area.shouts_allowed = False
        client.area.broadcast_ooc('Shouts have been disallowed in this area.')
    else:
        client.area.shouts_allowed = True
        client.area.broadcast_ooc('Shouts have been allowed in this area.')

def ooc_cmd_hidecount(client, arg):
    if client not in client.area.owners and not client.is_mod:
        raise ClientError('You must be a CM.')
    if len(arg) > 0:
        raise ArgumentError('This command takes no arguments.')
    if client.area.hidden == False:
        client.area.hidden = True
        client.server.area_manager.send_arup_players()
        client.area.broadcast_ooc('The playercount for this area has been hidden.')
    else:
        client.area.hidden = False
        client.server.area_manager.send_arup_players()
        client.area.broadcast_ooc('The playercount for this area has been revealed.')

def ooc_cmd_create(client, arg):
    if not client.is_mod and client.permission == False:
        raise ClientError('You must have permission to create an area, please ask staff.')
    if len(arg) == 0:
        raise ArgumentError('Not enough arguments, use /create <name>.')
    if len(arg) > 25:
        raise ArgumentError('That name is too long!')
    staffroom = None
    for a in client.server.area_manager.areas:
        if a.abbreviation == 'SR':
            staffroom = a
    client.server.area_manager.areas.remove(staffroom)
    new_id = staffroom.id
    staffroom.id = client.server.area_manager.cur_id
    client.server.area_manager.cur_id += 1
    client.server.area_manager.areas.append(client.server.area_manager.Area(new_id, client.server, name=arg, background='MeetingRoom', bg_lock=False, evidence_mod='CM', locking_allowed=True, iniswap_allowed=True, showname_changes_allowed=True, shouts_allowed=True, jukebox=False, abbreviation='CA', non_int_pres_only=False))
    client.server.area_manager.areas.append(staffroom)
    client.server.build_music_list_ao2()
    client.server.send_all_cmd_pred(
        'CT', '{}'.format(client.server.config['hostname']),
        f'=== Announcement ===\r\nA new area has been created.\n[{new_id}] {arg}\r\n==================', '1')

def ooc_cmd_destroy(client, arg):
    if client not in client.area.owners and not client.is_mod:
        raise ClientError('You must be CM.')
    if not client.is_mod and client.permission == False:
        raise ClientError('You must have permission to destroy an area, please ask staff.')
    if not client.is_mod and client.area.abbreviation != 'CA':
        raise AreaError('You are not allowed to destroy non-custom areas!')
    if len(arg) > 0:
        raise ArgumentError('This command takes no arguments.')
    destroyed = client.area
    destroyedclients = set()
    client.server.area_manager.send_arup_cms()
    client.server.area_manager.cur_id = 0
    client.server.area_manager.areas.remove(destroyed)
    list = []
    for a in client.server.area_manager.areas:
        list.append(a)
        a.id = client.server.area_manager.cur_id
        client.server.area_manager.cur_id += 1
    for c in destroyed.clients:
        if c in destroyed.owners:
            destroyed.owners.remove(c)
            database.log_room('cm.remove', c, c.destroyed, target=c)
        destroyedclients.add(c)
    landing = client.server.area_manager.get_area_by_id(0)
    for cc in destroyedclients:
        if cc in destroyed.clients:
            cc.change_area(landing)
            cc.send_ooc(f'You were removed from {destroyed.name} because it was destroyed.')
    client.server.area_manager.areas.clear()
    for aa in list:
        client.server.area_manager.areas.append(aa)
    client.server.build_music_list_ao2()
    client.server.send_all_cmd_pred('CT', '{}'.format(client.server.config['hostname']), f'=== Announcement ===\r\n{destroyed.name} was destroyed and no longer exists.\r\n==================', '1')


def ooc_cmd_rename(client, arg):
    if client not in client.area.owners and not client.is_mod:
        raise ClientError('You must be a CM.')
    if not client.is_mod and client.permission == False:
        raise ClientError('You must have permission to rename an area, please ask staff.')
    if len(arg) == 0:
        raise ArgumentError('Not enough arguments, use /rename <name>.')
    if len(arg) > 25:
        raise ArgumentError('That name is too long!')
    if not client.is_mod and client.area.abbreviation.startswith('CR') == True:
        raise AreaError('Can\'t change the name of a Courtroom.')
    old_name = client.area.name
    client.area.name = arg
    client.server.build_music_list_ao2()
    client.server.send_all_cmd_pred(
        'CT', '{}'.format(client.server.config['hostname']),
        f'=== Announcement ===\r\n{old_name} [{client.area.id}] has been renamed to {client.area.name}.\r\n==================', '1')

def ooc_cmd_bg(client, arg):
    """
    Set the background of a room.
    Usage: /bg <background>
    """
    if len(arg) == 0:
        raise ArgumentError('You must specify a name. Use /bg <background>.')
    if not client.is_mod and client.area.bg_lock == True:
        raise AreaError("This area's background is locked")
    try:
        client.area.change_background(arg)
    except AreaError:
        raise
    client.area.broadcast_ooc(
        f'{client.char_name} changed the background to {arg}.')
    database.log_room('bg', client, client.area, message=arg)

def ooc_cmd_currentbg(client, arg):
    """
    Set the background of a room.
    Usage: /bg <background>
    """
    if len(arg) > 0:
        raise ArgumentError('This command takes no arguments.')
    client.send_ooc(f'Current background is "{client.area.background}".')

def ooc_cmd_custombg(client, arg):
    """
    Set the background of a room.
    Usage: /bg <background>
    """
    if client not in client.area.owners and not client.is_mod:
        raise ClientError('You must be a CM.')
    if len(arg) == 0:
        raise ArgumentError('You must specify a name. Use /bg <background>.')
    msg = 'custom/'
    msg += arg
    try:
        client.area.change_cbackground(msg)
    except AreaError:
        raise
    client.area.broadcast_ooc(
        f'{client.char_name} changed the background to {arg}.')
    database.log_room('bg', client, client.area, message=msg)

def ooc_cmd_addcustom(client, arg):
    """
    Adds a link to the custom list.
    Usage: /addcustom <link>
    """
    if len(arg) == 0:
        raise ArgumentError('You must specify a link. Use /addcustom <link>.')
    elif client.char_name.startswith("custom"):
        client.area.custom_list[client.char_name] = arg
        client.area.broadcast_ooc('{} added a link for their custom.'.format(client.char_name))
    else:
        raise ClientError('You must play as a custom character.')

def ooc_cmd_removecustom(client, arg):
    """
    Removes a link from the custom list.
    Usage: /removecustom
    """
    try:
        del client.area.custom_list[client.char_name]
        client.area.broadcast_ooc('{} erased their link from the custom list.'.format(
            client.char_name))
    except KeyError:
        raise ClientError('You do not have a custom set.')

def ooc_cmd_customlist(client, arg):
    """
    Updates the custom list and then shows it.
    Usage: /customlist
    """
    if len(arg) > 0:
        raise ArgumentError('This command takes no arguments.')
    elif len(client.area.custom_list) == 0:
        raise AreaError('The custom list is empty.')
    msg = "Custom List:"
    for customadder, customlink in client.area.custom_list.items():
        msg += f' \n{customadder}: {customlink}'
    client.send_ooc(msg)

def ooc_cmd_clearcustomlist(client, arg):
    """
    Updates the custom list and then shows it.
    Usage: /customlist
    """
    client.area.custom_list.clear()
    client.area.broadcast_ooc('The custom list was cleared.')

def ooc_cmd_bglock(client, arg):
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
def ooc_cmd_allowiniswap(client, arg):
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


def ooc_cmd_allowblankposting(client, arg):
    """
    Toggle whether or not in-character messages purely consisting of spaces
    are allowed.
    Usage: /allow_blankposting
    """
    if client not in client.area.owners and not client.is_mod:
        raise ClientError('You must be a CM.')
    client.area.blankposting_allowed = not client.area.blankposting_allowed
    answer = 'allowed' if client.area.blankposting_allowed else 'forbidden'
    client.area.broadcast_ooc(
        '{} [{}] has set blankposting in the area to {}.'.format(
            client.char_name, client.id, answer))
    database.log_room('blankposting', client, client.area, message=client.area.blankposting_allowed)


def ooc_cmd_forcenonintpres(client, arg):
    """
    Toggle whether or not all pre-animations lack a delay before a
    character begins speaking.
    Usage: /force_nonint_pres
    """
    if client not in client.area.owners and not client.is_mod:
        raise ClientError('You must be a CM.')
    client.area.non_int_pres_only = not client.area.non_int_pres_only
    answer = 'non-interrupting only' if client.area.non_int_pres_only else 'non-interrupting or interrupting as you choose'
    client.area.broadcast_ooc(
        '{} [{}] has set pres in the area to be {}.'.format(
            client.char_name, client.id, answer))
    database.log_room('force_nonint_pres', client, client.area, message=client.area.non_int_pres_only)


def ooc_cmd_status(client, arg):
    """
    Show or modify the current status of a room.
    Usage: /status <idle|rp|casing|looking-for-players|lfp|recess|gaming>
    """
    if len(arg) == 0:
        client.send_ooc(f'Current status: {client.area.status}')
    elif 'CM' not in client.area.evidence_mod:
        raise ClientError('You can\'t change the status of this area')
    else:
        try:
            client.area.change_status(arg)
            client.area.broadcast_ooc('{} changed status to {}.'.format(
                client.char_name, client.area.status))
            database.log_room('status', client, client.area, message=arg)
        except AreaError:
            raise

def ooc_cmd_customstatus(client, arg):
    """
    Show or modify the current status of a room.
    Usage: /status <idle|rp|casing|looking-for-players|lfp|recess|gaming>
    """
    if len(arg) == 0:
        client.send_ooc(f'Current status: {client.area.status}')
    elif 'CM' not in client.area.evidence_mod and not client.is_mod:
        raise ClientError('You can\'t change the status of this area')
    elif client not in client.area.owners and not client.is_mod:
        raise ClientError('You must be CM.')
    elif len(arg) > 35:
        raise ArgumentError('That status is too long!')
    else:
        try:
            client.area.custom_status(arg)
            client.area.broadcast_ooc('{} changed status to {}.'.format(
                client.char_name, client.area.status))
            database.log_room('status', client, client.area, message=arg)
        except AreaError:
            raise

def ooc_cmd_area(client, arg):
    """
    List areas, or go to another area/room.
    Usage: /area [id]
    """
    args = arg.split()
    if len(args) == 0:
        client.send_area_list()
    elif len(args) == 1:
        try:
            area = client.server.area_manager.get_area_by_id(int(args[0]))
            client.change_area(area)
        except ValueError:
            raise ArgumentError('Area ID must be a number.')
        except (AreaError, ClientError):
            raise
    elif len(args) == 2:
        try:
            area = client.server.area_manager.get_area_by_id(int(args[0]))
            if area.password != '':
                if area.password == args[1]:
                    area.invite_list[client.id] = None
                    client.send_ooc('Password accepted.')
            client.change_area(area)
        except ValueError:
            raise ArgumentError('Area ID must be a number.')
        except (AreaError, ClientError):
            raise
    else:
        raise ArgumentError('Too many arguments. Use /area <id> and optionally <password>.')

def ooc_cmd_connect(client, arg):
    """
    Connects areas together.
    """
    args = arg.split()
    if client not in client.area.owners and not client.is_mod:
        raise ClientError('You must be a CM.')
    elif len(args) == 0:
        raise ArgumentError('You must specify an area, use /connect <area id>')
    elif len(args) == 1:
        try:
            connection = client.server.area_manager.get_area_by_id(int(args[0]))
            landing = client.server.area_manager.get_area_by_id(0)
            is_landing = False
            for c in client.area.connections:
                if c == connection:
                    raise AreaError('Area is already connected.')
                if c == landing:
                    is_landing = True
            if landing != connection and not is_landing:
                client.area.connections.append(landing)
            client.area.connections.append(connection)
            client.area.is_restricted = True
            client.send_ooc(f'Area connected to {connection.name}')
        except ValueError:
            raise ArgumentError('Area ID must be a number.')
        except (AreaError, ClientError):
            raise
    else:
        raise ArgumentError('Too many arguments. Use /connect <area id>.')

def ooc_cmd_biconnect(client, arg):
    """
    Connects areas together.
    """
    args = arg.split()
    if client not in client.area.owners and not client.is_mod:
        raise ClientError('You must be a CM.')
    elif len(args) == 0:
        raise ArgumentError('You must specify an area, use /connect <area id>')
    elif len(args) == 1:
        try:
            connection = client.server.area_manager.get_area_by_id(int(args[0]))
            landing = client.server.area_manager.get_area_by_id(0)
            is_landing = False
            is_connected = False
            for c in client.area.connections:
                if c == connection:
                    raise AreaError('Area is already connected.')
                if c == landing:
                    is_landing = True
            if landing != connection and not is_landing:
                client.area.connections.append(landing)
            client.area.connections.append(connection)
            client.area.is_restricted = True
            for c in connection.connections:
                if c == landing:
                    is_landing = True
                if c == client.area:
                    is_connected = True
            if not is_landing:
                connection.connections.append(landing)
            if not is_connected and client in connection.owners:
                connection.connections.append(client.area)
            elif client not in connection.owners:
                client.send_ooc('Only a one-way connection was established. You are not the CM of the connected area.')
            client.send_ooc(f'Area bi-connected to [{connection.id}]{connection.name}')
        except ValueError:
            raise ArgumentError('Area ID must be a number.')
        except (AreaError, ClientError):
            raise
    else:
        raise ArgumentError('Too many arguments. Use /connect <area id>.')

def ooc_cmd_connectlist(client, arg):
    """
    Connects areas together.
    """
    if len(arg) > 0:
        raise ArgumentError('This command takes no arguments.')
    if len(client.area.connections) == 0:
        raise AreaError('This area has no connections.')
    msg = f'[{client.area.id}]{client.area.name} is connected to '
    index = 0
    for connection in client.area.connections:
        if index > 0:
            msg += ', '
        msg += f'[{connection.id}]{connection.name}'
        index += 1
    msg += '.'
    client.send_ooc(msg)

def ooc_cmd_clearconnect(client, arg):
    """
    Connects areas together.
    """
    if len(arg) > 0:
        raise ArgumentError('This command takes no arguments.')
    if client not in client.area.owners and not client.is_mod:
        raise ClientError('You must be a CM.')
    client.area.connections.clear()
    client.area.is_restricted = False
    client.area.broadcast_ooc(f'All {client.area.name} connections cleared.')

def ooc_cmd_disconnect(client, arg):
    """
    Connects areas together.
    """
    args = arg.split()
    if client not in client.area.owners and not client.is_mod:
        raise ClientError('You must be a CM.')
    elif len(args) == 0:
        raise ArgumentError('You must specify an area, use /disconnect <area id>')
    elif len(args) == 1:
        try:
            connection = client.server.area_manager.get_area_by_id(int(args[0]))
            client.area.connections.remove(connection)
            client.send_ooc(f'Area disconnected from {connection.name}')
            for a in client.area.connections:
                if a.id == 0:
                    client.area.connections.remove(a)
            if len(client.area.connections) == 0:
                client.area.is_restricted = False
        except ValueError:
            raise ArgumentError('Area ID must be a number.')
        except (AreaError, ClientError):
            raise
    else:
        raise ArgumentError('Too many arguments. Use /connect <area id>.')

def ooc_cmd_bidisconnect(client, arg):
    """
    Connects areas together.
    """
    args = arg.split()
    if client not in client.area.owners and not client.is_mod:
        raise ClientError('You must be a CM.')
    elif len(args) == 0:
        raise ArgumentError('You must specify an area, use /disconnect <area id>')
    elif len(args) == 1:
        try:
            connection = client.server.area_manager.get_area_by_id(int(args[0]))
            client.area.connections.remove(connection)
            client.send_ooc(f'Area disconnected from {connection.name}')
            for a in client.area.connections:
                if a.id == 0:
                    client.area.connections.remove(a)
            if len(client.area.connections) == 0:
                client.area.is_restricted = False
            if client in connection.owners:
                for a in connection.connections:
                    if a.id == 0:
                        connection.connections.remove(a)
                    if a == client.area:
                        connection.connections.remove(a)
                if len(connection.connections) == 0:
                    connection.is_restricted = False
        except ValueError:
            raise ArgumentError('Area ID must be a number.')
        except (AreaError, ClientError):
            raise
    else:
        raise ArgumentError('Too many arguments. Use /connect <area id>.')

def ooc_cmd_getarea(client, arg):
    """
    Show information about the current area.
    Usage: /getarea
    """
    client.send_area_info(client.area.id, False)


def ooc_cmd_getareas(client, arg):
    """
    Show information about all areas.
    Usage: /getareas
    """
    client.send_area_info(-1, False)


def ooc_cmd_lock(client, arg):
    """
    Prevent users from joining the current area.
    Usage: /lock <optional password>
    """
    if not client.area.locking_allowed:
        client.send_ooc('Area locking is disabled in this area.')
    elif client.area.is_locked == client.area.Locked.LOCKED:
        client.send_ooc('Area is already locked.')
    elif client in client.area.owners or client.is_mod:
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

def ooc_cmd_password(client, arg):
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
        
	
def ooc_cmd_unlock(client, arg):
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


def ooc_cmd_spectatable(client, arg):
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
		

def ooc_cmd_invite(client, arg):
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
        client.send_ooc('{} is invited to your area.'.format(
            c.char_name))
        c.send_ooc(
            f'You were invited and given access to {client.area.name}.')
        database.log_room('invite', client, client.area, target=c)
    except:
        raise ClientError('You must specify a target. Use /invite <id>')

def ooc_cmd_uninvite(client, arg):
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


def ooc_cmd_uninviteall(client, arg):
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

def ooc_cmd_iclock(client, arg):
    if len(arg) > 0:
        raise ArgumentError('This command takes no arguments.')
    if client.area.is_locked != client.area.Locked.FREE and client.area.is_locked != client.area.Locked.LOCKED:
	    return ooc_cmd_uninviteall(client, arg)
    if client not in client.area.owners and not client.is_mod:
        raise ClientError('You are not a CM.')
    else:
        if client.area.is_locked != client.area.Locked.LOCKED:
            client.area.spectator()
            client.area.invite_list = {}
        else:
            client.area.invite_list = {}
        for c in client.area.owners:
            client.area.invite_list[c.id] = None
        client.area.broadcast_ooc("IClock enabled.")

def ooc_cmd_areakick(client, arg):
    """
    Remove a user from the current area and move them to another area.
    Usage: /area_kick <id> [destination]
    """
    if client not in client.area.owners and not client.is_mod:
        raise ClientError('You must be a CM.')
    elif client.area.is_locked == client.area.Locked.FREE and not client.is_mod:
        raise ClientError('Area isn\'t locked.')
    elif not arg:
        raise ClientError('You must specify a target. Use /areakick <id> [destination #]')
    elif arg[0] == '*':
        targets = [c for c in client.area.clients if c != client and c != client.area.owners]
    else:
        targets = None
        arg = arg.split()
        if not client.is_mod and len(arg) > 1:
            raise ClientError('You must be a mod to kick people to a specific area.')
    if targets is None:
        try:
            targets = client.server.client_manager.get_targets(client, TargetType.ID, int(arg[0]), False)
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
                c.change_area(area)
                c.send_ooc(
                    f"You were kicked from the area to area {output}.")
                database.log_room('area_kick', client, client.area, target=c, message=output)
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
                database.log_room('area_kick', client, client.area, target=c, message=output)
                if client.area.is_locked != client.area.Locked.FREE:
                    client.area.invite_list.pop(c.id)
        except AreaError:
            raise
        except ClientError:
            raise
    else:
        client.send_ooc("No targets found.")
