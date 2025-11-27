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

    # 5. Tạo kênh text (Đồng bộ với Category)
    channel_name = f"dao-khi-{member.id}"
    created_channel = None

    try:
        # Bước 1: Tạo kênh thuần (Sẽ kế thừa quyền của Category)
        created_channel = await guild.create_text_channel(
            name=channel_name,
            category=category, 
            topic=f"Kênh phạt của {member.id}"
        )
        
        # Bước 2: Cấp quyền riêng cho người bị ban (Ghi đè lên quyền sync)
        await created_channel.set_permissions(member, read_messages=True, send_messages=True)
        
        await created_channel.send(f"Chào mừng {member.mention} đến với đảo khỉ! Mày sẽ ở đây {time_str}.")
        
    except Exception as e:
        await ctx.send(f"⚠️ Lỗi tạo kênh: {e}")

    # Đếm ngược
    await asyncio.sleep(seconds)

    # --- HẾT GIỜ ---
    member = guild.get_member(member.id) 
    if member and role in member.roles:
        try:
            await member.remove_roles(role)
        except:
            pass
        
        if created_channel:
             try:
                await created_channel.delete()
                await ctx.send(f"🎉 {member.name} đã về bờ ({time_str}).")
             except:
                pass

# --- LỆNH VỀ BỜ ---
@bot.command()
@commands.has_permissions(administrator=True)
async def vebo(ctx, member: discord.Member):
    guild = ctx.guild
    role = guild.get_role(TARGET_ROLE_ID)
    category = guild.get_channel(TARGET_CATEGORY_ID)

    if not role: return

    if role in member.roles:
        try:
            await member.remove_roles(role)
            await ctx.send(f"✅ Đã ân xá cho {member.mention}!")
        except Exception as e:
            await ctx.send(f"❌ Lỗi: {e}")
    else:
        await ctx.send(f"⚠️ {member.name} không có ở đảo.")

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
        await ctx.send("Bạn không có quyền ân xá.")

bot.run(os.getenv('TOKEN'))
