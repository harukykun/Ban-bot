import discord
from discord.ext import commands
import asyncio
import os
# --- CẤU HÌNH ID (Thay số của bạn vào đây) ---
# Lưu ý: ID là số nguyên, không được để trong dấu ngoặc kép ""
TARGET_ROLE_ID = 1442769995783475292     # <-- Dán ID Role "radao" vào đây
TARGET_CATEGORY_ID = 1442769574285283399 # <-- Dán ID Category "đảo" vào đây
# ---------------------------------------------

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Hàm đổi thời gian (Giữ nguyên)
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

@bot.command()
@commands.has_permissions(administrator=True)
async def radao(ctx, member: discord.Member, time_str: str):
    # 1. Xử lý thời gian
    seconds = convert_time(time_str)
    if seconds == -1:
        await ctx.send("⚠️ Định dạng thời gian sai! Ví dụ: 10s, 5m, 1h")
        return

    guild = ctx.guild

    # 2. Lấy Role theo ID
    role = guild.get_role(TARGET_ROLE_ID)
    if not role:
        await ctx.send(f"❌ Lỗi: Không tìm thấy Role có ID `{TARGET_ROLE_ID}`. Hãy kiểm tra lại code.")
        return

    # 3. Lấy Category theo ID
    category = guild.get_channel(TARGET_CATEGORY_ID)
    # Kiểm tra xem ID đó có tồn tại và đúng là Category không
    if not category or not isinstance(category, discord.CategoryChannel):
        await ctx.send(f"❌ Lỗi: Không tìm thấy Category có ID `{TARGET_CATEGORY_ID}` hoặc ID đó không phải là Category.")
        return

    # 4. Cấp Role
    try:
        await member.add_roles(role)
        await ctx.send(f"{member.mention} đã cook ra đảo trong **{time_str}**.")
    except discord.Forbidden:
        await ctx.send("❌ Bot không đủ quyền! Hãy kéo Role của Bot lên CAO HƠN role cần cấp.")
        return
    except Exception as e:
        await ctx.send(f"❌ Lỗi lạ: {e}")
        return

    # 5. Tạo kênh text
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, manage_channels=True)
    }

    channel_name = f"monkey-island" # Tên kênh không dấu, không cách
    created_channel = None

    try:
        created_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"Kênh phạt {member.name}. Thời gian: {time_str}"
        )
        await created_channel.send(f"Chào mừng{member.mention} đến với đảo khỉ nha! Mày sẽ ở đây {time_str}.")
    except Exception as e:
        await ctx.send(f"⚠️ Đã cấp role nhưng lỗi tạo kênh: {e}")

    # 6. Đếm ngược
    await asyncio.sleep(seconds)

    # 7. Hết giờ: Xóa kênh & Gỡ Role
    # Gỡ role (kiểm tra member còn trong server không)
    # Cần fetch lại member để đảm bảo dữ liệu mới nhất (tránh cache cũ)
    try:
        member = await guild.fetch_member(member.id)
        if role in member.roles:
            await member.remove_roles(role)
            print(f"Đã gỡ role cho {member.name}")
    except:
        pass # Member có thể đã thoát server

    # Xóa kênh
    if created_channel:
        try:
            await created_channel.delete()
            await ctx.send(f"{member.name} đã về bờ và tiếp xúc với nền văn minh nhân loại sau ({time_str}).")
        except:
            pass 

# Xử lý lỗi lệnh
@radao.error
async def radao_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("🚫 Bạn không phải Admin.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Dùng lệnh sai: `!radao <@tag> <thời_gian>`")


bot.run(os.getenv('TOKEN'))
