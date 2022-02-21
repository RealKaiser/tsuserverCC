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
import re 
from enum import Enum
from enum import IntFlag


class TargetType(Enum):
    # possible keys: ip, OOC, id, cname, ipid, hdid
    IP = 0
    OOC_NAME = 1
    ID = 2
    CHAR_NAME = 3
    IPID = 4
    HDID = 5
    ALL = 6

class MusicEffect(IntFlag):
    FADE_IN = 1
    FADE_OUT = 2
    SYNC_POS = 4

def dezalgo(input, tolerance=3):
    """
    Turns any string into a de-zalgo'd version, with a tolerance to allow for normal diacritic use.

    The following Unicode blocks are scrubbed:
    U+0300 - U+036F - COMBINING DIACRITICAL MARKS
    U+1AB0 - U+1AFF - COMBINING DIACRITICAL MARKS EXTENDED
    U+1DC0 - U+1DFF - COMBINING DIACRITICAL MARKS SUPPLEMENT
    U+20D0 - U+20FF - COMBINING DIACRITICAL MARKS FOR SYMBOLS
    U+FE20 - U+FE2F - COMBINING HALF MARKS
    U+115F          - HANGUL CHOSEONG FILLER
    U+1160          - HANGUL JUNGSEONG FILLER
    U+3164          - HANGUL FILLER
    """

    filtered = re.sub('([\u0300-\u036f\u1ab0-\u1aff\u1dc0-\u1dff\u20d0-\u20ff\ufe20-\ufe2f' +
                        '\u115f\u1160\u3164]' +
                        '{' + re.escape(str(tolerance)) + ',})',
                        '', input)
    return filtered

def remove_URL(sample):
    """Remove URLs from a sample string"""
    return re.sub(r"http\S+", "", sample)

def contains_URL(sample):
    """Determine if string contains a URL in sample string."""
    return re.match(r"http\S+", sample) != None
