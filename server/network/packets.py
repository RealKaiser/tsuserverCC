"""
tsuserverOLE, an Attorney Online server.
Copyright (C) 2021 KillerSteel <killermagnum5@gmail.com

Derivative of tsuserverCC, an Attorney Online server.
Copyright (C) 2020 Kaiser <kaiserkaisie@gmail.com>

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

def features_fl():
    """
    Returns a list of features supported by the server. 
    
    This function is intended to be used in aoprotocol.py
    in order to obtain the flags needed for the FL Packet 
    (net_cmd_id) and it takes no arguments.

    """
    features = 	['FL', 'yellowtext', 'customobjections', 
				'flipping', 'fastloading', 'noencryption',
				'deskmod', 'evidence', 'modcall_reason', 
				'cccc_ic_support', 'arup', 'casing_alerts', 
				'looping_sfx', 'additive', 'effects',
				'prezoom', 'y_offset', 'expanded_desk_mods',
                'auth_packet']
    return features