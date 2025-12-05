import discord
from discord.ext import commands
import asyncio
import os
from discord import app_commands 
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

def convert_time(time):
    unit = time[-1].lower()
    if unit not in ['s', 'm', 'h', 'd']: return -1
    try: val = int(time[:-1])
    except ValueError: return -1
    if unit == 's': return val
    elif unit == 'm': return val * 60
    elif unit == 'h': return val * 3600
    elif unit == 'd': return val * 86400
    return -1

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
    member='Con khỉ cần ra đảo',
    time='Thời gian ra đảo (e.g., 10s, 5m, 1h)',
    reason='Nguyên nhân lùi hóa'
)
@commands.has_permissions(administrator=True) 
async def radao_slash(interaction: discord.Interaction, member: discord.Member, time: str, reason: str = "Thích thì cho ra thôi"):
    
    if member.id == interaction.user.id:
        await interaction.response.send_message("Sao lại tự bắn vào dé chính mình thế? Khùng hả?", ephemeral=True)
        return

    if member.id == interaction.guild.owner_id:
        await interaction.response.send_message("Mày định ban chủ server à? Lá gan to đấy!", ephemeral=True)
        return

    if member.top_role > interaction.user.top_role:
        await interaction.response.send_message(f"Đòi ban bố của bạn hả? Mơ đi.", ephemeral=True)
        return
    if member.top_role == interaction.user.top_role:
        await interaction.response.send_message(f"Đồng loại với nhau cả mà!", ephemeral=True)
        return
    # ---------------------------

    seconds = convert_time(time)
    if seconds == -1:
        await interaction.response.send_message("Sai định dạng thời gian (10s, 5m, 1h).", ephemeral=True)
        return

    guild = interaction.guild
    role_radao = guild.get_role(TARGET_ROLE_ID)
    category = guild.get_channel(TARGET_CATEGORY_ID)

    if not role_radao or not category:
        await interaction.response.send_message("Lỗi cấu hình ID.", ephemeral=True)
        return

    if role_radao in member.roles:
        await interaction.response.send_message(f"{member.mention} đang là khỉ rồi!", ephemeral=True)
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
            await member.remove_roles(*roles_to_remove_objects, reason=f"Lý do: {reason}")
        except Exception as e:
            print(f"Không thể gỡ role chỉ định: {e}")

    try:
        await member.add_roles(role_radao, reason=f"Lý do: {reason}")
        await interaction.response.send_message(f"Bonk 🔨 bà zà mày ra đảo trong **{time}** vì: **{reason}**.")
    except Exception as e:
        await interaction.response.send_message(f"Lỗi cấp role Radao: {e}", ephemeral=True)
        return

    channel_name = f"dao-khi-cua-{member.display_name}"
    created_channel = None

    try:
        created_channel = await guild.create_text_channel(
            name=channel_name,
            category=category, 
            topic=f"Kênh phạt của {member.id} - Lý do: {reason}" # Thêm lý do vào topic
        )
        
        await created_channel.set_permissions(member, read_messages=True, send_messages=True, read_message_history=True)
        
        await created_channel.send(f"Chào mừng {member.mention}! Ở đây {time} nhé.")

        try:
            await created_channel.send(f"Mày ra đảo vì **{reason}**")
            await created_channel.send("Ngồi đây bị Rick Lăn nhé :Đ!")
            await created_channel.send("https://tenor.com/view/rickroll-roll-rick-never-gonna-give-you-up-never-gonna-gif-22954713")
        except Exception as e:
            print(f"Lỗi gửi link: {e}")
            await created_channel.send(f"Lần này méo có rick roll mày may đấy")
        
    except Exception as e:
        await interaction.followup.send(f"Lỗi tạo kênh: {e}", ephemeral=True)
    await asyncio.sleep(seconds)
    member = guild.get_member(member.id) 
    if member and role_radao in member.roles:
        try:
            await member.remove_roles(role_radao, reason="Hết giờ ra đảo") 
            await restore_roles(guild, member) 
        except: pass
        
        if created_channel:
             try:
                await created_channel.delete()
                await interaction.followup.send(f"{member.name} tiến hóa thành người sau ({time}).")
             except: pass

@bot.tree.command(name="vebo", description="Dùng thuốc tiến hóa lên con khỉ đang ở đảo.")
@app_commands.describe(
    member='Con khỉ cần thuốc'
)
@commands.has_permissions(administrator=True)
async def vebo_slash(interaction: discord.Interaction, member: discord.Member):
    guild = interaction.guild
    role_radao = guild.get_role(TARGET_ROLE_ID)
    category = guild.get_channel(TARGET_CATEGORY_ID)

    if role_radao in member.roles:
        try:
            await member.remove_roles(role_radao, reason="Tiêm thuốc (Về bờ)") 
            await restore_roles(guild, member)
            await interaction.response.send_message(f"Đã ân xá cho {member.mention}!")
        except Exception as e:
            await interaction.response.send_message(f"Lỗi: {e}", ephemeral=True)
    else:
        await interaction.response.send_message(f"{member.name} không có ở đảo.", ephemeral=True)

    # Xóa kênh liên quan
    if category:
        for channel in category.text_channels:
            if str(member.id) in channel.name or (channel.topic and str(member.id) in channel.topic):
                try: await channel.delete()
                except: pass
bot.run(os.getenv('TOKEN'))

