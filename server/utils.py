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
import os
import logging
import yaml

import requests
import json

from server import database


class Utilities:
    """
    Contains functions useful for server administrators.
    """
    def __init__(self, server):
        self.server = server
    
    def modcall_webhook(self, message=None):
        url = self.server.config['webhook_url']
        mods = self.server.area_manager.mods_online()
        data = {}
        if mods != 0:
            data["content"] = f"New modcall received ({mods} moderators online)"
        else:
            data["content"] = "@here A user called for a moderator, but there are none online!"
        data["embeds"] = []
        embed = {}
        embed["description"] = message
        embed ["title"] = "Modcall"
        data["embeds"].append(embed)

        result = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})

        try:
            result.raise_for_status()
        except requests.exceptions.HTTPError as err:
            database.log_misc('webhook.err', data=err)
        else:
            database.log_misc('webhook.ok', data="successfully delivered payload, code {}".format(result.status_code))

