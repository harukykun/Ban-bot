import discord
from discord.ext import commands
import asyncio
import os
from discord import app_commands 
from typing import Optional
import re 
import time

TARGET_ROLE_ID = 1442769995783475292  
TARGET_CATEGORY_ID = 1442769574285283399 
GIF_STICKER_ID = 1443617401538347108     

ROLES_TO_REMOVE = [
    1434043875445702656,
    1408433140363432006,
    1397191419361230970,
    1408419247163576330,
    1397191790381236304
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
    found_valid = False
    for val, unit in matches:
        val = int(val)
        found_valid = True
        if unit == 's': total_seconds += val
        elif unit == 'm': total_seconds += val * 60
        elif unit == 'h': total_seconds += val * 3600
        elif unit == 'd': total_seconds += val * 86400
        
    return total_seconds if found_valid and total_seconds > 0 else -1

def parse_monkeys(guild: discord.Guild, monkeys: str) -> list[discord.Member]:
    members = []
    id_pattern = re.compile(r'<@!?(\d+)>')
    parts = re.split(r'[,\s]+', monkeys.strip())
    
    for part in parts:
        if not part: continue
        
        member_id = None
        match = id_pattern.match(part)
        if match:
            member_id = int(match.group(1))
        else:
            try:
                member_id = int(part)
            except ValueError:
                continue 
        
        if member_id:
            member = guild.get_member(member_id)
            if member and member not in members:
                members.append(member)
    return members

async def restore_roles(guild, member):
    if member.id in temp_saved_roles:
        role_ids = temp_saved_roles[member.id]
        roles_to_add = []
        for r_id in role_ids:
            role = guild.get_role(r_id)
            if role: roles_to_add.append(role)
        
        if roles_to_add:
            try: await member.add_roles(*roles_to_add)
            except Exception as e: print(f"Lỗi trả role: {e}")
        del temp_saved_roles[member.id]

async def perform_radao(interaction: discord.Interaction, member: discord.Member, seconds: int, period: str, reason: str):
    guild = interaction.guild
    role_radao = guild.get_role(TARGET_ROLE_ID)
    category = guild.get_channel(TARGET_CATEGORY_ID)

    if not role_radao or not category:
        print(f"Lỗi cấu hình ID. Không thể ban {member.display_name}")
        return
    removed_roles_list = []
    roles_to_remove_objects = []
    
    for user_role in member.roles:
        if user_role.id in ROLES_TO_REMOVE:
            removed_roles_list.append(user_role.id)
            roles_to_remove_objects.append(user_role)
    
    if removed_roles_list:
        temp_saved_roles[member.id] = removed_roles_list
        try:
            await member.remove_roles(*roles_to_remove_objects, reason=f"[Radao] {reason}")
        except Exception as e:
            print(f"Không thể gỡ role chỉ định cho {member.display_name}: {e}")
    try:
        await member.add_roles(role_radao, reason=f"[Radao] {reason}")
        channel_name = f"dao-khi-cua-{member.display_name}"
        created_channel = None
        end_time_timestamp = int(time.time() + seconds)
        discord_timestamp = f"<t:{end_time_timestamp}:R>" 
        full_date_timestamp = f"<t:{end_time_timestamp}:F>"
        try:
            created_channel = await guild.create_text_channel(
                name=channel_name,
                category=category, 
                topic=f"ID: {member.id} | Đảo khỉ của {member.display_name} - Lý do ra đảo: {reason}"
            )
            
            await created_channel.set_permissions(member, read_messages=True, send_messages=True, read_message_history=True)
            await created_channel.send(f"Chào mừng {member.mention}! Bạn sẽ được thả tự do {discord_timestamp} ({full_date_timestamp}).")

            try:
                await created_channel.send(f"Mày ra đảo vì **{reason}**")
                await created_channel.send("Ngồi đây bị Rick Lăn nhé :Đ!")
                await created_channel.send("https://tenor.com/view/rickroll-roll-rick-never-gonna-give-you-up-never-gonna-gif-22954713")
            except Exception as e:
                print(f"Lỗi gửi link cho {member.display_name}: {e}")
                await created_channel.send(f"Lần này méo có rick roll mày may đấy")
            
        except Exception as e:
            print(f"Lỗi tạo kênh cho {member.display_name}: {e}")
        await asyncio.sleep(seconds)
        member = guild.get_member(member.id) 
        if member and role_radao in member.roles:
            try:
                await member.remove_roles(role_radao, reason="Hết giờ ra đảo") 
                await restore_roles(guild, member)
            except Exception as e:
                print(f"Lỗi khi unban/trả role cho {member.display_name}: {e}")
            
        if created_channel:
             try:
                await created_channel.delete()
             except Exception as e:
                print(f"Lỗi xóa kênh cho {member.display_name}: {e}")
                
    except Exception as e:
        print(f"Lỗi cấp role Radao cho {member.display_name}: {e}")

@bot.event
async def on_ready():
    print(f'Bot đã sẵn sàng: {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Đã đồng bộ hóa {len(synced)} lệnh Slash Commands.")
    except Exception as e:
        print(f"Lỗi đồng bộ hóa lệnh Slash: {e}")

@bot.tree.command(name="radao", description="Đưa một con khỉ ra đảo để chiêm nghiệm cuộc đời.")
@app_commands.describe(
    monkeys='Các con khỉ cần ra đảo (dùng mention @, ID, cách nhau bởi khoảng trắng hoặc dấu phẩy)',
    period='Thời gian ra đảo (vd: 1h30m, 10s, 1d2h)',
    reason='Nguyên nhân lùi hóa'
)
@commands.has_permissions(administrator=True) 
async def radao_slash(interaction: discord.Interaction, monkeys: str, period: str, reason: Optional[str] = None): 
    if reason is None:
        reason = "Thằng ban thích thì cho ra đảo thôi!"
        
    seconds = convert_time(period)
    if seconds == -1:
        await interaction.response.send_message("Sai định dạng thời gian (vd: 1h30m, 90s, 1d).", ephemeral=True)
        return
        
    guild = interaction.guild
    members_to_process = parse_monkeys(guild, monkeys)
    
    if not members_to_process:
        await interaction.response.send_message("Không tìm thấy thành viên hợp lệ nào trong danh sách. Vui lòng sử dụng mention (@user) hoặc ID.", ephemeral=True)
        return
    await interaction.response.defer() 

    banned_members = []
    skipped_members = []
    role_radao = guild.get_role(TARGET_ROLE_ID)
    
    for member in members_to_process:
        
        is_skipped = False
        skip_reason = ""
        
        if member.id == interaction.user.id:
            skip_reason = "Tự ban"
            is_skipped = True
        elif member.id == interaction.guild.owner_id:
            skip_reason = "Chủ server"
            is_skipped = True
        elif member.top_role >= interaction.user.top_role:
            skip_reason = "Role cao hơn/bằng"
            is_skipped = True
        
        if role_radao and role_radao in member.roles:
            skip_reason = "Đã ở đảo"
            is_skipped = True

        if is_skipped:
            skipped_members.append(f"**{member.display_name}** ({skip_reason})")
            continue

        asyncio.create_task(perform_radao(interaction, member, seconds, period, reason))
        banned_members.append(f"**{member.display_name}**")

    response_message = ""
    if banned_members:
        response_message += f"**Bonk 🔨** {len(banned_members)} khỉ ra đảo trong **{period}** vì: **{reason}**.\n"
    if skipped_members:
        if banned_members: response_message += "\n"
        response_message += f"**Tha cho** {len(skipped_members)} khỉ:\n"
        response_message += "Danh sách: " + ", ".join(banned_members) + "\n"
    if not banned_members and not skipped_members:
         response_message = "Không có thành viên hợp lệ nào được tìm thấy hoặc tất cả đều không thể bị ban."

    await interaction.followup.send(response_message)

@bot.tree.command(name="vebo", description="Dùng thuốc tiến hóa lên con khỉ đang ở đảo.")
@app_commands.describe(
    monkeys='Các con khỉ cần thuốc (dùng mention @, ID, cách nhau bởi khoảng trắng hoặc dấu phẩy)'
)
@commands.has_permissions(administrator=True)
async def vebo_slash(interaction: discord.Interaction, monkeys: str):
    guild = interaction.guild
    role_radao = guild.get_role(TARGET_ROLE_ID)
    category = guild.get_channel(TARGET_CATEGORY_ID)

    members_to_process = parse_monkeys(guild, monkeys)
    
    if not members_to_process:
        await interaction.response.send_message("Không tìm thấy thành viên hợp lệ nào trong danh sách.", ephemeral=True)
        return

    await interaction.response.defer()

    unbanned_members = []
    skipped_members = []
    
    for member in members_to_process:
        if role_radao and role_radao in member.roles:
            try:
                await member.remove_roles(role_radao, reason="Tiêm thuốc (Về bờ)") 
                await restore_roles(guild, member)
                unbanned_members.append(f"**{member.display_name}**")
            except Exception as e:
                skipped_members.append(f"**{member.display_name}** (Lỗi: {e})")
                continue
        else:
            skipped_members.append(f"**{member.display_name}** (Không ở đảo)")

        if category:
            for channel in category.text_channels:
                if str(member.id) in channel.name or (channel.topic and str(member.id) in channel.topic):
                    try: await channel.delete()
                    except: pass

    response_message = ""
    if unbanned_members:
        response_message += "Ân xá cho: " + ", ".join(unbanned_members) + "\n"
    
    if skipped_members:
        if unbanned_members: response_message += "\n"
        response_message += f"**Ân xá** cho **{len(skipped_members)}** khỉ:\n"
        response_message += f"Đã ân xá cho **{len(unbanned_members)}** khỉ!\n"
        response_message += "Danh sách: " + ", ".join(unbanned_members) + "\n"
    
    if skipped_members:
        if unbanned_members: response_message += "\n"
        response_message += f"**Bỏ qua** cho **{len(skipped_members)}** khỉ:\n"
        
    if not unbanned_members and not skipped_members:
         response_message = "Không có con khỉ nào."

    await interaction.followup.send(response_message)
bot.run(os.getenv('TOKEN'))
