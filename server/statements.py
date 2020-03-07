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

class Statement:

	def __init__(self, msg_type, pre, folder, anim, msg, pos, sfx, anim_type, cid, sfx_delay, button, evidence, flip, ding, color, showname, charid_pair, other_folder, other_emote, offset_pair, other_offset, other_flip, nonint_pre, looping_sfx, screenshake, frame_screenshake, frame_realization, frame_sfx):
		self.msg_type = msg_type
		self.pre = pre
		self.folder = folder
		self.anim = anim
		self.msg = msg
		self.pos = pos
		self.sfx = sfx
		self.anim_type = anim_type
		self.cid = cid
		self.sfx_delay = sfx_delay
		self.button = button
		self.evidence = evidence
		self.flip = flip
		self.ding = ding
		self.color = color
		self.showname = showname
		self.charid_pair = charid_pair
		self.other_folder = other_folder
		self.other_emote = other_emote
		self.offset_pair = offset_pair
		self.other_offset = other_offset
		self.other_flip = other_flip
		self.nonint_pre = nonint_pre
		self.looping_sfx = looping_sfx
		self.screenshake = screenshake
		self.frame_screenshake = frame_screenshake
		self.frame_realization = frame_realization
		self.frame_sfx = frame_sfx

		self.id = 0