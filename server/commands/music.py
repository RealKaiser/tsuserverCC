import random
import asyncio
import shlex

from server import database
from server.exceptions import ClientError, ServerError, ArgumentError
from server.constants import TargetType

from . import mod_only

__all__ = [
    'ooc_cmd_currentmusic',
    'ooc_cmd_music',
    'ooc_cmd_jukeboxtoggle',
    'ooc_cmd_jukeboxskip',
    'ooc_cmd_jukebox',
    'ooc_cmd_play',
    'ooc_cmd_playrandom',
    'ooc_cmd_shuffle',
    'ooc_cmd_blockdj',
    'ooc_cmd_unblockdj',
    'ooc_cmd_addmlist',
    'ooc_cmd_playl',
    'ooc_cmd_musiclist',
    'ooc_cmd_storemlist',
    'ooc_cmd_loadmlist',
    'ooc_cmd_clearmusiclist'
]


def ooc_cmd_addmlist(client, arg):
    if not client.area.name.startswith('Custom'):
        if client not in client.area.owners and not client.is_mod:
            raise ClientError('You must be a CM.')
    args = shlex.split(arg)
    if len(args) < 2:
        raise ArgumentError('Not enough arguments. Use /addmlist "name" "length in seconds".')
    elif len(args) == 2:
        name = 'custom/'
        name += args[0]
        length = args[1]
        try:
            length = int(args[1])
        except ValueError:
            raise ClientError(f'{length} does not look like a valid length.')
        client.area.cmusic_list[name] = length
        nname = name[7:]
        client.area.broadcast_ooc(f'{nname} added to the area music list.')

def ooc_cmd_storemlist(client, arg):
    if client not in client.area.owners and not client.is_mod:
        raise ClientError('You must be a CM.')
    if len(arg) < 1:
        raise ArgumentError('Your stored list requires a name!')
    if len(arg) > 12:
        raise ArgumentError('Keep the name of your list to 12 characters or below.')
    if ' ' in arg:
        raise ArgumentError('Try to use a name without spaces.')
    if len(client.area.cmusic_list) == 0:
        raise ArgumentError('No list to store!')
    client.server.musiclist_manager.storelist(client, arg)

def ooc_cmd_loadmlist(client, arg):
    if client not in client.area.owners and not client.is_mod:
        raise ClientError('You must be a CM.')
    if len(arg) < 1:
        raise ArgumentError('Your stored list requires a name!')
    if len(arg) > 12:
        raise ArgumentError('Keep the name of your list to 12 characters or below.')
    if ' ' in arg:
        raise ArgumentError('Try to use a name without spaces.')
    client.server.musiclist_manager.loadlist(client, arg)

def ooc_cmd_musiclist(client, arg):
    if len(arg) > 0:
        raise ArgumentError('This command takes no arguments.')
    if len(client.area.cmusic_list) == 0:
        raise ArgumentError('Music list is empty.')
    msg = 'Music List:'
    index = 1
    for name, length in client.area.cmusic_list.items():
        nname = name[7:]
        msg += f' \n{index}: {nname} - {length} seconds.\n'
        msg += f'-------------------'
        index += 1
    client.send_ooc(msg)

def ooc_cmd_clearmusiclist(client, arg):
    if not client.area.name.startswith('Custom'):
        if client not in client.area.owners and not client.is_mod:
            raise ClientError('You must be a CM.')
    if len(arg) > 0:
        raise ArgumentError('This command takes no arguments.')
    client.area.cmusic_list.clear()
    client.send_ooc(f'Area music list cleared.')

def ooc_cmd_playl(client, arg):
    if not client.area.name.startswith('Custom'):
        if client not in client.area.owners and not client.is_mod:
            raise ClientError('You must be a CM.')
    if len(arg) == 0:
        raise ArgumentError('Choose a number to play from /musiclist.')
    try:
        trackno = int(arg)
    except ValueError:
        raise ClientError(f'{arg} does not look like a valid length.')
    index = 1
    if len(client.area.cmusic_list) != 0:
        for name, length in client.area.cmusic_list.items():
            if trackno == index:
                client.area.play_music(name, client.char_id, length)
                client.area.add_music_playing(client, name)
                database.log_room('play', client, client.area, message=name)
                return
            else:
                index += 1
        raise ClientError('Track not found!')
    else:
        raise ClientError('Nothing to play in the music list.')

def ooc_cmd_play(client, arg):
    """
    Play a track.
    Usage: /play <name>
    """
    if not client.area.name.startswith('Custom'):
        if client not in client.area.owners and not client.is_mod:
            raise ClientError('You must be a CM.')
    args = shlex.split(arg)
    if len(args) < 1:
        raise ArgumentError('Not enough arguments. Use /play "name" "length in seconds".')
    elif len(args) == 2:
        name = 'custom/'
        name += args[0]
        length = args[1]
        try:
            length = int(args[1])
        except ValueError:
            raise ClientError(f'{length} does not look like a valid length.')
    elif len(args) == 1:
        name = 'custom/'
        name += args[0]
        length = -1
    else:
        raise ArgumentError('Too many arguments. Use /play "name" "length in seconds".')
    client.area.play_music(name, client.char_id, length)
    client.area.add_music_playing(client, args[0])
    database.log_room('play', client, client.area, message=name)

def ooc_cmd_currentmusic(client, arg):
    """
    Show the current music playing.
    Usage: /currentmusic
    """
    if len(arg) != 0:
        raise ArgumentError('This command has no arguments.')
    if client.area.current_music == '':
        raise ClientError('There is no music currently playing.')
    if client.is_mod:
        client.send_ooc(
            'The current music is {} and was played by {} ({}).'.format(
                client.area.current_music, client.area.current_music_player,
                client.area.current_music_player_ipid))
    else:
        client.send_ooc(
            'The current music is {} and was played by {}.'.format(
                client.area.current_music, client.area.current_music_player))


def ooc_cmd_music(client, arg):
    """
    Show the current music playing.
    Usage: /currentmusic
    """
    ooc_cmd_currentmusic(client, arg)

def ooc_cmd_jukeboxtoggle(client, arg):
    """
    Toggle jukebox mode. While jukebox mode is on, all music changes become
    votes for the next track, rather than changing the track immediately.
    Usage: /jukebox_toggle
    """
    if len(arg) != 0:
        raise ArgumentError('This command has no arguments.')
    if client not in client.area.owners and not client.is_mod:
        raise ClientError('You must be a CM.')
    client.area.jukebox = not client.area.jukebox
    client.area.jukebox_votes = []
    client.area.broadcast_ooc('{} [{}] has set the jukebox to {}.'.format(
        client.char_name, client.id, client.area.jukebox))
    database.log_room('jukebox_toggle', client, client.area,
        message=client.area.jukebox)


def ooc_cmd_jukeboxskip(client, arg):
    """
    Skip the current track.
    Usage: /jukebox_skip
    """
    if len(arg) != 0:
        raise ArgumentError('This command has no arguments.')
    if not client.area.jukebox:
        raise ClientError('This area does not have a jukebox.')
    if len(client.area.jukebox_votes) == 0:
        raise ClientError('There is no song playing right now, skipping is pointless.')
    if client not in client.area.owners and not client.is_mod:
        raise ClientError('You must be a CM.')
    client.area.start_jukebox()
    if len(client.area.jukebox_votes) == 1:
        client.area.broadcast_ooc(
            '{} [{}] has forced a skip, restarting the only jukebox song.'.
            format(client.char_name, client.id))
    else:
        client.area.broadcast_ooc(
            '{} [{}] has forced a skip to the next jukebox song.'.format(
                client.char_name, client.id))
    database.log_room('jukebox_skip', client, client.area)


def ooc_cmd_jukebox(client, arg):
    """
    Show information about the jukebox's queue and votes.
    Usage: /jukebox
    """
    if len(arg) != 0:
        raise ArgumentError('This command has no arguments.')
    if not client.area.jukebox:
        raise ClientError('This area does not have a jukebox.')
    if len(client.area.jukebox_votes) == 0:
        client.send_ooc('The jukebox has no songs in it.')
    else:
        total = 0
        songs = []
        voters = dict()
        chance = dict()
        message = ''

        for current_vote in client.area.jukebox_votes:
            if songs.count(current_vote.name) == 0:
                songs.append(current_vote.name)
                voters[current_vote.name] = [current_vote.client]
                chance[current_vote.name] = current_vote.chance
            else:
                voters[current_vote.name].append(current_vote.client)
                chance[current_vote.name] += current_vote.chance
            total += current_vote.chance

        for song in songs:
            message += '\n- ' + song + '\n'
            message += '-- VOTERS: '

            first = True
            for voter in voters[song]:
                if first:
                    first = False
                else:
                    message += ', '
                message += voter.char_name + ' [' + str(voter.id) + ']'
                if client.is_mod:
                    message += '(' + str(voter.ipid) + ')'
            message += '\n'

            if total == 0:
                message += '-- CHANCE: 100'
            else:
                message += '-- CHANCE: ' + str(
                    round(chance[song] / total * 100))

        client.send_ooc(
            f'The jukebox has the following songs in it:{message}')

def ooc_cmd_playrandom(client, arg):
    """
    Plays a random track.
    Usage: /playrandom
    """
    if len(arg) > 0:
        raise ArgumentError('This command takes no arguments.')
    index = 0
    for item in client.server.music_list:
        for song in item['songs']:
            index += 1
    if index == 0:
        raise ServerError(
                'No music found.')
    else:
        music_set = set(range(index))
        trackid = random.choice(tuple(music_set))
        index = 1
        for item in client.server.music_list:
            for song in item['songs']:
                if index == trackid:
                    client.area.play_music(song['name'], client.char_id, song['length'])
                    client.area.add_music_playing(client, song['name'])
                    database.log_room('play', client, client.area, message=song['name'])
                    return
                else:
                    index += 1

def ooc_cmd_shuffle(client, arg):
    """
    Play a track.
    Usage: /play <name>
    """
    if arg == 'musiclist':
        client.area.musiclist_shuffle(client)
    else:
        client.area.music_shuffle(arg, client)

@mod_only()
def ooc_cmd_blockdj(client, arg):
    """
    Prevent a user from changing music.
    Usage: /blockdj <id>
    """
    if len(arg) == 0:
        raise ArgumentError('You must specify a target. Use /blockdj <id>.')
    try:
        targets = client.server.client_manager.get_targets(
            client, TargetType.ID, int(arg), False)
    except:
        raise ArgumentError('You must enter a number. Use /blockdj <id>.')
    if not targets:
        raise ArgumentError('Target not found. Use /blockdj <id>.')
    for target in targets:
        target.is_dj = False
        target.send_ooc(
            'A moderator muted you from changing the music.')
        database.log_room('blockdj', client, client.area, target=target)
        target.area.remove_jukebox_vote(target, True)
    client.send_ooc('blockdj\'d {}.'.format(
        targets[0].char_name))


@mod_only()
def ooc_cmd_unblockdj(client, arg):
    """
    Unblock a user from changing music.
    Usage: /unblockdj <id>
    """
    if len(arg) == 0:
        raise ArgumentError('You must specify a target. Use /unblockdj <id>.')
    try:
        targets = client.server.client_manager.get_targets(
            client, TargetType.ID, int(arg), False)
    except:
        raise ArgumentError('You must enter a number. Use /unblockdj <id>.')
    if not targets:
        raise ArgumentError('Target not found. Use /blockdj <id>.')
    for target in targets:
        target.is_dj = True
        target.send_ooc(
            'A moderator unmuted you from changing the music.')
        database.log_room('unblockdj', client, client.area, target=target)
    client.send_ooc('Unblockdj\'d {}.'.format(
        targets[0].char_name))
