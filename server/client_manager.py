# tsuserverCC, an Attorney Online server.
#
# Copyright (C) 2020 Kaiser <kaiserkaisie@gmail.com>
#
# Derivative of tsuserver3, an Attorney Online server. Copyright (C) 2016 argoneus <argoneuscze@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import re
import time
import random
from heapq import heappop, heappush

from server import database
from server.timer import Timer
from server.constants import TargetType
from server.exceptions import ClientError, AreaError


class ClientManager:
    """Holds the list of all clients currently connected to the server."""
    class Client:
        """Represents a single instance of a user.

        Clients may only belong to a single room.
        """
        def __init__(self, server, transport, user_id, ipid):
            self.is_checked = False
            self.transport = transport
            self.hdid = ''
            self.id = user_id
            self.char_id = -1
            self.area = server.area_manager.default_area()
            self.server = server
            self.name = ''
            self.showname = ''
            self.fake_name = ''
            self.is_mod = False
            self.mod_profile_name = None
            self.is_dj = True
            self.can_wtce = True
            self.pos = ''
            self.evi_list = []
            self.disemvowel = False
            self.shaken = False
            self.gimp = False
            self.charcurse = []
            self.muted_global = False
            self.muted_adverts = False
            self.is_muted = False
            self.is_ooc_muted = False
            self.pm_mute = False
            self.mod_call_time = 0
            self.ipid = ipid
            self.notepad = ''
            self.autopass = False
            self.followers = []
            self.following = []
            self.is_following = False
            self.followable = True
            self.is_hostage = False
            self.timer = Timer()
            self.old_char_name = ''
            self.permission = False
            self.ghost = False
            self.hidden = False
            self.in_party = False
            self.party = None
            self.partyrole = ''
            self.votepower = 0
            self.voted = False
            self.visible = True
            self.narrator = False
            self.offset = 0
            self.clientscon = 0
            self.friendlist = None
            self.friendrequests = set()
            self.areapair = 'middle'

            # Pairing stuff
            self.charid_pair = -1
            self.offset_pair = 0
            self.last_sprite = ''
            self.flip = 0
            self.claimed_folder = ''

            # Casing stuff
            self.casing_cm = False
            self.casing_cases = ''
            self.casing_def = False
            self.casing_pro = False
            self.casing_jud = False
            self.casing_jur = False
            self.casing_steno = False
            self.case_call_time = 0

            # flood-guard stuff
            self.mus_counter = 0
            self.mus_mute_time = 0
            self.mus_change_time = [
                x * self.server.config['music_change_floodguard']
                ['interval_length']
                for x in range(self.server.config['music_change_floodguard']
                               ['times_per_interval'])
            ]
            self.wtce_counter = 0
            self.wtce_mute_time = 0
            self.wtce_time = [
                x * self.server.config['wtce_floodguard']['interval_length']
                for x in range(self.server.config['wtce_floodguard']
                               ['times_per_interval'])
            ]

        def ann_alarm(self):
            if alarmtype == 'seconds':
                self.send_ooc(f'Alarm: {alarmtime:0.0f} seconds have passed.')
            if alarmtype == 'hours':
                self.send_ooc(f'Alarm: {alarmtime:0.0f} hours have passed.')
            if alarmtype == 'minutes':
                self.send_ooc(f'Alarm: {alarmtime:0.0f} minutes have passed.')
            self.timer.alarmset = False

        def send_raw_message(self, msg):
            """
            Send a raw packet over TCP.
            :param msg: string to send
            """
            self.transport.write(msg.encode('utf-8'))

        def send_command(self, command, *args):
            """
            Compose and send an AO-compatible message, with arguments
            delimited by `#` and ending with `#%`.
            :param command: command name
            :param *args: list of arguments
            """
            if args:
                if command == 'MS':
                    for evi_num in range(len(self.evi_list)):
                        if self.evi_list[evi_num] == args[11]:
                            lst = list(args)
                            lst[11] = evi_num
                            args = tuple(lst)
                            break
                self.send_raw_message(
                    f'{command}#{"#".join([str(x) for x in args])}#%')
            else:
                self.send_raw_message(f'{command}#%')

        def send_ooc(self, msg):
            """
            Send an out-of-character message to the client.
            :param msg: message to send
            """
            self.send_command('CT', self.server.config['hostname'], msg, '1')

        def send_poll(self):
            poll = 'There is currently no server poll running.'
            if self.server.poll != '':
                poll = self.server.poll
                yay = self.server.pollyay
                nay = self.server.pollnay
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
                    else:
                        poll += f'\n===================\nThere are currently {len(yay)} yays and {len(nay)} nays.\nThe yays and the nays are tied.'
                self.send_ooc(poll)
            else:
                self.send_ooc(poll)

        def send_motd(self):
            """Send the message of the day to the client."""
            motd = self.server.config['motd']
            self.send_ooc(f'=== MOTD ===\r\n{motd}\r\n=============')

        def send_player_count(self):
            """
            Send a message stating the number of players currently online
            to the client.
            """
            players = self.server.player_count
            limit = self.server.config['playerlimit']
            self.send_ooc(f'{players}/{limit} players online.')

        def is_valid_name(self, name):
            """
            Check if the given string is valid as an OOC name.
            :param name: name to check
            """
            name_ws = name.replace(' ', '')
            if not name_ws or name_ws.isdigit():
                return False
            for client in self.server.client_manager.clients:
                if client.name == name:
                    return False
            return True

        def disconnect(self):
            """Disconnect the client gracefully."""
            self.transport.close()

        def change_character(self, char_id, force=False, switch=False):
            """
            Change the client's character or force the character selection
            screen to appear for the client.
            :param char_id: character ID to switch to
            :param force: whether or not the client is forced to switch
            to another character if the target character is not available
            (Default value = False)
            """
            if not self.server.is_valid_char_id(char_id):
                raise ClientError('Invalid character ID.')
            if len(self.charcurse) > 0:
                if not char_id in self.charcurse:
                    raise ClientError('Character not available.')
                force = True
            if not self.area.is_char_available(char_id):
                if force:
                    for client in self.area.clients:
                        if client.char_id == char_id:
                            client.char_select()
                else:
                    raise ClientError('Character not available.')
            old_char = self.char_name
            self.char_id = char_id
            self.pos = ''
            self.send_command('PV', self.id, 'CID', self.char_id, switch)
            self.area.send_command('CharsCheck', *self.get_available_char_list())
            new_char = self.char_name
            database.log_room('char.change', self, self.area,
                message={'from': old_char, 'to': new_char})

        def change_music_cd(self):
            """
            Check if the client can change music or not.
            :returns: how many seconds the client must wait to change music
            """
            if self.is_mod or self in self.area.owners:
                return 0
            if self.mus_mute_time:
                if time.time() - self.mus_mute_time < self.server.config[
                        'music_change_floodguard']['mute_length']:
                    return self.server.config['music_change_floodguard'][
                        'mute_length'] - (time.time() - self.mus_mute_time)
                else:
                    self.mus_mute_time = 0
            times_per_interval = self.server.config['music_change_floodguard'][
                'times_per_interval']
            interval_length = self.server.config['music_change_floodguard'][
                'interval_length']
            if time.time() - self.mus_change_time[
                (self.mus_counter - times_per_interval + 1) %
                    times_per_interval] < interval_length:
                self.mus_mute_time = time.time()
                return self.server.config['music_change_floodguard'][
                    'mute_length']
            self.mus_counter = (self.mus_counter + 1) % times_per_interval
            self.mus_change_time[self.mus_counter] = time.time()
            return 0

        def wtce_mute(self):
            """
            Check if the client can use WT/CE or not.
            :returns: how many seconds the client must wait to use WT/CE
            """
            if self.is_mod or self in self.area.owners:
                return 0
            if self.wtce_mute_time:
                if time.time() - self.wtce_mute_time < self.server.config[
                        'wtce_floodguard']['mute_length']:
                    return self.server.config['wtce_floodguard'][
                        'mute_length'] - (time.time() - self.wtce_mute_time)
                else:
                    self.wtce_mute_time = 0
            times_per_interval = self.server.config['wtce_floodguard'][
                'times_per_interval']
            interval_length = self.server.config['wtce_floodguard'][
                'interval_length']
            if time.time() - self.wtce_time[
                (self.wtce_counter - times_per_interval + 1) %
                    times_per_interval] < interval_length:
                self.wtce_mute_time = time.time()
                return self.server.config['music_change_floodguard'][
                    'mute_length']
            self.wtce_counter = (self.wtce_counter + 1) % times_per_interval
            self.wtce_time[self.wtce_counter] = time.time()
            return 0

        def reload_character(self):
            """Reload the state of the current character."""
            try:
                self.change_character(self.char_id, True)
            except ClientError:
                raise

        def change_area(self, area):
            """
            Switch the client to another area, unless the area is locked.
            :param area: area to switch to
            """
            if self.area == area:
                raise ClientError('User already in specified area.')
            if self.is_hostage == True:
                for c in self.following:
                    if not c in area.clients:
                        raise ClientError('You cannot leave as long as you are a hostage!')
                    elif area.is_locked == area.Locked.LOCKED and not self.id in area.invite_list:
                        area.invite_list[self.id] = None
            if area.is_locked == area.Locked.LOCKED and not self.is_mod and not self.id in area.invite_list:
                if area.password != '':
                    self.send_command('AP', area)
                    raise ClientError('That area is locked with a password! Use /area <id> <password> to enter.')
                else:
                    raise ClientError('That area is locked!')
            if area.is_locked == area.Locked.SPECTATABLE and not self.is_mod and not self.id in area.invite_list:
                self.send_ooc('This area is spectatable, but not free - you cannot talk in-character unless invited.')
            if self.is_following == True:
                for c in self.following:
                    if not c in area.clients:
                        self.is_following = False
                        c.followers.remove(self)
                        c.send_ooc(f'{self.char_name} left the area and is no longer following you.')
                        self.send_ooc(f'You left the area and are no longer following {c.char_name}.')
                        self.following.remove(c)
            if not self.is_mod and self.area.is_restricted == True:
                found = 'false'
                for connection in self.area.connections:
                    if connection == area or self in self.area.owners:
                        found = 'true'
                if found != 'true':
                    raise ClientError('That area is not connected to your current area!')

            if self.area.jukebox:
                self.area.remove_jukebox_vote(self, True)

            old_area = self.area
            if not area.is_char_available(self.char_id):
                try:
                    new_char_id = area.get_rand_avail_char_id()
                except AreaError:
                    if self.is_following == True:
                        self.is_following = False
                        for c in self.following:
                            c.send_ooc(f'No available characters in {area.name} for {self.char_name} so they cannot follow you any longer.')
                            c.followers.remove(self)
                            self.following.remove(c)
                        raise ClientError(f'No available characters in {area.name}, cannot follow {self.char_name}. Unfollowing.')
                    else:
                        raise ClientError('No available characters in that area.')
            if self.autopass == True:
                if self.is_following:
                    for c in self.following:
                        if self.char_name.startswith('custom') and self.showname != 0:
                            if c.char_name.startswith('custom') and c.showname != 0:
                                self.area.broadcast_ooc(f'{self.showname} has followed {c.showname} to {area.name}.')
                            else:
                                self.area.broadcast_ooc(f'{self.showname} has followed {c.char_name} to {area.name}.')
                        else:
                            if c.char_name.startswith('custom') and c.showname != 0:
                                self.area.broadcast_ooc(f'{self.char_name} has followed {c.showname} to {area.name}.')
                            else:
                                self.area.broadcast_ooc(f'{self.char_name} has followed {c.char_name} to {area.name}.')
                else:
                    if self.char_name.startswith('custom') and self.showname != 0:
                        self.area.broadcast_ooc(f'{self.showname} has left to {area.name}.')
                    else:
                        self.area.broadcast_ooc(f'{self.char_name} has left to {area.name}.')
            if len(self.followers) > 0:
                for c in self.followers:
                    if area.is_locked == area.Locked.LOCKED and not c.is_mod and not c.is_hostage and not c.id in area.invite_list:
                        c.send_ooc(f'Cannot follow {self.char_name} to {area.name}. Unfollowing.')
                        self.send_ooc(f'{c.char_name} cannot enter that area and is no longer following you.')
                        c.is_following = False
                        c.following.remove(self)
                        self.followers.remove(c)
                    elif not area.is_char_available(c.char_id):
                        try:
                            follow_char_id = area.get_rand_avail_char_id()
                        except AreaError:
                            c.send_ooc(f'No available characters in {area.name}, cannot follow {self.char_name}. Unfollowing.')
                            c.is_following = False
                            c.following.remove(self)
                            self.followers.remove(c)
                            self.send_ooc(f'No available characters in {area.name} for {c.char_name} so they cannot follow you any longer.')
            self.old_char_name = self.char_name
            if not area.is_char_available(self.char_id):
                self.change_character(new_char_id)
                self.send_ooc(
                    f'Character taken, switched to {self.char_name}.')

            self.area.remove_client(self)
            self.area = area
            area.new_client(self)

            self.send_ooc(f'Changed area to {area.name} [{self.area.status}].')
            if self.autopass == True:
                if self.is_following:
                    for c in self.following:
                        if self.char_name.startswith('custom') and self.showname != 0:
                            if c.char_name.startswith('custom') and c.showname != 0:
                                self.area.broadcast_ooc(f'{self.showname} has followed {c.showname} from {old_area.name}.')
                            else:
                                self.area.broadcast_ooc(f'{self.showname} has followed {c.char_name} from {old_area.name}.')
                        else:
                            if c.char_name.startswith('custom') and c.showname != 0:
                                self.area.broadcast_ooc(f'{self.char_name} has followed {c.showname} from {old_area.name}.')
                            else:
                                self.area.broadcast_ooc(f'{self.char_name} has followed {c.char_name} from {old_area.name}.')
                else:
                    if self.char_name.startswith('custom') and self.showname != 0:
                        self.area.broadcast_ooc(f'{self.showname} has entered from {old_area.name}.')
                    else:
                        self.area.broadcast_ooc(f'{self.char_name} has entered from {old_area.name}.')
            for c in self.followers:
                c.change_area(area)
            self.area.send_command('CharsCheck', *self.get_available_char_list())
            self.send_command('HP', 1, self.area.hp_def)
            self.send_command('HP', 2, self.area.hp_pro)
            self.send_command('BN', self.area.background)
            self.send_command('LE', *self.area.get_evidence_list(self))

        def send_area_list(self):
            """Send a list of areas over OOC."""
            msg = '=== Areas ==='
            for _, area in enumerate(self.server.area_manager.areas):
                owner = 'FREE'
                if len(area.owners) > 0:
                    owner = f'CMs: {area.get_cms()}'
                lock = {
                    area.Locked.FREE: '',
                    area.Locked.SPECTATABLE: '[SPECTATABLE]',
                    area.Locked.LOCKED: '[LOCKED]'
                }
                msg += f'\r\nArea {area.abbreviation}: {area.name} (users: {len(area.clients)}) [{area.status}][{owner}]{lock[area.is_locked]}'
                if self.area == area:
                    msg += ' [*]'
            self.send_ooc(msg)

        def get_area_info(self, area_id, mods):
            """
            Get information about a specific area.
            :param area_id: area ID
            :param mods: limit player list to mods
            :returns: information as a string
            """
            info = '\r\n'
            try:
                area = self.server.area_manager.get_area_by_id(area_id)
            except AreaError:
                raise
            info += f'=== {area.name} ==='
            info += '\r\n'

            lock = {
                area.Locked.FREE: '',
                area.Locked.SPECTATABLE: '[SPECTATABLE]',
                area.Locked.LOCKED: '[LOCKED]'
            }

            if self not in area.owners and self not in area.clients and not self.is_mod and area.hidden == True:
                info += f'[{area.abbreviation}]: [Hidden][{area.status}]{lock[area.is_locked]}'
                info += '\r\n'
                info += 'This area\'s playercount is hidden.'
            else:
                index = 0
                for client in area.clients:
                    if not client.ghost and not client.hidden:
                        index += 1
                info += f'[{area.abbreviation}]: [{index} Users][{area.status}]{lock[area.is_locked]}'
                sorted_clients = []
                for client in area.clients:
                    if self.is_mod:
                        if (not mods) or client.is_mod:
                            sorted_clients.append(client)
                    elif self in area.owners and not client.ghost and client.hidden:
                        if (not mods) or client.is_mod:
                            sorted_clients.append(client)
                    elif self == client and client.hidden:
                        if (not mods) or client.is_mod:
                            sorted_clients.append(client)
                    elif not self.is_mod and not client.ghost and not client.hidden:
                        if (not mods) or client.is_mod:
                            sorted_clients.append(client)
                for owner in area.owners:
                    if not (mods or owner in area.clients):
                        sorted_clients.append(owner)
                if not sorted_clients:
                    return ''
                sorted_clients = sorted(sorted_clients,
                                    key=lambda x: x.char_name or '')
                for c in sorted_clients:
                    info += '\r\n'
                    if c.hidden and self in area.owners:
                        info += '[Hidden]'
                    elif c.hidden and self == c:
                        info += '[Hidden]'
                    elif c.hidden and self.is_mod:
                        info += '[Hidden]'
                    if c in area.owners:
                        if not c in area.clients:
                            info += '[RCM]'
                        else:
                            info += '[CM]'
                    info += f'[{c.id}] {c.char_name}'
                    if self.is_mod:
                        info += f' ({c.ipid}): {c.name}'
                    if c.showname != '':
                        info += f' ({c.showname})'
                    

            return info

        def send_area_info(self, area_id, mods):
            """
            Send information over OOC about a specific area.
            :param area_id: area ID
            :param mods: limit player list to mods
            """
            # if area_id is -1 then return all areas. If mods is True then return only mods
            info = ''
            if area_id == -1:
                # all areas info
                cnt = 0
                info = '\n== Area List =='
                for i in range(len(self.server.area_manager.areas)):
                    if len(self.server.area_manager.areas[i].clients) > 0 or len(self.server.area_manager.areas[i].owners) > 0:
                        for client in self.server.area_manager.areas[i].clients:
                            if self.is_mod:
                                cnt += 1
                            elif self in self.server.area_manager.areas[i].owners and not client.ghost:
                                cnt += 1
                            elif self == client and client.hidden:
                                cnt += 1
                            elif not client.ghost and not client.hidden:
                                cnt += 1
                        info += f'{self.get_area_info(i, mods)}'
                info = f'Current online: {cnt}{info}'
            else:
                try:
                    area_client_cnt = 0
                    for client in self.server.area_manager.areas[area_id].clients:
                        if self.is_mod:
                            area_client_cnt += 1
                        elif self in self.server.area_manager.areas[area_id].owners and not client.ghost:
                            area_client_cnt += 1
                        elif self == client and client.hidden:
                            area_client_cnt += 1
                        elif not client.ghost and not client.hidden:
                            area_client_cnt += 1
                    info = f'People in this area: {area_client_cnt}'
                    info += self.get_area_info(area_id, mods)

                except AreaError:
                    raise
            self.send_ooc(info)

        def send_done(self):
            """
            Send area information and finish the join handshake.
            This unconditionally causes the client to show the character
            selection screen, even if the client has already joined.
            """
            self.send_command('CharsCheck', *self.get_available_char_list())
            self.send_command('HP', 1, self.area.hp_def)
            self.send_command('HP', 2, self.area.hp_pro)
            self.send_command('BN', self.area.background)
            self.send_command('LE', *self.area.get_evidence_list(self))
            self.send_command('MM', 1)

            self.server.area_manager.send_arup_players()
            self.server.area_manager.send_arup_status()
            self.server.area_manager.send_arup_cms()
            self.server.area_manager.send_arup_lock()

            self.send_command('DONE')

        def char_select(self):
            """Force the client to select a different character."""
            self.char_id = -1
            self.send_done()

        def get_available_char_list(self):
            """Get a list of character IDs that the client can select."""
            if len(self.charcurse) > 0:
                avail_char_ids = set(range(len(
                    self.server.char_list))) and set(self.charcurse)
            else:
                avail_char_ids = set(range(len(self.server.char_list))) - {
                    x.char_id
                    for x in self.area.clients
                }
            char_list = [-1] * len(self.server.char_list)
            for x in avail_char_ids:
                char_list[x] = 0
            return char_list

        def auth_mod(self, password):
            """
            Attempt to log in as a moderator.
            :param password: password string
            :returns: name of profile which the password belongs to, if login
            was successful
            :raises: ClientError if password is incorrect
            """
            modpasses = self.server.config['modpass']
            if isinstance(modpasses, dict):
                matches = [k for k in modpasses
                    if modpasses[k]['password'] == password]
            elif modpasses == password:
                matches = ['default']
            else:
                matches = []

            if self.is_mod:
                raise ClientError('Already logged in.')
            elif len(matches) > 0:
                self.is_mod = True
                self.mod_profile_name = matches[0]
                return self.mod_profile_name
            else:
                self.send_command("FAILEDLOGIN");
                raise ClientError('Invalid password.')

        @property
        def ip(self):
            """Get an anonymized version of the IP address."""
            return self.ipid

        @property
        def char_name(self):
            """Get the name of the character that the client is using."""
            if self.char_id == -1:
                return None
            return self.server.char_list[self.char_id]

        def change_position(self, pos=''):
            """
            Change the character's current position in the area.
            :param pos: position in area (Default value = '')
            """
            positions = ('def', 'pro', 'hld', 'hlp', 'jud', 'wit', 'jur', 'sea')
            if pos not in positions and pos != '':
                raise ClientError(
                    f'Invalid position. Possible values: {", ".join(positions)}'
                )
            self.pos = pos

        def set_mod_call_delay(self):
            """Begin the mod call cooldown."""
            self.mod_call_time = round(time.time() * 1000.0 + 30000)

        def can_call_mod(self):
            """Whether or not the client can currently call mod."""
            return (time.time() * 1000.0 - self.mod_call_time) > 0

        def set_case_call_delay(self):
            """Begin the case announcement cooldown."""
            self.case_call_time = round(time.time() * 1000.0 + 60000)

        def can_call_case(self):
            """Whether or not the client can currently announce a case."""
            return (time.time() * 1000.0 - self.case_call_time) > 0

        def disemvowel_message(self, message):
            """Disemvowel a chat message."""
            message = re.sub('[aeiou]', '', message, flags=re.IGNORECASE)
            return re.sub(r'\s+', ' ', message)

        def shake_message(self, message):
            """Mix the words in a chat message."""
            import random
            parts = message.split()
            random.shuffle(parts)
            return ' '.join(parts)

        def gimp_message(self, message):
            message = self.server.gimp_list
            return random.choice(message)

    def __init__(self, server):
        self.clients = set()
        self.server = server
        self.cur_id = [i for i in range(self.server.config['playerlimit'])]

    def new_client_preauth(self, client):
        maxclients = self.server.config['multiclient_limit']
        for c in self.server.client_manager.clients:
            if c.ipid == client.ipid:
                if c.clientscon > maxclients:
                    return False
        return True

    def new_client(self, transport):
        """
        Create a new client, add it to the list, and assign it a player ID.
        :param transport: asyncio transport
        """
        try:
            user_id = heappop(self.cur_id)
        except IndexError:
            transport.write(b'BD#This server is full.#%')
            raise ClientError
        c = self.Client(
            self.server, transport, user_id,
            database.ipid(transport.get_extra_info('peername')[0]))
        self.clients.add(c)
        temp_ipid = c.ipid
        for client in self.server.client_manager.clients:
            if client.ipid == temp_ipid:
                client.clientscon += 1
        self.server.friend_manager.new_friendlist(c)
        return c

    def remove_client(self, client):
        """
        Remove a disconnected client from the client list.
        :param client: disconnected client
        """
        if client.area.jukebox:
            client.area.remove_jukebox_vote(client, True)
        for a in self.server.area_manager.areas:
            if client in a.owners:
                a.owners.remove(client)
                client.server.area_manager.send_arup_cms()
                if len(a.owners) == 0:
                    if a.is_locked != a.Locked.FREE:
                        a.unlock()
                    if client.area.is_restricted:
                        client.area.is_restricted = False
                        client.area.connections.clear()
            if len(client.area.clients) <= 1:
                if client.area.is_locked != client.area.Locked.FREE:
                    client.area.unlock()
        for c in client.following:
            c.followers.remove(client)
            c.send_ooc(f'{client.char_name} disconnected and is no longer following you.')
        for b in client.followers:
            b.following.remove(self)
            b.is_following = False
            b.send_ooc(f'{client.char_name} disconnected. Unfollowing.')
        if client.in_party:
            party = client.party
            if len(party.users) != 0 and client in party.users:
                party.users.remove(client)
                for member in party.users:
                    member.send_ooc(f'{client.name} disconnected and left the party.')
            if party.leader == client and len(party.users) != 0:
                for member in party.users:
                    member.send_ooc(f'{client.name} disconnected and left the party.')
                    if party.leader not in party.users:
                        party.leader = member
                        member.send_ooc('Party Leader left, you are now the new Party Leader.')
                    else:
                        member.send_ooc(f'Party Leader left, {party.leader.name} is the new Party Leader.')
            if len(party.users) == 0:
                client.server.parties.remove(party)
        if client.friendlist != None:
            self.server.friend_manager.friendlists.remove(client.friendlist)
        heappush(self.cur_id, client.id)
        self.clients.remove(client)

    def get_targets(self, client, key, value, local=False, single=False):
        """
        Find players by a combination of identifying data.
        Possible keys: player ID, OOC name, character name, HDID, IPID,
        IP address (same as IPID)

        :param client: client
        :param key: the type of identifier that `value` represents
        :param value: data identifying a client
        :param local: search in current area only (Default value = False)
        :param single: search only a single user (Default value = False)
        """
        areas = None
        if local:
            areas = [client.area]
        else:
            areas = client.server.area_manager.areas
        targets = []
        if key == TargetType.ALL:
            for nkey in range(6):
                targets += self.get_targets(client, nkey, value, local)
        for area in areas:
            for client in area.clients:
                if key == TargetType.IP:
                    if value.lower().startswith(client.ip.lower()):
                        targets.append(client)
                elif key == TargetType.OOC_NAME:
                    if value.lower().startswith(
                            client.name.lower()) and client.name:
                        targets.append(client)
                elif key == TargetType.CHAR_NAME:
                    if value.lower().startswith(
                            client.char_name.lower()):
                        targets.append(client)
                elif key == TargetType.ID:
                    if client.id == value:
                        targets.append(client)
                elif key == TargetType.IPID:
                    if client.ipid == value:
                        targets.append(client)
        return targets

    def get_muted_clients(self):
        """Get a list of muted clients."""
        clients = []
        for client in self.clients:
            if client.is_muted:
                clients.append(client)
        return clients

    def get_ooc_muted_clients(self):
        """Get a list of OOC-muted clients."""
        clients = []
        for client in self.clients:
            if client.is_ooc_muted:
                clients.append(client)
        return clients
