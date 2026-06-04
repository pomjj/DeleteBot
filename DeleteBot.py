import discord
from discord.ext import commands
from discord.ui import Select, View, Button
import os
from flask import Flask
from threading import Thread


app = Flask('')

@app.route('/')
def home():
    return "DeleteBot Online!"

def run_web():
    app.run(host='0.0.0.0', port=10000) # Render  10000 default
def keep_alive():
    t = Thread(target=run_web)
    t.start()
# ===============================================

intents = discord.Intents.default()
intents.message_content = True 
intents.guilds = True           

bot = commands.Bot(command_prefix="!", intents=intents)

class ChannelDeleteSelect(Select):
    def __init__(self, channels):
        options = []
        for channel in channels:
            if isinstance(channel, discord.TextChannel):
                icon, c_type = "💬", "Text"
            elif isinstance(channel, discord.VoiceChannel):
                icon, c_type = "🔊", "Voice"
            elif isinstance(channel, discord.CategoryChannel):
                icon, c_type = "📁", "categories"
            elif isinstance(channel, discord.StageChannel):
                icon, c_type = "🎭", "Tribune"
            else:
                icon, c_type = "🔗", "Channel"

            options.append(discord.SelectOption(
                label=f"{channel.name}"[:100],
                description=f"Type: {c_type}",
                value=str(channel.id),
                emoji=icon
            ))

        super().__init__(
            placeholder="1. Select channels from the list...",
            min_values=1,
            max_values=len(options),
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.selected_channels = self.values
        self.view.delete_button.disabled = False
        await interaction.response.edit_message(view=self.view)

class PaginatedView(View):
    def __init__(self, all_channels, page=0):
        super().__init__(timeout=300)
        self.all_channels = all_channels
        self.page = page
        self.per_page = 25
        self.selected_channels = []

        start = self.page * self.per_page
        end = start + self.per_page
        current_channels = self.all_channels[start:end]

        self.add_item(ChannelDeleteSelect(current_channels))

        self.delete_button = Button(label="Delete selected", style=discord.ButtonStyle.danger, disabled=True)
        self.delete_button.callback = self.confirm_delete
        self.add_item(self.delete_button)

        self.add_item(Button(label=f"Page. {self.page + 1}", style=discord.ButtonStyle.gray, disabled=True))
        
        btn_back = Button(label="⬅️ Back", style=discord.ButtonStyle.secondary, disabled=(self.page == 0))
        btn_back.callback = self.back_button
        self.add_item(btn_back)

        max_pages = (len(all_channels) - 1) // self.per_page
        btn_next = Button(label="Forward ➡️", style=discord.ButtonStyle.secondary, disabled=(self.page >= max_pages))
        btn_next.callback = self.next_button
        self.add_item(btn_next)

    async def back_button(self, interaction: discord.Interaction):
        self.page -= 1
        await interaction.response.edit_message(view=PaginatedView(self.all_channels, self.page))

    async def next_button(self, interaction: discord.Interaction):
        self.page += 1
        await interaction.response.edit_message(view=PaginatedView(self.all_channels, self.page))

    async def confirm_delete(self, interaction: discord.Interaction):
        deleted_count = 0
        for channel_id in self.selected_channels:
            channel = interaction.guild.get_channel(int(channel_id))
            if channel:
                try:
                    await channel.delete()
                    deleted_count += 1
                except:
                    pass
        
        await interaction.message.delete()
        await interaction.response.send_message(f"✅ Objects deleted: {deleted_count}", ephemeral=True, delete_after=5)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def cleanup(ctx):
    all_channels = sorted(ctx.guild.channels, key=lambda x: (not isinstance(x, discord.CategoryChannel), x.position))
    all_channels = [c for c in all_channels if c.id != ctx.channel.id]

    if not all_channels:
        await ctx.send("Channels not found.")
        return

    view = PaginatedView(all_channels)
    await ctx.send("**Select the channels you want to delete**\n*After making a selection, press the red button*", view=view)
    
    try:
        await ctx.message.delete()
    except:
        pass

@bot.event
async def on_ready():
    print(f'Bot {bot.user} started ')

# start
if __name__ == "__main__":
    keep_alive() 
    token = os.environ.get('DISCORD_TOKEN') 
    if token is None:
        token = "token_bot"
    
    bot.run("Token_bot")