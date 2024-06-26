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

import os

import asyncio
import sqlite3
import json

import arrow

import logging
logger = logging.getLogger('debug')
event_logger = logging.getLogger('events')

from dataclasses import dataclass, field
from datetime import datetime
from functools import reduce
from textwrap import dedent

from .exceptions import ServerError


DB_FILE = os.getcwd() + '/storage/db.sqlite3'
_database_singleton = None

def __getattr__(name):
    global _database_singleton
    if _database_singleton is None:
        _database_singleton = Database()
    return getattr(_database_singleton, name)


class Database:
    """
    Represents a connection to an SQLite database that persists
    information about the server, such as users, bans, and logs.
    """

    def __init__(self):
        new = not os.path.exists(DB_FILE)

        self.db = sqlite3.connect(DB_FILE)
        self.db.execute('PRAGMA foreign_keys = ON')
        self.db.row_factory = sqlite3.Row

        if new:
            self.migrate_json_to_v1()

        self.migrate()

    def migrate_json_to_v1(self):
        """Migrate to v1 of the database from JSON."""
        with self.db as conn:
            logger.debug('Initializing database')
            with open('migrations/v1.sql', 'r') as file:
                conn.executescript(file.read())

            if not os.path.exists('storage/ip_ids.json'):
                logger.debug('ip_ids.json not found. Aborting migration.')
                return

            with open('storage/ip_ids.json', 'r') as ipids_file:
                # Sometimes, there are multiple IP addresses mapped to
                # the same IPID, so we have to reassign those IPIDs.
                ip_ipids = json.loads(ipids_file.read())
                ipids = set([ipid for ip, ipid in ip_ipids.items()])
                next_fallback_id = reduce(
                    lambda max_ipid, ipid: max(max_ipid, ipid), ipids)
                for ip, ipid in ip_ipids.items():
                    ipids.add(ipid)
                    effective_id = ipid
                    while True:
                        try:
                            conn.execute(dedent('''
                                INSERT INTO ipids(ipid, ip_address)
                                VALUES (?, ?)
                                '''), (effective_id, ip))
                        except sqlite3.IntegrityError:
                            effective_id = next_fallback_id
                            effective_id += 1
                            next_fallback_id = effective_id
                        else:
                            if effective_id != ipid:
                                logger.debug(f'IPID {ipid} reassigned to {effective_id}')
                            break

            with open('storage/hd_ids.json', 'r') as hdids_file:
                hdids = json.loads(hdids_file.read())
                for hdid, hdid_ipids in hdids.items():
                    for ipid in hdid_ipids:
                        # Sometimes, there are HDID entries that do not
                        # correspond to any IPIDs in the IPID table.
                        if ipid not in ipids:
                            logger.debug(f'IPID {ipid} in HDID list does not exist. Ignoring.')
                            continue
                        conn.execute(dedent('''
                            INSERT OR IGNORE INTO hdids(hdid, ipid)
                            VALUES (?, ?)
                            '''), (hdid, ipid))

            if not os.path.exists('storage/banlist.json'):
                logger.debug(f'banlist.json not found. Not migrating bans.')
                return
            with open('storage/banlist.json', 'r') as banlist_file:
                bans = json.load(banlist_file)
                for ipid, ban_info in bans.items():
                    try:
                        ipid = int(ipid)
                    except ValueError:
                        logger.debug(f'Bad IPID {ipid} in ban list. Ignoring.')
                        continue
                    if ipid not in ipids:
                        logger.debug(f'IPID {ipid} in ban list does not exist. Ignoring.')
                        continue
                    ban_id = conn.execute(dedent('''
                        INSERT INTO bans(ban_id, reason)
                        VALUES (NULL, ?)
                        '''), (ban_info['Reason'],)).lastrowid
                    conn.execute(dedent('''
                        INSERT INTO ip_bans(ipid, ban_id)
                        VALUES (?, ?)
                        '''), (ipid, ban_id))
            logger.debug('Migration to v1 complete')

    def migrate(self):
        for version in [2, 3, 4]:
            self.migrate_to_version(version)

    def migrate_to_version(self, version):
        with self.db as conn:
            cur_version = conn.execute('PRAGMA user_version') \
                .fetchone()['user_version']
            if cur_version >= version:
                return

            with open(f'migrations/v{version}.sql', 'r') as file:
                conn.executescript(file.read())
        logger.debug(f'Migration to v{version} complete')

    def ipid(self, ip):
        """Get an IPID from an IP address."""
        with self.db as conn:
            conn.execute(dedent('''
                INSERT OR IGNORE INTO ipids(ipid, ip_address) VALUES (NULL, ?)
                '''), (ip, ))
            ipid = conn.execute(dedent('''
                SELECT ipid FROM ipids WHERE ip_address = ?
                '''), (ip, )).fetchone()['ipid']
            event_logger.info(f'IPID for {ip}: {ipid}')
            return ipid

    def add_hdid(self, ipid, hdid):
        """Associate an HDID with an IPID."""
        with self.db as conn:
            event_logger.info(f'Associated {ipid} with {hdid}')
            conn.execute(dedent('''
                INSERT OR IGNORE INTO hdids(hdid, ipid) VALUES (?, ?)
                '''), (hdid, ipid))

    def ban(self,
            target_id,
            reason,
            ban_type='ipid',
            banned_by=None,
            unban_date=None,
            ban_id=None):
        """
        Ban an IPID or HDID.
        These should be used sparingly, as they can affect large swaths
        of web users if used incorrectly.
        """
        with self.db as conn:
            if ban_id is None:
                event_logger.info(f'{banned_by.name} ({banned_by.ipid}) ' +
                                  f'banned {target_id}: \'{reason}\'.')
                ban_id = conn.execute(dedent('''
                    INSERT INTO bans(reason, banned_by, unban_date)
                    VALUES (?, ?, ?)
                    '''), (reason, banned_by.ipid, unban_date)).lastrowid
            if ban_type == 'ipid':
                try:
                    conn.execute(dedent('''
                        INSERT INTO ip_bans(ipid, ban_id) VALUES (?, ?)
                        '''), (target_id, ban_id))
                except sqlite3.IntegrityError as exc:
                    raise ServerError(f'Error inserting ban: {exc}'
                                      ' (the IPID may not exist)')
            elif ban_type == 'hdid':
                try:
                    conn.execute(dedent('''
                        INSERT INTO hdid_bans(hdid, ban_id) VALUES (?, ?)
                        '''), (target_id, ban_id))
                except sqlite3.IntegrityError as exc:
                    raise ServerError(f'Error inserting ban: {exc}')
            else:
                raise ServerError(f'unknown ban type {ban_type}')

        if unban_date is not None:
            self._schedule_unban(ban_id)

        return ban_id
    
    def warn(self,
            target,
            reason,
            warned_by=None,
            warn_id=None):
        """
        Warn an IPID.
        """
        with self.db as conn:
            if warn_id is None:
                event_logger.info(f'{warned_by.name} ({warned_by.ipid}) ' +
                                  f'warned {target.ipid}: \'{reason}\'.')
                warn_id = conn.execute(dedent('''
                    INSERT INTO warns(reason, warned_by)
                    VALUES (?, ?)
                    '''), (reason, warned_by.ipid)).lastrowid
                warn_id_int = int(warn_id)
                try:
                    conn.execute("UPDATE warns SET ipid = ? WHERE warn_id = ?", (target.ipid, warn_id_int))
                except sqlite3.IntegrityError as exc:
                    raise ServerError(f'Error inserting warn: {exc}')
        return warn_id

    def last_known_name(self, ipid):
        """
        Find the last known OOC name of an IPID.
        """
        with self.db as conn:
            row = conn.execute(dedent('''
                SELECT ooc_name FROM room_events
                WHERE ipid = ? AND ooc_name IS NOT NULL AND ooc_name != ''
                ORDER BY event_time DESC LIMIT 1
                '''), (ipid,)).fetchone()
            if row is not None:
                return row['ooc_name']
            else:
                return None

    @dataclass
    class Ban:
        ban_id: int
        ban_date: datetime
        unban_date: datetime
        banned_by: int
        reason: str

        def __post_init__(self):
            self.ban_date = arrow.get(self.ban_date).datetime

            if self.unban_date is None or self.unban_date == None or self.unban_date == "":
                self.unban_date = None
            else:
                self.unban_date = arrow.get(self.unban_date).datetime

        @property
        def ipids(self):
            """Find IPIDs affected by this ban."""
            with _database_singleton.db as conn:
                return [row['ipid'] for row in
                    conn.execute(dedent('''
                        SELECT ipid FROM ip_bans WHERE ban_id = ?
                        '''), (self.ban_id,)).fetchall()
                ]

        @property
        def hdids(self):
            """Find HDIDs affected by this ban."""
            with _database_singleton.db as conn:
                return [row['hdid'] for row in
                    conn.execute(dedent('''
                        SELECT hdid FROM hdid_bans WHERE ban_id = ?
                        '''), (self.ban_id,)).fetchall()
                ]

        @property
        def banned_by_name(self):
            """
            Find the last known OOC name of the player who issued
            the ban.
            """
            return _database_singleton.last_known_name(self.banned_by)

    @dataclass
    class Warn:
        warn_id: int
        ipid: int
        warn_date: datetime
        warned_by: int
        reason: str

        def __post_init__(self):
            self.warn_date = arrow.get(self.warn_date).datetime

        @property
        def ipids(self):
            """Find IPIDs affected by this warn."""
            with _database_singleton.db as conn:
                return [row['ipid'] for row in
                    conn.execute(dedent('''
                        SELECT * FROM warns WHERE warn_id = ?
                        '''), (self.warn_id,)).fetchall()
                ]

        @property
        def warned_by_name(self):
            """
            Find the last known OOC name of the player who issued
            the warn.
            """
            return _database_singleton.last_known_name(self.warned_by)


    def find_ban(self, ipid=None, hdid=None, ban_id=None):
        """Check if an IPID and/or HDID are banned."""
        with self.db as conn:
            # Why is this query so complicated? The answer is that I am
            # offloading most of the work to SQLite. This query first
            # finds HDID or IPID bans, then looks up the associated ban
            # information. Then it finds the last known OOC name of the
            # player who issued that ban, purely as a convenience
            # for later use. Use `EXPLAIN QUERY PLAN` for a breakdown.
            #   LEFT OUTER JOIN room_events ON
            #      room_events.ipid = banned_by AND
            #      ooc_name IS NOT NULL
            #   ORDER BY event_time DESC LIMIT 1
            ban = conn.execute(dedent('''
                SELECT *
                FROM (
                    SELECT ban_id FROM ip_bans WHERE ipid = ?
                    UNION SELECT ban_id FROM hdid_bans WHERE hdid = ?
                    UNION SELECT ban_id FROM bans WHERE ban_id = ?
                )
                JOIN bans USING (ban_id)
                '''), (ipid, hdid, ban_id)).fetchone()
            if ban is not None:
                return Database.Ban(**ban)
            else:
                return None

    def unban(self, ban_id):
        """Remove a ban entry."""
        event_logger.info(f'Unbanning {ban_id}')
        with self.db as conn:
            unbans = conn.execute(dedent('''
                DELETE FROM bans WHERE ban_id = ?
                '''), (ban_id,)).rowcount
            return unbans > 0
        
    def find_warn(self, warn_id):
        """Get the warn entry matching the given warn ID."""
        #TODO: this should not be a for loop
        with self.db as conn:
            return [Database.Warn(**row) for row in
                conn.execute(dedent('''
                SELECT * FROM warns WHERE warn_id = ?
                '''), (warn_id,)).fetchall()]
    
    def list_warns(self, query, count, lookup_type='ipid'):
        """
        List the last <count> warns for a given query.
        """
        with self.db as conn:
            if lookup_type == 'ipid':
                return [Database.Warn(**row) for row in
                    conn.execute(dedent('''
                    SELECT *
                    FROM (
                        SELECT * FROM warns WHERE ipid = ?
                        ORDER BY warn_date DESC LIMIT ?
                    )
                    ORDER BY warn_date ASC
                    '''), (query,count)).fetchall()]
            elif lookup_type == 'warned_by':
                return [Database.Warn(**row) for row in
                    conn.execute(dedent('''
                    SELECT *
                    FROM (
                        SELECT * FROM warns WHERE warned_by = ?
                        ORDER BY warn_date DESC LIMIT ?
                    )
                    ORDER BY warn_date ASC
                    '''), (query,count)).fetchall()]

    def unwarn(self, warn_id):
        """Remove a warn entry."""
        event_logger.info(f'Unwarning {warn_id}')
        with self.db as conn:
            unwarns = conn.execute(dedent('''
                DELETE FROM warns WHERE warn_id = ?
                '''), (warn_id,)).rowcount
            return unwarns > 0

    def schedule_unbans(self):
        """
        Schedule unbans from the database.

        There is a bug in Python 3.7 and below where functions cannot be
        scheduled with a timeout longer than one day. As a workaround,
        schedule_unbans will only get the unbans for the next 12 hours
        and then will have to be called again 12 hours later.
        """
        dated_bans = []
        with self.db as conn:
            dated_bans = conn.execute(dedent('''
                SELECT ban_id FROM bans
                WHERE unban_date IS NOT NULL AND
                    datetime(unban_date) < datetime(?, '+12 hours')
                '''), (arrow.utcnow().datetime,)).fetchall()

        for ban in dated_bans:
            self._schedule_unban(ban['ban_id'])

    def _schedule_unban(self, ban_id):
        with self.db as conn:
            ban = conn.execute(dedent('''
                SELECT unban_date FROM bans WHERE ban_id = ?
                '''), (ban_id,)).fetchone()
            time_to_unban = (arrow.get(ban['unban_date']) - arrow.utcnow()).total_seconds()

            def auto_unban():
                self.unban(ban_id)
                self.log_misc('auto_unban', data={'id': ban_id})

            asyncio.get_event_loop().call_later(time_to_unban, auto_unban)

    def log_ic(self, client, room, showname, message):
        """Log an IC message."""
        event_logger.info(f'[{room.abbreviation}] {showname}/{client.char_name}' +
                          f'/{client.name} ({client.ipid}): {message}')
        with self.db as conn:
            conn.execute(dedent('''
                INSERT INTO ic_events(ipid, room_name, char_name, ic_name,
                    message) VALUES (?, ?, ?, ?, ?)
                '''), (client.ipid, room.abbreviation, client.char_name,
                    showname, message))

    def log_room(self, event_subtype, client, room, message=None, target=None):
        """
        Log a room or OOC event. The event subtype is translated to an enum
        value, creating one if necessary.
        """
        ipid, char_name, ooc_name = (client.ipid, client.char_name,
                                     client.name) if client is not None else (
                                         None, None, None)
        target_ipid = target.ipid if target is not None else None
        subtype_id = self._subtype_atom('room', event_subtype)
        if isinstance(message, dict):
            message = json.dumps(message)

        event_logger.info(f'[{room.abbreviation}] {client.char_name}' +
                    f'/{client.name} ({client.ipid}): event {event_subtype} ({message})')
        with self.db as conn:
            conn.execute(dedent('''
                INSERT INTO room_events(ipid, room_name, char_name, ooc_name,
                    event_subtype, message, target_ipid)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                '''), (ipid, room.abbreviation, char_name, ooc_name,
                    subtype_id, message, target_ipid))

    def log_connect(self, client, failed=False):
        """Log a connect attempt."""
        event_logger.info(f'{client.ipid} (HDID: {client.hdid}) ' +
                          f'{"was blocked from connecting" if failed else "connected"}.')
        with self.db as conn:
            conn.execute(dedent('''
                INSERT INTO connect_events(ipid, hdid, failed) VALUES (?, ?, ?)
                '''), (client.ipid, client.hdid, failed))

    def log_misc(self, event_subtype, client=None, target=None, data=None):
        """
        Log a miscellaneous event. The event subtype is translated to an enum
        value, creating one if necessary.
        """
        client_ipid = client.ipid if client is not None else None
        target_ipid = target.ipid if target is not None else None
        subtype_id = self._subtype_atom('misc', event_subtype)
        data_json = json.dumps(data)
        event_logger.info(f'{event_subtype} ({client_ipid} onto {target_ipid}): {data}')

        with self.db as conn:
            conn.execute(dedent('''
                INSERT INTO misc_events(ipid, target_ipid, event_subtype,
                    event_data) VALUES (?, ?, ?, ?)
                '''), (client_ipid, target_ipid, subtype_id, data_json))

    def recent_bans(self, count=5):
        """
        Get the most recent bans in chronological order.
        """
        with self.db as conn:
            return [Database.Ban(**row) for row in
                conn.execute(dedent('''
                    SELECT * FROM (SELECT * FROM bans
                        WHERE ban_date IS NOT NULL
                        ORDER BY ban_date DESC LIMIT ?)
                    ORDER BY ban_date ASC
                    '''), (count,)).fetchall()]

    def _subtype_atom(self, event_type, event_subtype):
        if event_type not in ('room', 'misc'):
            raise AssertionError()

        with self.db as conn:
            conn.execute(dedent(f'''
                INSERT OR IGNORE INTO {event_type}_event_types(type_name)
                VALUES (?)
                '''), (event_subtype,))
            return conn.execute(dedent(f'''
                SELECT type_id FROM {event_type}_event_types
                WHERE type_name = ?
                '''), (event_subtype,)).fetchone()['type_id']
