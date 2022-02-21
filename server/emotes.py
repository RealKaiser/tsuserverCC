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

from os import path
from configparser import ConfigParser

import logging
logger = logging.getLogger('debug')

char_dir = 'characters'


class Emotes:
    """
    Represents a list of emotes read in from a character INI file
    used for validating which emotes can be sent by clients.
    """

    def __init__(self, name):
        self.name = name
        self.emotes = set()
        self.read_ini()

    def read_ini(self):
        char_ini = ConfigParser(comment_prefixes=('#', ';', '//', '\\\\'),
                                strict=False)
        try:
            char_path = path.join(char_dir, self.name, 'char.ini')
            with open(char_path) as f:
                char_ini.read_file(f)
        except FileNotFoundError:
            logger.warn(f'Character file {char_path} not found')
            return

        try:
            for emote_id in range(1, int(char_ini['Emotions']['number']) + 1):
                emote_id = str(emote_id)
                _name, preanim, anim, _mod = char_ini['Emotions'][str(emote_id)].split('#')[:4]
                if emote_id in char_ini['SoundN']:
                    sfx = char_ini['SoundN'][str(emote_id)]
                    if len(sfx) == 1:
                        # Often, a one-character SFX is a placeholder for no sfx,
                        # so allow it
                        sfx = None
                else:
                    sfx = None
                self.emotes.add((preanim, anim, sfx))

                # No SFX should always be allowed
                self.emotes.add((preanim, anim, None))
        except KeyError as e:
            logger.warn(f'Unknown key {e.args[0]} in character file {char_path}. '
                        'This indicates a malformed character INI file.')
            return

    def validate(self, preanim, anim, sfx):
        """
        Determines whether or not an emote canonically belongs to this
        character (that is, it is defined server-side).
        """
        # There are no emotes loaded, so allow anything
        if len(self.emotes) == 0:
            return True

        if len(sfx) <= 1:
            sfx = None
        return (preanim, anim, sfx) in self.emotes
