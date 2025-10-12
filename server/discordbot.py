import asyncio
import discord
import yaml
from discord.ext import commands, tasks
from discord.utils import escape_markdown, find
from discord.errors import Forbidden, HTTPException
import time

class Commandbot(commands.Bot):
    # AO2 Command Bot
    def __init__(self, server):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents = intents)
        self.server = server
        self.queue_whitelist_requests = []
        self.server_name = self.server.config['masterserver_name']
        self.is_wl_prompting_user = False

    async def init(self, token):
        # starts bot
        print("Trying to start Discord command bot...")
        try:
            await self.start(token)
        except Exception as e:
            print(e)
    
    class WhitelistButton(discord.ui.View):
        def __init__(self, bot_details, requested_user: discord.Member):
            super().__init__(timeout=120)
            self.bot_details = bot_details
            self.requested_user: discord.Member = requested_user
            self.has_whitelisted: bool = False
            self.message: discord.Message | None = None

        @discord.ui.button(label="Whitelist Self", style=discord.ButtonStyle.blurple)
        async def button_callback(self, interaction: discord.Interaction, _button):
            await self.notify_ao_client()  # This notifies the AO Client and make the necessary adjustments to whitelist the player.
            embed = discord.Embed(color=discord.Color.random(),
                                  title="[Whitelist Success!]",
                                  description=f"Welcome to {self.bot_details.server_name}, {interaction.user.mention}!")
            try:
                await interaction.response.edit_message(content=None, view=None, embed=embed)
            except Exception as e:
                await interaction.response.send_message("Honestly, I don't know how you got here but congrats. "
                                                  "Ping Yuzuru for this tbh along with the error.", e)

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            # To make the button work, this needs to return True.
            try:
                if self.requested_user.id == interaction.user.id:
                    if await self.get_ao_clients():  # This ensures the AO client does exist. 
                        self.has_whitelisted = True  # This ensures the message doesn't tweak due to timeout.
                        return True
                        
                    else:  # When it doesn't find anything.
                        await interaction.response.send_message(f"Your client is not found in {self.bot_details.server_name}!", ephemeral=True, delete_after=15)
                        
                else:  # When someone tries to press someone else's buttons.
                    await interaction.response.send_message(f"**Shoot yourself {interaction.user.mention} (in-game) for pressing {self.requested_user.name}'s Prompt**", delete_after=5)

            except discord.InteractionResponded:  # On the off-chance this was pressed more than once.
                await interaction.response.send_message("You have clicked more than once, please wait.", ephemeral=True, delete_after=5)
            return False

        async def on_timeout(self) -> None:
            if not self.has_whitelisted:
                embed = discord.Embed(color=discord.Color.random(),
                                    title="[Whitelist Timed Out!]",
                                    description=f"Retry the Whitelist Procedure through {self.bot_details.server_name}.")
                await self.message.edit(content=None, view=None, embed=embed, delete_after=120)
        
        async def get_ao_clients(self):
            clients = list()
            for c in self.bot_details.server.client_manager.clients:
                # God forgive me for this.
                if c.discord_name == self.requested_user.name:  # This ensures that the requestee is in the server.
                    if not c.is_wlisted:  # This ensures that they are not whitelisted yet.
                        if c.wlrequest:  # This ensures that they have requested for a whitelist.
                            clients.append(c)
            return clients

        async def notify_ao_client(self):
            clients = await self.get_ao_clients()
            for client in clients:
                client.is_wlisted = True
                client.discord_name = self.requested_user.name
                client.send_ooc(f"Whitelisted as {client.discord_name}.")
                client.whitelist_trust()


    async def whitelist_prompt(self, client, requested_user: str) -> None:
        if self.server.config['commandbot']['whitelist_channel'] == '':
            return

        # This entire process is to check if channel and member exists. And once validated, things go through normally.
        requested_user = requested_user.strip().lower()
        get_channel = self.get_channel(self.server.config['commandbot']['whitelist_channel'])
        if get_channel:
            get_guild = get_channel.guild
            member = find(lambda m: m.name.lower() == requested_user, get_guild.members)
            if member:
                wl_button = self.WhitelistButton(bot_details=self, requested_user=member)
                seconds_before_timeout = round(time.time()) + wl_button.timeout
                timeout_left_string = f"<t:{seconds_before_timeout}:R>"
                embed = discord.Embed(color=discord.Color.random(),
                                      title="[Whitelist Prompt]",
                                      description=f"{client.char_name} ({member.mention}) has requested to be whitelisted!\n"
                                                  f"Please press the button to confirm this action.")

                embed.add_field(name="Prompt Ends In:", value=timeout_left_string, inline=True)
                wl_button.message = await get_channel.send(embed=embed, view=wl_button)
            else:
                client.send_ooc(f"{requested_user} is not an existing member in the {self.server_name} Discord Server.")
        else:
            client.send_ooc(f"ERR: Whitelist Channel in Discord Server not found. Please contact {self.server_name} Staff.")

    def add_commands(self):
        @self.tree.command()
        async def getplayers(interaction: discord.Interaction):
            if not interaction.guild:
                await interaction.response.send_message("You may not send commands through DMs!")
                return
            await interaction.response.send_message(f"There are {int(self.server.player_count)} players on Case Cafe!")           
        
    async def on_ready(self):
        print("Discord Bot successfully logged in.")
        print("Username -> " + self.user.name)
        print("ID -> " + str(self.user.id))
        try:
            await self.tree.sync()
            print("Synced commands!")
        except Exception as e:
            print(e)
        self.guild = self.guilds[0]
        await self.wait_until_ready()
    
        self.auto_check_whitelist_prompt.start()
            
    @tasks.loop(seconds=1)
    async def auto_check_whitelist_prompt(self):
        if not self.is_wl_prompting_user:  # This ensures the task is not running when this function is called.
            if len(self.queue_whitelist_requests) > 0:  # Ensures there's something here...
                self.is_wl_prompting_user = True
                await self.whitelist_prompt(*self.queue_whitelist_requests.pop())
                await asyncio.sleep(0.25)
                self.is_wl_prompting_user = False
