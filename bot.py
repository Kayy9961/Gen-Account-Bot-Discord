import discord
from discord import app_commands
from discord.ext import tasks
import asyncio
import json
import os
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.members = True
intents.messages = True

class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.cooldowns = {}
        self.COOLDOWN_FILE = 'cooldowns.json'
        self.ROLES_CONFIG = {
            'Normal': {
                'file': 'cuentas/normal.txt',
                'cooldown': 30 * 60,
                'emoji': '🔵'
            },
            'Premiun': {
                'file': 'cuentas/premium.txt',
                'cooldown': 5 * 60,
                'emoji': '🟡'
            },
            'Diamante': {
                'file': 'cuentas/diamante.txt',
                'cooldown': 6 * 60,
                'emoji': '💎'
            }
        }

    async def setup_hook(self):
        if os.path.exists(self.COOLDOWN_FILE):
            with open(self.COOLDOWN_FILE, 'r') as f:
                self.cooldowns = json.load(f)
        else:
            self.cooldowns = {}
        await self.tree.sync()
        self.save_cooldowns.start()

    async def on_ready(self):
        print(f'Bot conectado como {self.user}')

    @tasks.loop(minutes=1)
    async def save_cooldowns(self):
        with open(self.COOLDOWN_FILE, 'w') as f:
            json.dump(self.cooldowns, f)

    async def on_command_error(self, ctx, error):
        print(f'Error: {error}')

bot = MyBot()

@bot.tree.command(name="generar", description="Genera una cuenta según tu rol.")
async def generar(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    member = interaction.user

    user_role = None
    role_emoji = ''
    for role_name, config in bot.ROLES_CONFIG.items():
        role = discord.utils.get(member.roles, name=role_name)
        if role:
            user_role = role_name
            role_emoji = config['emoji']
            break

    if not user_role:
        embed = discord.Embed(
            title="❌ Error",
            description="No tienes un rol válido para usar este comando.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    current_time = datetime.utcnow().timestamp()
    if user_id in bot.cooldowns:
        last_time = bot.cooldowns[user_id]
        elapsed = current_time - last_time
        required = bot.ROLES_CONFIG[user_role]['cooldown']
        if elapsed < required:
            remaining_seconds = int(required - elapsed)
            remaining = str(timedelta(seconds=remaining_seconds))
            embed = discord.Embed(
                title="⏳ Cooldown Activo",
                description=f"Debes esperar **{remaining}** antes de usar este comando nuevamente.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
    file_path = bot.ROLES_CONFIG[user_role]['file']
    if not os.path.exists(file_path):
        embed = discord.Embed(
            title="⚠️ Sin Cuentas",
            description="No hay cuentas disponibles en este momento.",
            color=discord.Color.dark_gray()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    with open(file_path, 'r') as f:
        lines = f.readlines()

    if not lines:
        embed = discord.Embed(
            title="⚠️ Sin Cuentas",
            description="No hay cuentas disponibles en este momento.",
            color=discord.Color.dark_gray()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    account = lines[0].strip()
    embed_dm = discord.Embed(
        title=f"🎉 Cuenta Generada",
        description=f"**Rol:** {role_emoji} {user_role}\n**Cuenta:** `{account}`",
        color=discord.Color.green(),
        timestamp=datetime.utcnow()
    )
    embed_dm.set_footer(text="¡Disfruta tu cuenta!")

    try:
        await member.send(embed=embed_dm)
    except discord.Forbidden:
        embed = discord.Embed(
            title="❌ Error al Enviar DM",
            description="No puedo enviarte mensajes privados. Por favor, habilita los DMs",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    with open(file_path, 'w') as f:
        f.writelines(lines[1:])
    bot.cooldowns[user_id] = current_time
    embed_response = discord.Embed(
        title="✅ ¡Cuenta Enviada!",
        description="He enviado una cuenta a tus mensajes privados. Revisa tus DMs",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    embed_response.set_thumbnail(url=member.display_avatar.url)
    await interaction.response.send_message(embed=embed_response, ephemeral=True)
BOT_TOKEN = 'EL TOKEN DE TU BOT DE DISCORD'
bot.run(BOT_TOKEN)
