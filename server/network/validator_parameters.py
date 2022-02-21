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

from enum import Enum

class ArgType(Enum):
		"""Represents the data type of an argument for a network command."""
		STR = 1,
		STR_OR_EMPTY = 2,
		INT = 3,
		INT_OR_STR = 3

# These are the different sets of paramemeters needed for messages validation.
# Each function returns a set of parameters needed by  each version of the client.

def validator_pre260():
    """
    Absurdly big chunk of validation parameters for pre2.6 clients. 
    
    These contain the msg_type, pre, folder, anim, text,
    pos, sfx, emote_mod, cid, sfx_delay, button, evidence,
    flip, ding, color. 

    This function is used in aoprotocol.py to assign 
    these parameters as class variables.

    Parameters: None
    Preconditions: None
    
    """
    parameters =   [ArgType.STR,                        
                    ArgType.STR_OR_EMPTY, ArgType.STR, 
			        ArgType.STR, ArgType.STR, 
		            ArgType.STR, ArgType.STR, 
			        ArgType.INT, ArgType.INT,
			        ArgType.INT, ArgType.INT_OR_STR, 
			        ArgType.INT, ArgType.INT, 
			        ArgType.INT, ArgType.INT]
    return parameters

def validator_270():
    """
    Absurdly big chunk of validation parameters for 2.7 clients (RIP LMAO).
    
    These contain the msg_type, pre, folder, anim, text, pos, sfx, anim_type, 
    cid, sfx_delay, button, evidence, flip, ding, color, showname, charid_pair, 
    offset_pair, nonint_pre, looping_sfx, screenshake, frame_screenshake, 
    frame_realization, frame_sfx.

    This function is used in aoprotocol.py to assign 
    these parameters as class variables.

    Parameters: None
    Preconditions: None
    """ 

    parameters =   [ArgType.STR, ArgType.STR_OR_EMPTY, 
                    ArgType.STR, ArgType.STR,
					ArgType.STR, ArgType.STR, 
                    ArgType.STR, ArgType.INT,
					ArgType.INT, ArgType.INT, 
                    ArgType.INT, ArgType.INT,
					ArgType.INT, ArgType.INT, 
                    ArgType.INT, ArgType.STR_OR_EMPTY,
					ArgType.INT, ArgType.INT, 
                    ArgType.INT, ArgType.STR,
					ArgType.INT, ArgType.STR, 
                    ArgType.STR, ArgType.STR]
    return parameters

def validator_290():
    """
    Absurdly big chunk of validation parameters for 2.9 clients. 
    
    These contain the msg_type, pre, folder, anim, text, 
    pos, sfx, anim_type, cid, sfx_delay, button, evidence, 
    flip, ding, color, showname, charid_pair, offset_pair, 
    nonint_pre, looping_sfx, screenshake, frame_screenshake, 
    frame_realization, frame_sfx, additive, effect.

    This function is used in aoprotocol.py to assign 
    these parameters as class variables. 

    Parameters: None
    Precondition: None

    """

    parameters =       [ArgType.STR, ArgType.STR_OR_EMPTY, 
                        ArgType.STR, ArgType.STR, 
						ArgType.STR, ArgType.STR, 
                        ArgType.STR, ArgType.INT, 
						ArgType.INT, ArgType.INT, 
                        ArgType.INT_OR_STR, ArgType.INT, 
						ArgType.INT, ArgType.INT, 
                        ArgType.INT, ArgType.STR_OR_EMPTY, 
						ArgType.STR, ArgType.STR, 
                        ArgType.INT, ArgType.STR, 
						ArgType.INT, ArgType.STR, 
                        ArgType.STR, ArgType.STR,
						ArgType.INT, ArgType.STR]
    return parameters

