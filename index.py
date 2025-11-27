import discord
from discord.ext import commands
import asyncio
import os

# --- CẤU HÌNH ID ---
TARGET_ROLE_ID = 1442769995783475292      # ID Role "radao"
TARGET_CATEGORY_ID = 1442769574285283399  # ID Category "đảo"
# -------------------

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Biến toàn cục để lưu các tác vụ đang đếm ngược (để có thể hủy nếu cần - nâng cao)
# Ở mức cơ bản, chúng ta sẽ dùng check role để xử lý xung đột.

def convert_time(time_str):
    unit = time_str[-1].lower()
    if unit not in ['s', 'm', 'h', 'd']:
        return -1
    try:
        val = int(time_str[:-1])
    except ValueError:
        return -1

    if unit == 's': return val
    elif unit == 'm': return val * 60
    elif unit == 'h': return val * 3600
    elif unit == 'd': return val * 86400
    return -1

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
    role = guild.get_role(TARGET_ROLE_ID)
    category = guild.get_channel(TARGET_CATEGORY_ID)

    if not role or not category:
        await ctx.send("❌ Lỗi cấu hình ID Role hoặc Category.")
        return

    # Cấp Role
    try:
        await member.add_roles(role)
        await ctx.send(f"{member.mention} đã cook ra đảo trong **{time_str}**.")
    except Exception as e:
        await ctx.send(f"❌ Lỗi cấp role: {e}")
        return

    # Tạo kênh (Tên kênh phải unique để !vebo tìm được)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, manage_channels=True)
    }

    # Đặt tên kênh có chứa ID user để dễ tìm
    channel_name = f"dao-khi-{member.id}" 
    
    try:
        created_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"Kênh phạt của {member.id}" # Lưu ID vào topic để chắc chắn
        )
        await created_channel.send(f"Chào mừng {member.mention} đến với đảo khỉ! Mày sẽ ở đây {time_str}.")
    except Exception as e:
        await ctx.send(f"⚠️ Lỗi tạo kênh: {e}")
        created_channel = None

    # Đếm ngược
    await asyncio.sleep(seconds)

    # --- HẾT GIỜ ---
    # Kiểm tra lại xem member còn role không (đề phòng đã được !vebo trước đó)
    member = guild.get_member(member.id) # Fetch lại member
    if member and role in member.roles:
        try:
            await member.remove_roles(role)
        except:
            pass
        
        # Gửi thông báo về kênh gốc nếu kênh phạt bị xóa
        if created_channel: # Nếu kênh phạt vẫn còn
             try:
                await created_channel.delete()
                await ctx.send(f"{member.name} đã về bờ sớm và tiếp xúc với nền văn minh nhân loại sau ({time_str}).")
             except:
                pass # Kênh đã bị xóa bởi !vebo

# --- LỆNH VỀ BỜ (MỚI) ---
@bot.command()
@commands.has_permissions(administrator=True)
async def vebo(ctx, member: discord.Member):
    guild = ctx.guild
    role = guild.get_role(TARGET_ROLE_ID)
    category = guild.get_channel(TARGET_CATEGORY_ID)

    if not role:
        await ctx.send("❌ Không tìm thấy Role.")
        return

    # 1. Gỡ Role ngay lập tức
    if role in member.roles:
        try:
            await member.remove_roles(role)
            await ctx.send(f"Đã ân xá cho {member.mention} về bờ sớm!")
        except Exception as e:
            await ctx.send(f"❌ Lỗi khi gỡ role: {e}")
    else:
        await ctx.send(f"{member.name} hiện không ở đảo (không có role radao).")

    # 2. Tìm và xóa kênh phạt của người đó
    # Duyệt qua tất cả kênh trong category Đảo
    if category:
        found_channel = False
        for channel in category.text_channels:
            # Kiểm tra: Tên kênh chứa ID HOẶC Topic chứa ID người dùng
            if str(member.id) in channel.name or (channel.topic and str(member.id) in channel.topic):
                try:
                    await channel.delete()
                    found_channel = True
                except:
                    await ctx.send("⚠️ Tìm thấy kênh nhưng không xóa được.")
        
        if not found_channel:
            # Không báo lỗi vì có thể admin đã xóa tay rồi
            pass

# Xử lý lỗi
@radao.error
async def radao_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Đáy xã hội mà cũng đòi ban người ta.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Dùng lệnh sai: `!radao <@tag> <thời_gian>`")

@vebo.error
async def vebo_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Bạn không có quyền ân xá.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Dùng lệnh sai: `!vebo <@tag>`")

bot.run(os.getenv('TOKEN'))
