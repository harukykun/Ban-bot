import discord
from discord.ext import commands
import asyncio
import os

# --- CẤU HÌNH ID (Thay số của bạn vào) ---
TARGET_ROLE_ID = 1442769995783475292      # ID Role "radao"
TARGET_CATEGORY_ID = 1442769574285283399  # ID Category "đảo"
GIF_STICKER_ID = 1443617401538347108      # ID Sticker/GIF (để dự phòng)

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
    
    # --- [MỚI] KIỂM TRA QUYỀN HẠN (HIERARCHY CHECK) ---
    
    # 1. Không được ban chính mình
    if member.id == ctx.author.id:
        await ctx.send("Sao lại tự bắn vào dé chính mình thế? Khùng hả?")
        return

    # 2. Không được ban Chủ Server (Owner)
    if member.id == ctx.guild.owner_id:
        await ctx.send("Mày định ban chủ server à? Lá gan to đấy!")
        return

    # 3. Kiểm tra Role: Nếu role cao nhất của thằng bị ban >= role cao nhất của thằng gõ lệnh
    if member.top_role > ctx.author.top_role:
        await ctx.send(f"Đòi ban bố của bạn hả? Mơ đi.")
        return
    if member.top_role == ctx.author.top_role:
        await ctx.send(f"Đồng loại với nhau cả mà!")
        return
    # ----------------------------------------------------

    seconds = convert_time(time_str)
    if seconds == -1:
        await ctx.send("Sai định dạng thời gian (10s, 5m, 1h).")
        return

    guild = ctx.guild
    role_radao = guild.get_role(TARGET_ROLE_ID)
    category = guild.get_channel(TARGET_CATEGORY_ID)

    if not role_radao or not category:
        await ctx.send("❌ Lỗi cấu hình ID.")
        return

    # --- [SỬA ĐỔI TẠI ĐÂY] ---
    # 4. Kiểm tra xem người này đã bị ban chưa (đã có role radao chưa)
    if role_radao in member.roles:
        await ctx.send(f"{member.mention} đang ở đảo rồi, đừng spam lệnh nữa!")
        return
    # -------------------------

    # 5. Gỡ các role trong danh sách chỉ định
# 5. Gỡ TẤT CẢ role (trừ role @everyone và role managed)
    removed_roles_list = []
    roles_to_remove_objects = []
    
    for user_role in member.roles:
        # Điều kiện: Không phải role @everyone (default_role) VÀ Không phải role hệ thống (managed)
        if user_role != ctx.guild.default_role and not user_role.managed:
            removed_roles_list.append(user_role.id)
            roles_to_remove_objects.append(user_role)
    
    if removed_roles_list:
        temp_saved_roles[member.id] = removed_roles_list
        try:
            await member.remove_roles(*roles_to_remove_objects)
        except Exception as e:
            print(f"Không thể gỡ hết role: {e}")

    # 6. Cấp Role Radao
    try:
        await member.add_roles(role_radao)
        await ctx.send(f"Bonk 🔨 bà zà mày ra đảo trong **{time_str}** nhé.")
    except Exception as e:
        await ctx.send(f"❌ Lỗi cấp role Radao: {e}")
        return

    # 7. Tạo kênh
    channel_name = f"dao-khi-cua-{member.display_name}"
    created_channel = None

    try:
        # Bước A: Tạo kênh thuần
        created_channel = await guild.create_text_channel(
            name=channel_name,
            category=category, 
            topic=f"Kênh phạt của {member.id}"
        )
        
        # Bước B: Cấp quyền 
        await created_channel.set_permissions(member, read_messages=True, send_messages=True, read_message_history=True)
        
        await created_channel.send(f"Chào mừng {member.mention}! Ở đây {time_str} nhé.")

        # --- GỬI STICKER/LINK ---
        try:
            await created_channel.send("Ngồi đây bị Rick Lăn nhé :Đ!")
            await created_channel.send("https://tenor.com/view/rickroll-roll-rick-never-gonna-give-you-up-never-gonna-gif-22954713")
        except Exception as e:
            print(f"Lỗi gửi link: {e}")
            await created_channel.send(f"Lần này méo có rick roll mày may đấy")
        
    except Exception as e:
        await ctx.send(f"⚠️ Lỗi tạo kênh: {e}")

    # 8. Đếm ngược
    await asyncio.sleep(seconds)

    # 9. Hết giờ
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
        await ctx.send(f"{member.name} không có ở đảo.")

    if category:
        for channel in category.text_channels:
            if str(member.id) in channel.name or (channel.topic and str(member.id) in channel.topic):
                try: await channel.delete()
                except: pass

@radao.error
async def radao_error(ctx, error):
    if isinstance(error, commands.MissingPermissions): await ctx.send("Không có quyền Admin.")
    elif isinstance(error, commands.MissingRequiredArgument): await ctx.send("Sai lệnh: `!radao <@tag> <time>`")

@vebo.error
async def vebo_error(ctx, error):
    if isinstance(error, commands.MissingPermissions): await ctx.send("Không có quyền Admin.")

bot.run(os.getenv('TOKEN'))
