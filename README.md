# tsuserverCC

A Python-based server for Attorney Online, forked from [AttorneyOnline/tsuserver3](https://github.com/AttorneyOnline/tsuserver3)

Also includes many code improvements from [TsuOLE](https://github.com/HolyMan-17/tsuserverOLE)

Requires Python 3.7+ and PyYAML.

### Changes/additions from tsuserver3
* Testimony recording/playback system,
* Extended support for custom content,
* More options for area management, including:
  - Accessible hub system, hubs with subareas without need for seperate area lists.
  - Storing/loading hubs up to a 100 areas, complete with connections and music lists,
  - On-the-fly area renaming, creation, and destruction,
  - Password locks,
  - Ability to connect areas via 'exits,'
  - and playercount hiding.
* Additional moderation features,
* Additional features to support roleplay,
* Add music on the fly, and have it appear on the server's music list, (per area/hub basis)
* A category-based music shuffle system.

## How to use

* Install the latest version of Python. **Python 2 will not work**, as tsuserver3 depends on async/await, which can only be found on Python 3.5 and newer.
  - If your system supports it, it is recommended that you use a separate virtual environment, such as [Anaconda](https://www.continuum.io/downloads) for Windows, or [virtualenv](https://virtualenv.pypa.io/en/stable/) for everyone else (it runs itself using Python).
* Open Command Prompt or your terminal, and change to the directory where you downloaded tsuserver3 to. You can do this in two ways:
  - Go up one folder above the tsuserver3 folder, Shift + right click the tsuserver3 folder, and click `Open command window here`. This is the easiest method.
  - Copy the path of the tsuserver3 folder, open the terminal, and type in `cd "[paste here]"`, excluding the brackes, but including the quotation marks if the path contains spaces.
* To install PyYAML and dependencies, type in the following:
  ```bash
  python -m pip install --user -r requirements.txt
  ```
  If you are using Windows and have both Python 2 and 3 installed, you may do the following:
  ```batch
  py -3 -m pip install --user -r requirements.txt
  ```
  This operation should not require administrator privileges, unless you decide to remove the `--user` option.
* Rename `config_sample` to `config` and edit the values to your liking. Be sure to check your YAML file for syntax errors. *Use spaces only; do not use tabs.*
* Run by either double-clicking `start_server.py` or typing in `python start_server.py`, or `py -3 start_server.py` if you use both Python 2 and 3. It is normal to not see any output once you start the server.
  - To stop the server, press Ctrl+C multiple times.

## Commands

### User Commands

* **help**
    - Links to this readme
* **g** "message" 
    - Sends a serverwide message
* **toggleglobal** 
    - Toggles global on and off
* **need** "message" 
    - Sends a serverwide advert
* **toggleadverts** 
    - Toggles adverts on and off
* **area** "area name/abbreviation" "password"
    - Displays all hubs when blank, swaps to area with the specified abbreviation
    - Specify a password to join a password locked area. (If the password matches. Obviously.)
* **getarea** 
    - Shows the current characters in your area
	- Also works as /ga.
* **getareas** 
    - Shows all characters in all areas, does not show a hub's subareas. If in hub, will only show lobby and the current hub.
	- Also works as /gas.
* **gethubs**
	- Same as **getareas**, but will always show as if not currently in hub.
* **mods**
    - Same as **getareas**, but only shows moderators
* **doc** "url" 
    - Gives the doc url if blank, updates the doc url
* **cleardoc** 
    - Clears the doc url
* **status** "status" 
    - Shows current areas status if blank, updates the status
    - Statuses: 'idle', 'rp', 'casing', 'looking-for-players'/'lfp', 'recess', 'gaming'
* **pm** "target" "Message" 
    - Currently non-functional
* **pmmute**
    - Disables all incoming PMs
* **charselect** 
    - Puts you back to char select screen
* **reload** 
    - Reloads your character ini
* **switch** "character" 
    - Quick switch to a character
* **randomchar** 
    - Randomly chooses a character
* **pos** "position" 
    - Changes your position in the area
    - Positions: Any (provided the background has it, otherwise will default to 'wit')
* **bg** "background" 
    - Changes the current background, if not an official background, server will look for it in background/custom
* **currentbg**
    - Gives user the name of the area's current background.
* **roll** "max" 
    - Rolls a 1D6 if blank
* **coinflip**
    - Flips a coin
* **currentmusic** / **music**
    - Displays the current music
* **playrandom**
    - Plays a random track from the server music list.
* **shuffle** "category"
    - Plays a random track, then plays another random track afterwards, etc.
    - Will only play from a single category if one is specified.
    - Shuffle will continue in original area if client switches areas, but will eventually stop once the client disconnects.
* **eviswap** <id1> <id2>
    - Swaps <id1> and <id2> evidence.
* **files**
    - Shows a list of anyone that's set custom character files.
* **addfiles** "link"
    - Allows user to set a link for the custom character they are currently using.
* **removefiles**
    - Removes the link for user's custom character files.
* **connectlist**
    - Shows all 'exits' for the current area.
* **autopass**
    - Toggles autopass. When enabled, an OOC broadcast will sound when the user switches areas.
    - This broadcast is visible in the area the user leaves and the area they join and details which area the user is going to or coming from, respectively.
* **musiclist**
    - View the area's current music list.
* **follow** "id"
    - Follow another user. If that user changes areas, the follower will also change areas.
    - Can be used with no arguments to check who the user is following.
    - Works with **autopass**.
* **unfollow**
    - Stop following.
* **followers**
    - Check who is following you. Will also show your followers' followers.
* **followable** "new"
    - Toggle whether users can follow you.
    - Use with argument "new" to disallow new followers without losing current followers.
* **time**
    - Show the current time and date according to the server's time.
* **serverpoll** "yay/nay"
    - View or vote on the current server poll.
* **digitalroot** "number"
    - Calculate the digital root of a given number.
* **knock** "area abbreviation"
    - Broadcast a message in the selected area that the user is knocking on their door.
* **cm**
    - Makes you a CM of the current area.
* **visible**
    - Toggles whether you will speak with a 'blank' emote.
* **areapair** "left/right/middle"
    - Area-pairs you. If you are to the right, you will "pair" with anyone on the left in your position.
* **call** "id or no argument"
    - Try to call someone or check who you're calling with.
* **acceptcall**
    - Accept an incoming call.
* **endcall**
    - End an ongoing call or reject an incoming one.
* **holdcall**
    - Holds your end of the ongoing call so you can speak to people outside the call.
* **bgslist**
    - Lists all official backgrounds on the server.

### Card Deck Commands
* **loaddecks** "name"
    - Loads a set of decks specified by the user, will list available ones. CM-only.
* **refreshdeck** "name"
    - Refreshes a deck, reverting it to its original state. CM-only.
* **deck**
    - Shows the decks in the area, including the discard pile. CM may see remaining cards in decks.
* **hand** "card number"
    - Shows the users current hand, if a card number is specified, the description (if applicable) is shown.
* **hands**
    - Shows the hands of all users in the area and the public hand. For non-CM users this will only show the area's public hand if one exists.
* **draw** "deck" "amount to draw (optional)"
    - Draws a card from the specified deck into the user's hand, optionally specific an amount to draw from it.
* **drawpublic** "deck"
    - Draws a card from the specified deck into the area's public hand.
* **takepublic** "card number"
    - Takes the card with the specified number into user's hand from the area's public hand.  
* **deal** "deck" "card number" "id"
    - Deals a specific card to any user in the area. CM-only.
* **pcard** "card number"
    - Plays the specified card, broadcasting in OOC and placing the card into the discard pile if applicable.
* **prcard** "card number"
    - Plays the specified card, broadcasting in OOC and and then returning it into its original deck, not recommended when using a deck with infinite draws.
* **clearhand**
    - Clears the user's hand of any cards.
* **cleardeck**
    - Clears the area of any card decks. CM-only.

### CM Commands
* **listenall**
    - Toggles whether you'll receive messages from remotely CM'd areas. On by default.
 * **hide** "ID/*"
    - Hides the target from /getarea and playercount.
* **unhide** "ID/*"
    - Unhides the target from /getarea and playercount, can be used by non-CM if no arguments are given.
* **allowmusic**
    - Toggles whether non-CMs are allowed to play music.
* **narrator**
    - Toggles whether you appear as if you are the Narrator character.
* **lock** "password"
    - Locks your area, preventing anyone outside of the invite list from joining.
    - Optionally, specify a password to be used with **area**.
* **unlock**
    - Unlocks your area.
* **iclock**
    - If area is unlocked, make area spectatable and disallow everyone but CMs from speaking IC.
    - If area is locked, disallow everyone from speaking without making area spectatable.
* **areakick** "ID/*" [area]
    - Kicks target and all of their multi-accs from your area to area 0 or specified [area] and removes them from invite-list should the area be locked.
    - Use "*" to kick everyone who isn't a CM or you.
* **invite** "ID"
    - Adds target to the invite list of your area.
* **uninvite** "ID"
    - Removes target from invite list of your area.
* **forcepos** "position" [target]
    - Forcibly change [target]'s position. Leave blank to affect everyone in area.
    - Positions: 'def', 'pro', 'hld', 'hlp', 'jud', 'wit'
* **connect** "area ID"
    - Sets an 'exit' for the current area. Clients can only leave the area through said 'exits'.
* **biconnect** "area ID"
    - Same as connect, but two-way.
* **disconnect** "area ID"
    - Removes an 'exit' from the current area.
* **bidisconnect** "area ID"
    - Same as disconnect, but two-way.
* **clearconnect**
    - Clears all 'exits' for the current area.
* **play** "song file name incl. extension" "length in seconds"
    - Plays a song from `music/custom`.
    - Optionally, specify the length in seconds for the song to loop server-side.
* **addmusic** "song file name incl. extension" "length in seconds"
    - Adds tracks to the area music list. Tracks must be located in `music/custom`.
* **addcategory** "name"
	- Adds a category to the area's music list.
* **clearmusiclist**
    - Clear the current area's music list.
* **storemlist** "name"
    - Store a music list on the server with the specified name.
* **loadmlist** "name"
    - Load a stored music list from the server with the specified name.
* **playl** "track number"
    - Plays the specified track from the area's music list. Will loop server-side according to the length provided by **addmlist**.
* **hidecount**
    - Hides the playercount for the current area.
    - Note: player count is only hidden from clients outside the area.
* **rename** "new name"
    - Rename the current area, must be a subarea in a hub.
* **removearea**
    - Destroy the current area, must be a subarea in a hub.
* **savehub** "name"
	- Saves a hub with the specified name.
* **loadhub** "name"
	- Loads a previously saved hub with the specified name.
* **clearhub**
	- Clears a hub of all it's areas.
* **hubstatus* "status"
	- Same as status, but affects all areas in a hub.
* **shouts**
    - Toggle shouts in the current area.
* **hide** "id"
    - Hide the specified client from /getarea and the server playercount.
    - Use `*` instead of an ID to hide all players in the area.
* **unhide** "id"
    - Unhide the specified client.
    - Use `*` instead of an ID to unhide all players in the area.
    - This can be used by non-CMs with no arguments to unhide themselves.
* **poslock** "pos/clear"
    - Allow only the specified position(s) to be used.
	- Use with no arguments to what positions the area is locked.
    - Using "clear" as an argument clears the poslock.
* **loop**
	- Toggles server-side looping. While on, allows new clients joining an area to hear a set song once it loops without needing to play it themselves.
* **timer** \<id> [+/-][x in seconds, minutes, hours etc.] | \<id> start | \<id> \<pause|stop> | \<id> hide
    - Manage a countdown timer in the current area. Note that timer of ID 0 is global. All other timer IDs are local to the area.
* **areadesc** "your description here"
	- Sets a description that will be sent to every client that enters the area, use without argument to check what the current is, if any.
* **clearareadesc**
	- Will clear the area's description if it has one.
* **movetime** "time in seconds"
	- Sets how long it takes to enter the area, only works in hubs you CM. if used in the hub's main area it will apply to every sub-area. setting this to 0 clears it.
* **ambiance** "track to play"
	- Plays ambiance that will alongside music, looks in the music folder by default, but you can also stream or use the "rain" preset.
* **clearambiance**
	- Clears any ambiance currently playing in the area.

#### Testimony Recording
* A new feature in tsuserverCC - you can now record testimonies and play them back with automatic formatting!
* You can now record your testimonies by putting in IC `//[Your Testimony Title]`. Formatting works just as normal, and this will automatically do the WT woosh.
* While recording, you can add new statements by putting in IC `+[Your Statement]`. These will show up as if you're just normally testifying for the first time. 
    - If you're paired and want your partner to have a statement, have the pair add the statement instead. (Make sure they are also a CM.)
* Once you're done recording your testimony, just do `/end`. After this, you can do `///` in IC to make the title appear again, this time with a CE woosh.
* After all that, anyone in the area can say `>` in IC to move to the next statement or `<` for the previous statement, `=` is also available to use to see the current statement again.
* If a statement is particularly long, you can say `>>` or `<<` to speed it up. You can also skip to a statement with `>[statement number]` or speed it up with `>>[statement number]`.
* All the statements will be automatically displayed in green.
* The CM can at this point  add 'substatements' by using +[statement] again, and can also amend the current statement by using &[amended statement].
* If you want to clear the testimony, use /cleartestimony in OOC. For viewing the current testimony, simply do /testimony in OOC.

### Mod Commands
* **login**
    - Logs in as a mod or admin depending on set privileges with /addmod.
* **gm** "Message" 
    - Sends a serverwide message with mod tag
* **lm** "Message" 
    - Sends an area OOC message with mod tag
* **judgelog** 
    - Displays the last judge actions in the current area
* **announce** "Message" 
    - Sends a serverwide announcement
* **charselect** "ID"
    - Kicks a player back to the character select screen. If no ID was entered then target yourself.
* **kick** "IPID" 
    - Kicks the targets with this IPID.
* **ban** "IPID" "reason" "length"
    - Bans the specified IPID for the specified length of time. If no time is specified, ban will default to six hours.
    - All arguments must be wrapped in double quotes.
    - Length syntax is as follows: `"[num] [seconds/minutes/hours/days/weeks] | perma"`.
* **banhdid** "IPID" "reason" "length"
    - "Old-style" HDID ban. This will ban both the specified IPID and the associated HDID.
    - All arguments must be wrapped in double quotes.
    - Length syntax is the same as ||ban||.
* **unban** "ban ID" 
    - Unbans the specified ban ID.
* **mute** "Target" 
    - Mutes the target from all IC actions, targets IPID.
* **unmute** "Target","all" 
    - Unmutes the target, "all" will unmute all muted clients
* **oocmute** "Target" 
    - Mutes the target from all OOC actions via ID.
* **oocunmute** "Target" 
    - Unmutes the target.
* **bans**
    - Returns the five most recent bans.
* **baninfo** "ban id" "['ban_id'|'ipid'|'hdid']"
    - Returns requested information about the specified Ban ID from the database.
* **permit** "id"
    - Toggles granting specified client special permissions.
* **setserverpoll** "poll"
    - Set the current server poll, and announce it globally.
* **setserverpoll** "poll"
    - Clear the current server poll, and announce it globally.
* **bglock** 
    - Toggles the background lock in the current area
* **disemvowel** "Target"
    - Removes the vowels from everything said by the target
* **undisemvowel** "Target"
    - Lifts the disemvowel curse from the target
* **blockdj** "target"
    - Mutes the target from changing music. 
* **unblockdj** "target"
    - Undo previous command.
* **blockwtce** "target"
    - Blocks the target from using Witness Testimony/Cross Examination signs.
* **unblockwtce** "target"
    - Undo previous command.
* **evidencemod** <MOD>
    - Changes evidence_mod in this area. Possible values: FFA, CM, HiddenCM, Mods
        * **FFA**
            - Everyone can add, edit and remove evidence.
        * **Mods**
            - Only moderators can add, edit or remove evidence.
        * **CM**
            - Only CM (case-maker, look at /cm for more info) or moderators can add, edit or remove evidence.
        * **HiddenCM**
            - Same as CM, but every evidence has a preset "owner's position" which can be set by a CM or moderator, such that only one side/position of the court may see the evidence. After presenting the evidence, the position of the evidence changes to "all." Possible positions include def (defense), pro (prosecutor), wit (witness), jud (judge), pos (hidden from everyone), and all (everyone can see the evidence).
* **allowiniswap**
    - Toggle allow_iniswap var in this area. 
    - Even if iniswap at all is forbidden you can configure all-time allowed iniswaps in *iniswaps.yaml*
* **ghost**
    - Toggles whether the moderator is visible in /getarea and playercount.
* **unmod**
    - Revokes moderator credentials from the user.

### Admin Commands
* **addmod** "ID" "name" "admin (optional for admin status)"
    - Adds a mod/admin's credentials so they can use /login.
* **removemod** "name"
    - Revokes a mod/admin's credentials based on the name they were added with.

## License

This server is licensed under the AGPLv3 license. In short, if you use a modified version of tsuserverCC, you *must* distribute its source licensed under the AGPLv3 as well, and notify your users where the modified source may be found. The main difference between the AGPL and the GPL is that for the AGPL, network use counts as distribution. If you do not accept these terms, you should use [serverD](https://github.com/Attorney-Online-Engineering-Task-Force/serverD), which uses GPL rather than AGPL.

See the [LICENSE](LICENSE.md) file for more information.