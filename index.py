import discord
from discord.ext import commands
import asyncio
import os
from discord import app_commands 
from typing import Optional
import re 
import time
from dotenv import load_dotenv
load_dotenv()
MAIN_GUILD_ID = discord.Object(id=1397175419664470031)
TARGET_ROLE_ID = 1442769995783475292  
TARGET_CATEGORY_ID = 1442769574285283399 
SECOND_GUILD_ID_INT = 1450079520756465758 
ROLES_TO_REMOVE = [
    1434043875445702656,
    1408433140363432006,
    1397191419361230970,
    1408419247163576330,
    1397191790381236304,
    1463754309245337672,
    1462487968705937418
]

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
temp_saved_roles = {}
def convert_time(time_str):
    time_str = time_str.lower().replace(" ", "")
    total_seconds = 0
    matches = re.findall(r"(\d+)([dhms])", time_str)
    if not matches: return -1
    for val, unit in matches:
        val = int(val)
        if unit == 's': total_seconds += val
        elif unit == 'm': total_seconds += val * 60
        elif unit == 'h': total_seconds += val * 3600
        elif unit == 'd': total_seconds += val * 86400
    return total_seconds if total_seconds > 0 else -1

def parse_monkeys(guild: discord.Guild, monkeys: str) -> list[discord.Member]:
    members = []
    id_pattern = re.compile(r'<@!?(\d+)>')
    parts = re.split(r'[,\s]+', monkeys.strip())
    for part in parts:
        if not part: continue
        match = id_pattern.match(part)
        member_id = int(match.group(1)) if match else (int(part) if part.isdigit() else None)
        if member_id:
            member = guild.get_member(member_id)
            if member and member not in members: members.append(member)
    return members

async def restore_roles(guild, member):
    if member.id in temp_saved_roles:
        role_ids = temp_saved_roles[member.id]
        roles_to_add = [guild.get_role(rid) for rid in role_ids if guild.get_role(rid)]
        if roles_to_add:
            try: await member.add_roles(*roles_to_add)
            except: pass
        del temp_saved_roles[member.id]

async def perform_radao(interaction, member, seconds, period, reason):
    guild = interaction.guild
    role_radao = guild.get_role(TARGET_ROLE_ID)
    category = guild.get_channel(TARGET_CATEGORY_ID)
    
    if not role_radao or not category: return

    roles_to_remove = [r for r in member.roles if r.id in ROLES_TO_REMOVE]
    if roles_to_remove:
        temp_saved_roles[member.id] = [r.id for r in roles_to_remove]
        try: await member.remove_roles(*roles_to_remove, reason="Radao")
        except: pass

    try:
        await member.add_roles(role_radao, reason=reason)
        end_time_timestamp = int(time.time() + seconds)
        discord_timestamp = f"<t:{end_time_timestamp}:R>" 
        full_date_timestamp = f"<t:{end_time_timestamp}:F>"

        channel = await guild.create_text_channel(
            name=f"dao-khi-{member.display_name}", 
            category=category,
            topic=f"ID: {member.id} | Ra đảo vì: {reason}"
        )
        
        await channel.set_permissions(member, read_messages=True, send_messages=True)
        await channel.send(f"Chào mừng {member.mention}! Bạn sẽ được thả tự do {discord_timestamp} ({full_date_timestamp}).")
        try:
            await channel.send(f"Mày ra đảo vì **{reason}**")
            await channel.send("Ngồi đây bị Rick Lăn nhé :Đ!")
            await channel.send("https://tenor.com/view/rickroll-roll-rick-never-gonna-give-you-up-never-gonna-gif-22954713")
        except Exception:
            await channel.send(f"Lần này méo có rick roll mày may đấy")

        await asyncio.sleep(seconds)
        
        if role_radao in member.roles:
            await member.remove_roles(role_radao)
            await restore_roles(guild, member)
        if channel: await channel.delete()
    except Exception as e:
        print(f"Lỗi quy trình: {e}")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------ BẮT ĐẦU ĐỒNG BỘ LỆNH ------')
    bot.tree.clear_commands(guild=None)
    await bot.tree.sync(guild=None)
    print(">> Đã xóa sạch lệnh Global cũ (Fix lỗi trùng lệnh).")
    # try:
    #     await bot.load_extension('second_sever')
    #     print(">> Đã tải Extension Second Server.")
    # except Exception as e:
    #     print(f"!! Lỗi tải extension: {e}")
    try:
        synced = await bot.tree.sync(guild=MAIN_GUILD_ID)
        print(f">> Server Chính (ID: {MAIN_GUILD_ID.id}): Đã sync {len(synced)} lệnh (/radao, /vebo).")
    except Exception as e:
        print(f"!! Lỗi Sync Server Chính: {e}")
    guild_2 = bot.get_guild(SECOND_GUILD_ID_INT)
    if guild_2:
        print(f">> Đã tìm thấy Server Phụ: {guild_2.name} (ID: {guild_2.id})")
    else:
        print(f"!! CẢNH BÁO: Bot KHÔNG tìm thấy Server Phụ có ID {SECOND_GUILD_ID_INT}.")
        print("   -> Kiểm tra lại ID Server hoặc mời Bot vào Server đó.")
    print('------ HOÀN TẤT ------')

@bot.tree.command(name="radao", description="Cho khỉ ra đảo.", guild=MAIN_GUILD_ID)
@app_commands.describe(monkeys='Tag hoặc ID', period='VD: 10m, 1h', reason='Lý do')
@commands.has_permissions(administrator=True)
async def radao(interaction: discord.Interaction, monkeys: str, period: str, reason: str = "Thằng ban thích thì cho thôi"):
    seconds = convert_time(period)
    if seconds == -1: return await interaction.response.send_message("Sai thời gian (vd: 10m, 1h).", ephemeral=True)
    
    targets = parse_monkeys(interaction.guild, monkeys)
    if not targets: return await interaction.response.send_message("Không tìm thấy người dùng.", ephemeral=True)
    
    await interaction.response.defer()
    msg = []
    for m in targets:
        if m.top_role >= interaction.user.top_role: 
            msg.append(f"Bỏ qua {m.mention} (Role cao).")
            continue
        asyncio.create_task(perform_radao(interaction, m, seconds, period, reason))
        msg.append(f"Bonk🔨 bà zà mài {m.mention} ra đảo trong {period} vì {reason}.")
    
    await interaction.followup.send("\n".join(msg))

@bot.tree.command(name="vebo", description="Đưa khỉ về bờ.", guild=MAIN_GUILD_ID)
@commands.has_permissions(administrator=True)
async def vebo(interaction: discord.Interaction, monkeys: str):
    targets = parse_monkeys(interaction.guild, monkeys)
    if not targets: return await interaction.response.send_message("Không tìm thấy ai.", ephemeral=True)
    
    await interaction.response.defer()
    role = interaction.guild.get_role(TARGET_ROLE_ID)
    msg = []
    for m in targets:
        if role in m.roles:
            await m.remove_roles(role)
            await restore_roles(interaction.guild, m)
            msg.append(f"Đã về bờ: {m.mention}")
            cat = interaction.guild.get_channel(TARGET_CATEGORY_ID)
            if cat:
                for c in cat.text_channels:
                    if str(m.id) in c.topic or str(m.id) in c.name:
                        await c.delete()
        else:
            msg.append(f"{m.mention} không ở đảo.")
    await interaction.followup.send("\n".join(msg))
bot.run(os.getenv('TOKEN'))
