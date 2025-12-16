import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import re
import time
import asyncio

# --- CẤU HÌNH ---
SECOND_GUILD_ID = discord.Object(id=1450079520756465758) 
TARGET_ROLE_ID = 1450101924845326417
TARGET_CATEGORY_ID = 1450095959492005888

ROLES_TO_REMOVE = [
    1450080529927110658,
    1450099654258589718,
    1450080490634743888
]

# --- HÀM HỖ TRỢ ---
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

def parse_di_giao(guild: discord.Guild, di_giao: str) -> list[discord.Member]:
    members = []
    id_pattern = re.compile(r'<@!?(\d+)>')
    parts = re.split(r'[,\s]+', di_giao.strip())
    
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

# --- COG CHÍNH ---
class SecondServerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.temp_saved_roles = {}

    async def restore_roles(self, guild, member):
        """Khôi phục lại role cũ cho thành viên"""
        if member.id in self.temp_saved_roles:
            role_ids = self.temp_saved_roles[member.id]
            roles_to_add = []
            for r_id in role_ids:
                role = guild.get_role(r_id)
                if role: roles_to_add.append(role)
            if roles_to_add:
                try: await member.add_roles(*roles_to_add)
                except Exception: pass
            del self.temp_saved_roles[member.id]

    async def perform_radao(self, interaction: discord.Interaction, member: discord.Member, seconds: int, period: str, reason: str):
        """Thực hiện logic thanh tẩy (remove role, add jail role, create channel, wait, restore)"""
        guild = interaction.guild
        role_radao = guild.get_role(TARGET_ROLE_ID)
        category = guild.get_channel(TARGET_CATEGORY_ID)

        if not role_radao or not category:
            return

        # 1. Lưu và Xóa role cũ
        removed_roles_list = []
        roles_to_remove_objects = []
        
        for user_role in member.roles:
            if user_role.id in ROLES_TO_REMOVE:
                removed_roles_list.append(user_role.id)
                roles_to_remove_objects.append(user_role)
        
        if removed_roles_list:
            self.temp_saved_roles[member.id] = removed_roles_list
            try:
                await member.remove_roles(*roles_to_remove_objects, reason=f"[ThanhTay] {reason}")
            except Exception: pass

        # 2. Thêm role Radao và tạo kênh
        try:
            await member.add_roles(role_radao, reason=f"[ThanhTay] {reason}")
            channel_name = f"nha-tho-cua-{member.display_name}"
            created_channel = None
            end_time_timestamp = int(time.time() + seconds)
            discord_timestamp = f"<t:{end_time_timestamp}:R>" 
            full_date_timestamp = f"<t:{end_time_timestamp}:F>"
            
            try:
                created_channel = await guild.create_text_channel(
                    name=channel_name,
                    category=category, 
                    topic=f"ID: {member.id} | Nhà thờ của {member.display_name} - Lý do thanh tẩy: {reason}",
                    slowmode_delay=10
                )
                # Set permission
                await created_channel.set_permissions(member, read_messages=True, send_messages=True, read_message_history=True)
                
                # Gửi thông báo
                await created_channel.send(f"Chào mừng {member.mention}! Bạn sẽ được thanh tẩy sau {discord_timestamp} ({full_date_timestamp}).")
                try:
                    await created_channel.send(f"Bạn bị thanh tẩy vì **{reason}**")
                    await created_channel.send("Ngồi đây bị Rick Lăn nhé :Đ!")
                    await created_channel.send("https://tenor.com/view/rickroll-roll-rick-never-gonna-give-you-up-never-gonna-gif-22954713")
                except Exception:
                    await created_channel.send(f"Lần này méo có rick roll mày may đấy")
            except Exception: pass

            # 3. Chờ hết thời gian
            await asyncio.sleep(seconds)

            # 4. Trả tự do
            member = guild.get_member(member.id) # Lấy lại object mới nhất
            if member and role_radao in member.roles:
                try:
                    await member.remove_roles(role_radao, reason="Hết giờ thanh tẩy") 
                    await self.restore_roles(guild, member)
                except Exception: pass

            # 5. Xóa kênh
            if created_channel:
                 try: await created_channel.delete()
                 except Exception: pass
        except Exception: pass

    @app_commands.command(name="thanhtay", description="Đưa một chiên đến nhà thờ để thanh tẩy (Server Phụ).")
    @app_commands.describe(
        di_giao='Các con chiên cần thanh tẩy (dùng mention @, ID, cách nhau bởi khoảng trắng hoặc dấu phẩy)',
        period='Thời gian thanh tẩy (vd: 1h30m, 10s, 1d2h)',
        reason='Nguyên nhân dị giáo hóa'
    )
    @app_commands.guilds(SECOND_GUILD_ID)
    @commands.has_permissions(administrator=True) 
    async def thanhtay_slash(self, interaction: discord.Interaction, di_giao: str, period: str, reason: Optional[str] = None): 
        if reason is None:
            reason = "Thích thì cho đi thanh tẩy thôi!"
        
        seconds = convert_time(period)
        if seconds == -1:
            await interaction.response.send_message("Sai định dạng thời gian (vd: 1h30m, 90s, 1d).", ephemeral=True)
            return
        
        guild = interaction.guild
        members_to_process = parse_di_giao(guild, di_giao)
        
        if not members_to_process:
            await interaction.response.send_message("Không tìm thấy thành viên hợp lệ.", ephemeral=True)
            return
        
        await interaction.response.defer() 
        
        banned_members = []
        skipped_members = []
        role_radao = guild.get_role(TARGET_ROLE_ID)
        
        for member in members_to_process:
            is_skipped = False
            skip_reason = ""
            if member.id == interaction.user.id:
                skip_reason = "Người anh em sao tự bắn vào chân thế"
                is_skipped = True
            elif member.id == interaction.guild.owner_id:
                skip_reason = "Người anh em sao lại ban chủ sever tính phổng đạn à?"
                is_skipped = True
            elif member.top_role > interaction.user.top_role:
                skip_reason = "Ban bố bạn hả (Role họ to hơn)"
                is_skipped = True
            elif member.top_role == interaction.user.top_role:
                skip_reason = "Đồng nghiệp với nhau cả ban gì (Role ngang nhau)"
                is_skipped = True
            elif role_radao and role_radao in member.roles:
                skip_reason = "Đang ở nhà thờ rồi"
                is_skipped = True
            if is_skipped:
                skipped_members.append(f"**{member.display_name}** ({skip_reason})")
                continue
            asyncio.create_task(self.perform_radao(interaction, member, seconds, period, reason))
            banned_members.append(f"**{member.display_name}**")
        response_message = ""
        if banned_members:
            response_message += f"**Bonk 🔨** {len(banned_members)} dị giáo bị thanh tẩy **{period}** vì: **{reason}**.\n"
            response_message += f"Danh sách: {', '.join(banned_members)}\n"
        
        if skipped_members:
            response_message += "\n**Bỏ qua:**\n"
            response_message += "\n".join([f"- {s}" for s in skipped_members])

        if not banned_members and not skipped_members:
             response_message = "Không có thành viên hợp lệ."
             
        await interaction.followup.send(response_message)

    @app_commands.command(name="giaicuu", description="Giải cứu con chiên ở nhà thờ (Server Phụ).")
    @app_commands.describe(
        di_giao='Các con chiên cần giải cứu (dùng mention @, ID, cách nhau bởi khoảng trắng hoặc dấu phẩy)'
    )
    @app_commands.guilds(SECOND_GUILD_ID)
    @commands.has_permissions(administrator=True)
    async def giaicuu_slash(self, interaction: discord.Interaction, di_giao: str):
        guild = interaction.guild
        role_radao = guild.get_role(TARGET_ROLE_ID)
        category = guild.get_channel(TARGET_CATEGORY_ID)
        
        members_to_process = parse_di_giao(guild, di_giao)
        if not members_to_process:
            await interaction.response.send_message("Không tìm thấy thành viên hợp lệ.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        unbanned_members = []
        skipped_members = []
        
        for member in members_to_process:
            if role_radao and role_radao in member.roles:
                try:
                    await member.remove_roles(role_radao, reason="Giải nước thánh") 
                    await self.restore_roles(guild, member)
                    unbanned_members.append(f"**{member.display_name}**")
                except Exception as e:
                    skipped_members.append(f"**{member.display_name}** (Lỗi: {e})")
                    continue
            else:
                skipped_members.append(f"**{member.display_name}** (Không ở nhà thờ)")
            if category:
                for channel in category.text_channels:
                    if str(member.id) in channel.name or (channel.topic and str(member.id) in channel.topic):
                        try: await channel.delete()
                        except: pass
                        
        response_message = ""
        if unbanned_members:
            response_message += "Đã giải cứu: " + ", ".join(unbanned_members) + "\n"
        if skipped_members:
            if unbanned_members: response_message += "\n"
            response_message += f"**Bỏ qua** cho **{len(skipped_members)}** dị giáo (Lý do: Không bị giam hoặc lỗi).\n"
            
        if not unbanned_members and not skipped_members:
             response_message = "Không có ai."
             
        await interaction.followup.send(response_message)

async def setup(bot):
    await bot.add_cog(SecondServerCog(bot))
    try:
        synced = await bot.tree.sync(guild=SECOND_GUILD_ID)
        print(f"Đã đồng bộ hóa {len(synced)} lệnh cho Server Phụ.")
    except Exception as e:
        print(f"Lỗi đồng bộ lệnh Server Phụ: {e}")
