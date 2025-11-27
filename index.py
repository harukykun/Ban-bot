import discord
from discord.ext import commands
import asyncio
import os

# --- CẤU HÌNH ID ---
TARGET_ROLE_ID = 1442769995783475292      # ID Role "radao" (Role bị phạt)
TARGET_CATEGORY_ID = 1442769574285283399  # ID Category "đảo"

# Danh sách ID các role sẽ bị GỠ khi ra đảo và CẤP LẠI khi về bờ
# Ví dụ: Role VIP, Role Thành viên, v.v.
ROLES_TO_REMOVE = [
    1397191419361230970  
]

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Biến bộ nhớ tạm để lưu role cũ của user: {user_id: [role_id_1, role_id_2]}
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

# Hàm hỗ trợ: Cấp lại role cũ cho user
async def restore_roles(guild, member):
    if member.id in temp_saved_roles:
        role_ids = temp_saved_roles[member.id]
        roles_to_add = []
        
        for r_id in role_ids:
            role = guild.get_role(r_id)
            if role:
                roles_to_add.append(role)
        
        if roles_to_add:
            try:
                await member.add_roles(*roles_to_add)
                print(f"Đã trả lại {len(roles_to_add)} role cho {member.name}")
            except Exception as e:
                print(f"Lỗi trả role: {e}")
        
        # Xóa khỏi bộ nhớ sau khi trả xong
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
        await ctx.send("⚠️ Định dạng thời gian sai! Ví dụ: 10s, 5m, 1h")
        return

    guild = ctx.guild
    role_radao = guild.get_role(TARGET_ROLE_ID)
    category = guild.get_channel(TARGET_CATEGORY_ID)

    if not role_radao or not category:
        await ctx.send("❌ Lỗi cấu hình ID Role hoặc Category.")
        return

    # --- BƯỚC MỚI: Xử lý gỡ Role chỉ định ---
    removed_roles_list = []
    roles_to_remove_objects = []

    for user_role in member.roles:
        if user_role.id in ROLES_TO_REMOVE:
            removed_roles_list.append(user_role.id)
            roles_to_remove_objects.append(user_role)
    
    # Lưu vào bộ nhớ nếu có role cần gỡ
    if removed_roles_list:
        temp_saved_roles[member.id] = removed_roles_list
        try:
            await member.remove_roles(*roles_to_remove_objects)
        except Exception as e:
            await ctx.send(f"⚠️ Lỗi khi tháo role: {e}")

    # --- Tiếp tục quy trình cũ ---
    try:
        await member.add_roles(role_radao)
        await ctx.send(f"🔨 {member.mention} đã cook ra đảo trong **{time_str}**.")
    except Exception as e:
        await ctx.send(f"❌ Lỗi cấp role Radao: {e}")
        return

    # Tạo kênh (Đồng bộ Category + Cấp quyền riêng)
    channel_name = f"dao-khi-{member.id}"
    created_channel = None

    try:
        created_channel = await guild.create_text_channel(
            name=channel_name,
            category=category, 
            topic=f"Kênh phạt của {member.id}"
        )
        await created_channel.set_permissions(member, read_messages=True, send_messages=True)
        await created_channel.send(f"Chào mừng {member.mention} đến với đảo khỉ! Mày sẽ ở đây {time_str}.")
    except Exception as e:
        await ctx.send(f"⚠️ Lỗi tạo kênh: {e}")

    # Đếm ngược
    await asyncio.sleep(seconds)

    # --- HẾT GIỜ (Tự động về bờ) ---
    # Cần fetch lại member để cập nhật trạng thái mới nhất
    member = guild.get_member(member.id) 
    
    # Kiểm tra: Nếu user vẫn còn role Radao (tức là chưa được !vebo trước đó)
    if member and role_radao in member.roles:
        try:
            await member.remove_roles(role_radao)
            # Cấp lại role cũ
            await restore_roles(guild, member)
        except:
            pass
        
        if created_channel:
             try:
                await created_channel.delete()
                await ctx.send(f"{member.name} hóa thành người sau ({time_str}).")
             except:
                pass

# --- LỆNH VỀ BỜ (Ân xá sớm) ---
@bot.command()
@commands.has_permissions(administrator=True)
async def vebo(ctx, member: discord.Member):
    guild = ctx.guild
    role_radao = guild.get_role(TARGET_ROLE_ID)
    category = guild.get_channel(TARGET_CATEGORY_ID)

    if not role_radao: return

    # 1. Gỡ role Radao và Cấp lại role cũ
    if role_radao in member.roles:
        try:
            await member.remove_roles(role_radao)
            # Gọi hàm trả role
            await restore_roles(guild, member)
            await ctx.send(f"Đã ân xá sớm cho {member.mention}!")
        except Exception as e:
            await ctx.send(f"❌ Lỗi xử lý role: {e}")
    else:
        await ctx.send(f"⚠️ {member.name} không có ở đảo.")

    # 2. Xóa kênh
    if category:
        for channel in category.text_channels:
            if str(member.id) in channel.name or (channel.topic and str(member.id) in channel.topic):
                try:
                    await channel.delete()
                except:
                    pass

# Error Handlers
@radao.error
async def radao_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Đáy xã hội mà cũng đòi ban người ta.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Dùng lệnh sai: `!radao <@tag> <thời_gian>`")

@vebo.error
async def vebo_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Con khỉ này thích ân xá đồng loại không?.")

bot.run(os.getenv('TOKEN'))


