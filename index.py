import discord
from discord.ext import commands
import asyncio
import os

# --- CẤU HÌNH ID (Thay số của bạn vào) ---
TARGET_ROLE_ID = 1442769995783475292      # ID Role "radao"
TARGET_CATEGORY_ID = 1442769574285283399  # ID Category "đảo"
GIF_STICKER_ID = 1443617401538347108      # ID Sticker/GIF bạn muốn gửi

# Danh sách ID các role sẽ bị GỠ TẠM THỜI
ROLES_TO_REMOVE = [
    1434043875445702656,
    1408433140363432006,
    1397191419361230970,
    1408419247163576330,
    1397191790381236304
]
# -----------------------------------------

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

temp_saved_roles = {}

def convert_time(time_str):
    unit = time_str[-1].lower()
    if unit not in ['s', 'm', 'h', 'd']: return -1
    try: val = int(time_str[:-1])
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

# --- LỆNH RA ĐẢO ---
@bot.command()
@commands.has_permissions(administrator=True)
async def radao(ctx, member: discord.Member, time_str: str):
    seconds = convert_time(time_str)
    if seconds == -1:
        await ctx.send("⚠️ Sai định dạng thời gian (10s, 5m, 1h).")
        return

    guild = ctx.guild
    role_radao = guild.get_role(TARGET_ROLE_ID)
    category = guild.get_channel(TARGET_CATEGORY_ID)

    if not role_radao or not category:
        await ctx.send("❌ Lỗi cấu hình ID.")
        return

    # 1. Gỡ các role trong danh sách chỉ định
    removed_roles_list = []
    roles_to_remove_objects = []
    for user_role in member.roles:
        if user_role.id in ROLES_TO_REMOVE:
            removed_roles_list.append(user_role.id)
            roles_to_remove_objects.append(user_role)
    
    if removed_roles_list:
        temp_saved_roles[member.id] = removed_roles_list
        try:
            await member.remove_roles(*roles_to_remove_objects)
        except: pass

    # 2. Cấp Role Radao
    try:
        await member.add_roles(role_radao)
        await ctx.send(f"🔨 {member.mention} ra đảo trong **{time_str}**.")
    except Exception as e:
        await ctx.send(f"❌ Lỗi cấp role Radao: {e}")
        return

    # 3. Tạo kênh (ĐỒNG BỘ VỚI CATEGORY)
    # Lưu ý: Dùng display_name an toàn hơn nickname (tránh lỗi None)
    channel_name = f"dao-khi-cua-{member.display_name}"
    created_channel = None

    try:
        # Bước A: Tạo kênh thuần
        created_channel = await guild.create_text_channel(
            name=channel_name,
            category=category, 
            topic=f"Kênh phạt của {member.id}"
        )
        
        # Bước B: Cấp quyền (Cho phép chat: send_messages=True)
        # Nếu bạn để False, người bị ban chỉ nhìn thấy chứ không chat được để xin lỗi.
        await created_channel.set_permissions(member, read_messages=True, send_messages=False, read_message_history=True)
        
        await created_channel.send(f"Chào mừng {member.mention}! Ở đây {time_str} nhé.")

        # --- PHẦN MỚI: GỬI STICKER/GIF THEO ID ---
        try:
            # Bot tìm sticker theo ID
            await created_channel.send("Ngồi đây bị Rick Lăn nhé :Đ!")
            await created_channel.send("https://tenor.com/view/rickroll-roll-rick-never-gonna-give-you-up-never-gonna-gif-22954713")
        except Exception as e:
            print(f"Không gửi được Sticker: {e}")
            await created_channel.send(f"Lần này méo có rick roll mày may đấy")
            # Nếu ID đó không phải Sticker (ví dụ ID của Emoji hoặc sai ID)
        # ------------------------------------------
        
    except Exception as e:
        await ctx.send(f"⚠️ Lỗi tạo kênh: {e}")

    # 4. Đếm ngược
    await asyncio.sleep(seconds)

    # 5. Hết giờ
    member = guild.get_member(member.id) 
    if member and role_radao in member.roles:
        try:
            await member.remove_roles(role_radao)
            await restore_roles(guild, member) # Trả role cũ
        except: pass
        
        if created_channel:
             try:
                await created_channel.delete()
                await ctx.send(f"{member.name} tiến hóa thành người sau ({time_str}).")
             except: pass

# --- LỆNH VỀ BỜ ---
@bot.command()
@commands.has_permissions(administrator=True)
async def vebo(ctx, member: discord.Member):
    guild = ctx.guild
    role_radao = guild.get_role(TARGET_ROLE_ID)
    category = guild.get_channel(TARGET_CATEGORY_ID)

    if role_radao in member.roles:
        try:
            await member.remove_roles(role_radao)
            await restore_roles(guild, member)
            await ctx.send(f"Đã ân xá cho {member.mention}!")
        except Exception as e:
            await ctx.send(f"❌ Lỗi: {e}")
    else:
        await ctx.send(f"⚠️ {member.name} không có ở đảo.")

    if category:
        for channel in category.text_channels:
            if str(member.id) in channel.name or (channel.topic and str(member.id) in channel.topic):
                try: await channel.delete()
                except: pass

@radao.error
async def radao_error(ctx, error):
    if isinstance(error, commands.MissingPermissions): await ctx.send("Khỉ con mà đòi làm bố thiên hạ hả.")
    elif isinstance(error, commands.MissingRequiredArgument): await ctx.send("Sai lệnh: `!radao <@tag> <time>`")

@vebo.error
async def vebo_error(ctx, error):
    if isinstance(error, commands.MissingPermissions): await ctx.send("Khỉ con mà đòi làm bố thiên hạ hả.")

bot.run(os.getenv('TOKEN'))








