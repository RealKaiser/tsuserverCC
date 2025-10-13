"""
tsuserverCC, an Attorney Online server.
Copyright (C) 2022 Kaiser <kaiserkaisie@gmail.com>

Derivative of tsuserverOLE, an Attorney Online server.
Copyright (C) 2021 KillerSteel <killermagnum5@gmail.com

Derivative of tsuserverCC, an Attorney Online server.
Copyright (C) 2020 Kaiser <kaiserkaisie@gmail.com>

Derivative of tsuserver3, an Attorney Online server. 
Copyright (C) 2016 argoneus <argoneuscze@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.
 
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.
 
You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import yaml
import os
import re
import time
import random
import asyncio
from datetime import datetime

from heapq import heappop, heappush
from yaml.loader import FullLoader

from server import database
from server.webhooks import Webhooks
from server.constants import TargetType
from server.exceptions import ClientError, AreaError
from server.constants import MusicEffect


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
            self.is_dj = True
            self.can_wtce = True
            self.pos = ''
            self.evi_list = []
            self.charcurse = []
            self.muted_global = False
            self.muted_adverts = False
            self.is_muted = False
            self.is_ooc_muted = False
            self.pm_mute = False
            self.mod_call_time = 0
            self.ipid = ipid
            self.autopass = False
            self.old_char_name = ''
            self.ooc_delay = None
            self.afk = False
            self.afktime = None
            self.listen = True
            self.ambiance = ''
            self.current_music = ''
            self.files = ''
            self.hidden = False
            self.hubview = False
            self.pid = -1
            self.is_wlisted = False
            self.discord_name = ''
            self.wlrequest = False
            
            # Mod/Admin stuff
            self.is_admin = False
            self.is_mod = False
            self.mod_profile_name = None
            self.ghost = False
            self.spying = []
            
            # Misc. IC stuff
            self.visible = True
            self.narrator = False
            self.disemvowel = False
            self.shaken = False
            self.gimp = False
            
            # Call stuff
            self.call = None
            self.calling = []
            self.incall = False
            
            # Area movement time stuff
            self.moveto = None
            self.movetimer = 0
            
            # Following stuff
            self.followers = []
            self.following = []
            self.is_following = False
            self.followable = True
            self.is_hostage = False

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
            
            # Security/Multiclient stuff
            self.clientscon = 0

            # Security/Multiclient stuff
            self.hand = []


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

        def send_ooc(self, msg: str) -> None:
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
                    if len(nay) == len(yay):
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

        def is_valid_name(self, name: str) -> bool:
            """
            Check if the given string is valid as an OOC name.
            :param name: name to check
            """
            name_ws = name.replace(' ', '')
            if not name_ws or name_ws.isdigit():
                return False
            for client in self.server.client_manager.clients:
                if client.name == name and self.ipid != client.ipid:
                    return False
            return True

        def disconnect(self):
            """Disconnect the client gracefully."""
            self.transport.close()

        def change_character(
            self, char_id: str, 
            force: bool = False, 
            switch: bool = False) -> None:
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
            """if not self.area.is_char_available(char_id):
                if force:
                    for client in self.area.clients:
                        if client.char_id == char_id:
                            client.char_select()
                else:
                    raise ClientError('Character not available.')"""
            old_char = self.char_name
            self.char_id = char_id
            self.pos = ''
            self.send_command('PV', self.id, 'CID', self.char_id, switch)
            self.send_command('SP', self.pos) #Send a "Set Position" packet
            self.area.send_command('CharsCheck', *self.get_available_char_list())
            new_char = self.char_name
            database.log_room('char.change', self, self.area,
                message={'from': old_char, 'to': new_char})
            if self.ambiance != self.area.ambiance:
                self.ambiance = self.area.ambiance
                self.send_command("MC", self.area.ambiance, -1, "", 1, 1, int(MusicEffect.FADE_OUT),)
            if not self.area.loop:
                if self.current_music != self.area.current_music:
                    self.send_command("MC", self.area.current_music, -1, "", 1, 0, int(MusicEffect.FADE_OUT),)
                    self.current_music = self.area.current_music
            if self.afk:
                self.server.client_manager.toggle_afk(self)
            if self.server.config['afk_delay'] > 0:
                if self.afktime:
                    self.afktime.cancel()
                self.afktime = asyncio.get_event_loop().call_later(self.server.config['afk_delay'], lambda: self.server.client_manager.toggle_afk(self))

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
                    if area.is_locked == area.Locked.LOCKED and not self.id in area.invite_list:
                        area.invite_list[self.id] = None
            #Add id to invite list if they are an area owner so they can actually enter. Why is this a dictionary again?
            if self in area.owners and not self.id in area.invite_list:
                area.invite_list[self.id] = None
            if area.is_locked == area.Locked.LOCKED and not self.is_mod and not self.id in area.invite_list:
                if area.password != '':
                    self.send_command('AP', area.id)
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
            if area.timetomove > 0:
                if not self.is_mod and not self.is_following and self not in area.owners:
                    if area.sub and not self.area.is_hub and self not in area.hub.owners:
                        if self.moveto != area:
                            self.moveto = area
                            self.movetimer = time.perf_counter() + area.timetomove
                            raise ClientError(f'Destination confirmed, wait for {area.timetomove} seconds to move to that area.')
                        else:
                            now = time.perf_counter()
                            if now < self.movetimer:
                                left = int(self.movetimer - now)
                                raise ClientError(f'You still need to wait {left} seconds to move there.')

            self.moveto = None
            self.movetimer = 0
            
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
                        if self.showname != 0:
                            if c.showname != 0:
                                self.area.broadcast_ooc(f'{self.showname}-({self.char_name}) has followed {c.showname}-({c.char_name}) to {area.name}.')
                            else:
                                self.area.broadcast_ooc(f'{self.showname}-({self.char_name}) has followed {c.char_name} to {area.name}.')
                        else:
                            if c.showname != 0:
                                self.area.broadcast_ooc(f'{self.char_name} has followed {c.showname}-({c.char_name}) to {area.name}.')
                            else:
                                self.area.broadcast_ooc(f'{self.char_name} has followed {c.char_name} to {area.name}.')
                else:
                    if self.showname != 0:
                        self.area.broadcast_ooc(f'{self.showname} ({self.char_name}) has left to {area.name}.')
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
            
            if old_area.sub and len(old_area.clients) == 0 and len(old_area.owners) == 0:
                if old_area.hub.hubtype == 'user':
                    self.server.hub_manager.removesub(self, old_area)
                    self.send_ooc('Old area was destroyed')
            
            lobby = self.server.area_manager.default_area()
            
            if self.area.is_hub and not old_area.sub or self.area.is_hub and old_area.is_restricted:
                area_list = []
                area_list.append(lobby.name)
                area_list.append(area.name)
                for a in self.area.subareas:
                    area_list.append(a.name)
                self.send_command('FA', *area_list)
                self.area.sub_arup_cms(self)
                self.area.sub_arup_status(self)
                self.area.sub_arup_lock(self)
            if old_area.is_hub or old_area.sub:
                if not self.area.sub and not self.area.is_hub:
                    area_list = []
                    for a in self.server.area_manager.areas:
                        area_list.append(a.name)
                    self.send_command('FA', *area_list)
                    self.server.area_manager.send_arup_cms(self)
                    self.server.area_manager.send_arup_status(self)
                    self.server.area_manager.send_arup_lock(self)
                    if old_area.is_hub:
                        old_area.sub_arup_players()
                    else:
                        if old_area.is_restricted:
                            old_area.hub.sub_arup_players()
            if self.area.sub and self.area.is_restricted:
                if not self in self.area.hub.owners:
                    area_list = []
                    area_list.append(lobby.name)
                    area_list.append(area.hub.name)
                    area_list.append(area.name)
                    for conn in area.connections:
                        if conn != lobby and conn != area.hub:
                            area_list.append(conn.name)
                    self.send_command('FA', *area_list)
                    self.area.conn_arup_cms()
                    self.area.conn_arup_status()
                    self.area.conn_arup_lock()
            if self.area.sub and not self.area.is_restricted and old_area.is_restricted:
                area_list = []
                area_list.append(lobby.name)
                area_list.append(area.hub.name)
                for a in self.area.hub.subareas:
                    area_list.append(a.name)
                self.send_command('FA', *area_list)
                self.area.hub.sub_arup_cms(self)
                self.area.hub.sub_arup_status(self)
                self.area.hub.sub_arup_lock(self)
            if old_area.cmusic_list != area.cmusic_list:
                music = area.get_music(self)
                self.send_command('FM', *music)
            if not self.area.is_hub and not self.area.sub:
                if self.hidden:
                    self.hidden = False
                    self.send_ooc('You are no longer hidden.')
            elif old_area.sub:
                if self.area.sub and self.area.hub != old_area.hub:
                    if self.hidden:
                        self.hidden = False
                        self.send_ooc('You are no longer hidden.')
                if self.area.is_hub and old_area.hub != self.area:
                    if self.hidden:
                        self.hidden = False
                        self.send_ooc('You are no longer hidden.')
            elif old_area.is_hub:
                if self.area.sub and self.area.hub != old_area:
                    if self.hidden:
                        self.hidden = False
                        self.send_ooc('You are no longer hidden.')
                if self.area.is_hub and self.area != old_area:
                    if self.hidden:
                        self.hidden = False
                        self.send_ooc('You are no longer hidden.')
            
            if area.sub:
                for othersub in area.hub.subareas:
                    if othersub.is_restricted:
                        if area in othersub.connections:
                            othersub.conn_arup_players()
                if area.is_restricted:
                    area.conn_arup_players()
                area.hub.sub_arup_players()
            elif area.is_hub:
                for sub in area.subareas:
                    if sub.is_restricted:
                        sub.conn_arup_players()
                area.sub_arup_players()
                if not old_area.sub:
                    self.server.area_manager.send_arup_players()
            else:
                self.server.area_manager.send_arup_players()

            self.send_ooc(f'Changed area to {area.name} [{self.area.status}].')
            if self.autopass == True:
                if self.is_following:
                    for c in self.following:
                        if self.showname != 0:
                            if c.showname != 0:
                                self.area.broadcast_ooc(f'{self.showname}-({self.char_name}) has followed {c.showname}-({c.char_name}) from {old_area.name}.')
                            else:
                                self.area.broadcast_ooc(f'{self.showname}-({self.char_name}) has followed {c.char_name} from {old_area.name}.')
                        else:
                            if c.showname != 0:
                                self.area.broadcast_ooc(f'{self.char_name} has followed {c.showname}-({c.char_name}) from {old_area.name}.')
                            else:
                                self.area.broadcast_ooc(f'{self.char_name} has followed {c.char_name} from {old_area.name}.')
                else:
                    if self.showname != 0:
                        self.area.broadcast_ooc(f'{self.showname} ({self.char_name}) has entered from {old_area.name}.')
                    else:
                        self.area.broadcast_ooc(f'{self.char_name} has entered from {old_area.name}.')
            for c in self.followers:
                c.change_area(area)
            self.area.send_command('CharsCheck', *self.get_available_char_list())
            self.send_command('HP', 1, self.area.hp_def)
            self.send_command('HP', 2, self.area.hp_pro)
            self.send_command('BN', self.area.background, self.pos)
            self.send_command('LE', *self.area.get_evidence_list(self))
            if self.afk:
                self.server.client_manager.toggle_afk(self)
            if self.afktime:
                self.afktime.cancel()
            if self.server.config['afk_delay'] > 0:
                self.afktime = asyncio.get_event_loop().call_later(self.server.config['afk_delay'], lambda: self.server.client_manager.toggle_afk(self))

        def send_self_arup(self, args):
            """Update the area properties for 2.6 clients.
            
            Playercount:
                ARUP#0#<area1_p: int>#<area2_p: int>#...
            Status:
                ARUP#1##<area1_s: string>##<area2_s: string>#...
            CM:
                ARUP#2##<area1_cm: string>##<area2_cm: string>#...
            Lockedness:
                ARUP#3##<area1_l: string>##<area2_l: string>#...


            :param args: 

            """
            if len(args) < 2:
                # An argument count smaller than 2 means we only got the identifier of ARUP.
                return
            if args[0] not in (0, 1, 2, 3):
                return

            if args[0] == 0:
                for part_arg in args[1:]:
                    try:
                        _sanitised = int(part_arg)
                    except:
                        return
            elif args[0] in (1, 2, 3, 4):
                for part_arg in args[1:]:
                    try:
                        _sanitised = str(part_arg)
                    except:
                        return
            self.send_command('ARUP', *args)

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

        def get_area_info(self, a, hubs: bool = False) -> str:
            """
            Get information about a specific area.
            :param area_id: area ID
            :param mods: limit player list to mods
            :returns: information as a string
            """
            selfarea = self.area
            area = a
            info = '\r\n'
            info += f'=== {area.name} ==='
            info += '\r\n'

            lock = {
                area.Locked.FREE: '',
                area.Locked.SPECTATABLE: '[SPECTATABLE]',
                area.Locked.LOCKED: '[LOCKED]'
            }

            if (
            self not in area.owners 
            and self not in area.clients and not 
            self.is_mod and area.hidden
              ):
                info += f'[{area.abbreviation}]: [Hidden][{area.status}]{lock[area.is_locked]}'
                info += '\r\n'
                info += 'This area\'s playercount is hidden.'
            else:
                index = 0
                for client in area.clients:
                    if not client.ghost and not client.hidden:
                        index += 1
                if area.is_hub and len(area.subareas) > 0:
                    if not selfarea.is_hub and not selfarea.sub:
                        for sub in area.subareas:
                            if len(sub.clients) > 0:
                                for client in sub.clients:
                                    if not client.ghost and not client.hidden:
                                        index += 1
                info += f'[{area.abbreviation}]: [{index} Users][{area.status}]{lock[area.is_locked]}'
                sorted_clients = [] 
                for client in area.clients:
                    if self.is_mod:
                        sorted_clients.append(client)
                    elif self in area.owners and not client.ghost and client.hidden:
                        sorted_clients.append(client)
                    elif self == client and client.hidden:
                        sorted_clients.append(client)
                    elif not client.ghost and not client.hidden:
                        sorted_clients.append(client)
                for owner in area.owners:
                    if not owner in area.clients:
                        if not owner.ghost or self.is_mod:
                            sorted_clients.append(owner)
                if area.is_hub and not selfarea.is_hub and not selfarea.sub or hubs:
                    if len(area.subareas) > 0:
                        for sub in area.subareas:
                            for client in sub.clients:
                                if self.is_mod:
                                    sorted_clients.append(client)
                                elif self in area.owners and not client.ghost and client.hidden:
                                    sorted_clients.append(client)
                                elif self == client and client.hidden:
                                    sorted_clients.append(client)
                                elif not self.is_mod and not client.ghost and not client.hidden:
                                    sorted_clients.append(client)
                if not sorted_clients:
                    return ''
                sorted_clients = sorted(sorted_clients, key=lambda x: x.char_name or '')
                for c in sorted_clients:
                    info += '\r\n'
                    if c.hidden and self in area.owners:
                        info += '[Hidden]'
                    elif c.hidden and self == c:
                        info += '[Hidden]'
                    elif c.hidden and self.is_mod:
                        info += '[Hidden]'
                    if c in area.owners:
                        if not c in area.clients and not area.is_hub:
                            info += '[RCM]'
                        else:
                            info += '[CM]'
                    if c.is_mod:
                        info += '[M]'

                    info += f'[{c.id}] {c.char_name}'
                    if c.is_wlisted:
                        info += f" [Disc: {c.discord_name}]"
                     
                    if self.is_mod:
                        info += f' ({c.ipid}): {c.name}'

                    if c.showname != '':
                        info += f' ({c.showname})'
                    
                    if c.afk:
                        info += ' [AFK]'

            return info
            
        def send_server_bgs(self) -> list:
            """
            Sends a list of the backgrounds available in the server.
            
            Checks if the backgrounds.yaml exists. If so, parses
            the yaml and returns a list. 

            This class method does NOT take any arguments and
            it's intended to be used as a helper for the function
            send_ooc_bgslist in area.py.

            """
            if os.path.exists('config/backgrounds.yaml'):
                with open('config/backgrounds.yaml') as b:
                    bgs = yaml.load(b, Loader = yaml.FullLoader)
                    return bgs
                        
        def send_area_info(self, area, all, hubs=False, multiclients=False):
            """
            Send information over OOC about a specific area.
            :param area_id: area ID
            :param mods: limit player list to mods
            """
            info = ''
            if all and not multiclients:
                # all areas info
                cnt = 0
                info = '\n== Area List =='
                for a in self.server.area_manager.areas:
                    for client in a.clients:
                        if self.is_mod:
                            cnt += 1
                        elif self in a.owners and not client.ghost:
                            cnt += 1
                        elif self == client and client.hidden:
                            cnt += 1
                        elif not client.ghost and not client.hidden:
                            cnt += 1
                    if a.is_hub and len(a.subareas) > 0:
                        for sub in a.subareas:
                            if len(sub.clients) > 0:
                                for client in sub.clients:
                                    if self.is_mod:
                                        cnt += 1
                                    elif self in sub.owners and not client.ghost:
                                        cnt += 1
                                    elif self == client and client.hidden:
                                        cnt += 1
                                    elif not client.ghost and not client.hidden:
                                        cnt += 1
                    if not area.is_hub and not area.sub or hubs:
                        info += f'{self.get_area_info(a, hubs)}'
                if area.is_hub and not hubs or area.sub and not hubs:
                    if area.is_hub:
                        info += f'{self.get_area_info(self.server.area_manager.default_area())}'
                        info += f'{self.get_area_info(area)}'
                        for sub in area.subareas:
                            info += f'{self.get_area_info(sub)}'
                    else:
                        info += f'{self.get_area_info(self.server.area_manager.default_area())}'
                        info += f'{self.get_area_info(area.hub)}'
                        for sub in area.hub.subareas:
                            info += f'{self.get_area_info(sub)}'
                info = f'Current online: {cnt}{info}'
            if not all and not multiclients:
                try:
                    area_client_cnt = 0
                    for client in area.clients:
                        if self.is_mod:
                            area_client_cnt += 1
                        elif self in area.owners and not client.ghost:
                            area_client_cnt += 1
                        elif self == client and client.hidden:
                            area_client_cnt += 1
                        elif not client.ghost and not client.hidden:
                            area_client_cnt += 1
                    info = f'People in this area: {area_client_cnt}'
                    info += self.get_area_info(area)

                except AreaError:
                    raise
            if not all and multiclients:
                checked = []
                cnt = 0
                for client in self.server.client_manager.clients:
                    if client in checked:
                        continue
                    for client2 in self.server.client_manager.clients:
                        if client != client2 and client.ipid == client2.ipid:
                            cnt += 1
                            checked.append(client2)
                    checked.append(client)
                    checked.append(client2)
                info = f'Current multiclients: {cnt}'
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
        def whitelist_trust(self):
            """
            If whitelist trust level is high, adds client to trusted users file.
            """
            
            if (self.server.config['commandbot']['whitelist_trustlevel'] == 'high'):
                trustedfile = 'config/trustedusers.yaml'
                trustedIPIDs = []
                if not os.path.exists(trustedfile):
                    trusted = []
                    trusted.append({'DiscordName': self.discord_name})
                    trusted[-1]['IPIDs'] = trustedIPIDs
                    trusted[-1]['IPIDs'].append({'IPID': self.ipid})
                else:
                    with open(trustedfile, 'r') as chars:
                        trusted = yaml.safe_load(chars)
                    match = False
                    for tu in trusted:
                        if tu['DiscordName'] == self.discord_name:
                            tu['IPIDs'].append({'IPID': self.ipid})
                            match = True
                            break
                    if not match:
                        trusted.append({'DiscordName': self.discord_name})
                        trusted[-1]['IPIDs'] = trustedIPIDs
                        trusted[-1]['IPIDs'].append({'IPID': client.ipid})
                with open(trustedfile, 'w', encoding='utf-8') as newfile:
                    yaml.dump(trusted, newfile)
            
        def auth_mod(self, password: str) -> None:
            """
            Attempt to log in as a moderator.
            :param password: password string
            :returns: name of profile which the password belongs to, if login
            was successful
            :raises: ClientError if password is incorrect
            
            
            """
            modfile = 'config/moderation.yaml'
            new = not os.path.exists(modfile)
            if new:
                raise ClientError('There is no moderation file!')
            if self.is_mod:
                raise ClientError('Already logged in.') 
            if len(password) == 0:
                with open(modfile, 'r') as chars:
                    mods = yaml.safe_load(chars)
                for item in mods:
                    ipid = item['ipid']
                    if self.ipid == ipid:
                        self.mod_profile_name = item['name']
                        self.is_mod = True
                        if item['status'] == 'admin':
                            self.is_admin = True
                if not self.is_mod:
                    self.send_command("FAILEDLOGIN");
                    raise ClientError('Login failed.')
                return self.mod_profile_name
            else:
                modpasses = self.server.config['modpass']
                if isinstance(modpasses, dict):
                    matches = [k for k in modpasses
                        if modpasses[k]['password'] == password]
                elif modpasses == password:
                    matches = ['default']
                else:
                    matches = []
                if len(matches) > 0:
                    self.is_mod = True
                    self.mod_profile_name = matches[0]
                    with open(modfile, 'r') as chars:
                        mods = yaml.safe_load(chars)
                    for item in mods:
                        ipid = item['ipid']
                        if self.ipid == ipid:
                            self.mod_profile_name = item['name']
                            self.is_mod = True
                            return self.mod_profile_name
                            if item['status'] == 'admin':
                                self.is_admin = True
                                return self.mod_profile_name
                    mods.append({'name': matches[0], 'status': 'mod', 'ipid': self.ipid})
                    with open(modfile, 'w', encoding='utf-8') as dump:
                        yaml.dump(mods, dump)
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

        def change_position(self, pos, silent=False):
            """
            Change the character's current position in the area.
            :param pos: position in area (Default value = '')
            """
            self.pos = pos
            if not silent:
                self.send_ooc(f'Position set to {pos}.')
            self.send_command('SP', self.pos) #Send a "Set Position" packet
            if pos == 'jud':
                self.send_command("JD", 1)
            else:
                self.send_command("JD", -1)
            self.area.broadcast_evidence_list()

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
        self.lastjoin = datetime.now()
        self.previd = -1
        self.available_ids = [i for i in range(self.server.config['playerlimit'])]
        self.all_ids = [i for i in range(self.server.config['playerlimit'])]

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
        user_id = None
        check_time = datetime.now()
        grab_id = database.ipid(transport.get_extra_info('peername')[0])
        res = int((check_time - self.lastjoin).total_seconds())
        print(f"It has been {res} seconds since the last join! {grab_id} attempted a connection!")
        if res < 5 and grab_id == self.previd:
            transport.write(b'BD#Please wait before connecting another client. Try again!#%')
            raise ClientError
        if len(self.available_ids) < 1:
            transport.write(b'BD#This server is full.#%')
            raise ClientError
        for id in self.all_ids:
            if id in self.available_ids:
                user_id = id
                self.available_ids.remove(id)
                break
        if user_id == None:
            transport.write(b'BD#Could not assign ID.#%')
            raise ClientError
        peername = transport.get_extra_info('peername')[0]
        c = self.Client(
            self.server, transport, user_id,
            database.ipid(peername))
        self.clients.add(c)
        for client in self.clients:
            if client.ipid == c.ipid:
                client.clientscon += 1
        self.lastjoin = datetime.now()
        self.previd = grab_id
        
        trustedfile = 'config/trustedusers.yaml'
        if not (self.server.config['webhooks_enabled']) or not (self.server.config['commandbot']['enabled']) or not (self.server.config['commandbot']['whitelist']):
            c.is_wlisted = True
        elif (self.server.config['commandbot']['whitelist_trustlevel'] == 'medium') or (self.server.config['commandbot']['whitelist_trustlevel'] == 'high'):
            for client in self.clients:
                if client.ipid == c.ipid and client.is_wlisted:
                    c.is_wlisted = True
                    c.discord_name = client.discord_name
        if (self.server.config['commandbot']['whitelist_trustlevel'] == 'high') and not c.is_wlisted:
            if os.path.exists(trustedfile):
                with open(trustedfile, 'r') as chars:
                    trusted = yaml.safe_load(chars)
                    for tu in trusted:
                        for tu_ipid in tu['IPIDs']:
                            if c.ipid == tu_ipid['IPID']:
                                c.is_wlisted = True
                                c.discord_name = tu['DiscordName']
                                self.server.commandbot.queue_trusted_whitelists.append(c)
                                break
                        if c.is_wlisted:
                            break
        return c

    def remove_client(self, client):
        """
        Remove a disconnected client from the client list.
        :param client: disconnected client
        """
        w = Webhooks(client.server)
        if client.id not in self.available_ids:
            self.available_ids.append(client.id)
        self.clients.discard(client)
        if client.area.jukebox:
            client.area.remove_jukebox_vote(client, True)
        for a in self.server.area_manager.areas:
            if client in a.owners:
                a.owners.remove(client)
                #if client.area.sub:
                #    client.area.hub.sub_arup_cms()
                if a.is_hub:
                    a.sub_arup_cms()
                    client.server.area_manager.send_arup_cms()
                else:
                    client.server.area_manager.send_arup_cms()
                if len(a.owners) == 0:
                    if a.is_locked != a.Locked.FREE:
                        a.unlock()
            if a.is_hub:
                for sub in a.subareas:
                    if client in sub.owners:
                        sub.owners.remove(client)
                        sub.hub.sub_arup_cms()
                    if len(sub.owners) == 0:
                        if len(sub.clients) == 0 and a.hubtype == 'user':
                            client.server.hub_manager.removesub(self, sub)
                            if sub.is_locked != sub.Locked.FREE:
                                sub.unlock()
        for c in client.following:
            c.followers.remove(client)
            c.send_ooc(f'{client.char_name} disconnected and is no longer following you.')
        for b in client.followers:
            b.following.remove(client)
            b.is_following = False
            b.send_ooc(f'{client.char_name} disconnected. Unfollowing.')
        if len(client.calling) > 0:
            caller = client.calling[0]
            client.calling.clear()
            if caller.calling[0] == client:
                caller.calling.clear()
                caller.incall = False
                if client.call != None:
                    callarea = client.call
                    callarea.owners.clear()
                    client.call = None
                    caller.call = None
                elif caller.call != None:
                    callarea = caller.call
                    callarea.owners.clear()
                    client.call = None
                    caller.call = None
        for c in self.clients:
            if c.ipid == client.ipid:
                c.clientscon -= 1
        if client.is_mod:
            w.unmod(client.mod_profile_name)
        if client.afktime:
            client.afktime.cancel()

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
            areas = []
            for a in client.server.area_manager.areas:
                areas.append(a)
                if a.is_hub:
                    for sub in a.subareas:
                        areas.append(sub)
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
                elif key == TargetType.HDID:
                    if client.hdid == value:
                        targets.append(client)
                elif key == TargetType.AFK:
                    if client.afk:
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

    def toggle_afk(self, client):
        w = Webhooks(client.server)
        if client.afk:
            client.area.broadcast_ooc('{} is no longer AFK.'.format(client.char_name))
            client.afk = False
            if client.is_mod:
                w.modafk(client=client, afk=False)
        else:
            client.area.broadcast_ooc('{} is now AFK.'.format(client.char_name))
            if client.afktime:
                client.afktime.cancel()
            client.afk = True
            if client.is_mod:
                w.modafk(client=client, afk=True)
