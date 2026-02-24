"""
╔══════════════════════════════════════════════════════════════╗
║  🎮 BOT CHUYỂN ĐỔI ITEMSADDER SANG BEDROCK - PHIÊN BẢN PRO  ║
║  Hỗ trợ: 3D Models | Sounds | Particles | Animations        ║
║  Phát triển bởi: Advanced Pack Converter Team               ║
╚══════════════════════════════════════════════════════════════╝
"""

import discord
from catbox_uploader import upload_multiple_to_catbox, upload_multiple_with_fallback
from discord.ext import commands
from discord import app_commands
import json, os, asyncio, zipfile, shutil, sys, psutil, time
from datetime import datetime, timedelta
from typing import Optional

# ==================== CẤU HÌNH BOT ====================
TOKEN = "MTQ3MjQwNzE2NzE0NjM5Nzg1OQ.G8Y8fF.s82EQ7uvFUSy-EsDSzmQWx_QrDiXuPm0i6IKpk"  # ⬅️ DÁN TOKEN VÀO ĐÂY

ADMIN_IDS = [1268159962564132864, 1093451783835226142]
DATABASE_FILE = "bot_database.json"
TEMP_DIR = os.path.abspath("temp_conversions")
START_TIME = time.time()

# Màu sắc chủ đạo
class Colors:
    PRIMARY = 0x5865F2      # Discord Blurple
    SUCCESS = 0x57F287      # Xanh lá
    WARNING = 0xFEE75C      # Vàng
    ERROR = 0xED4245        # Đỏ
    INFO = 0x5865F2         # Xanh dương
    PREMIUM = 0xEB459E      # Hồng VIP

# Emoji constants
EMOJI = {
    'success': '✅',
    'error': '❌',
    'warning': '⚠️',
    'loading': '⏳',
    'info': 'ℹ️',
    'premium': '⭐',
    'free': '🆓',
    'admin': '👑',
    'settings': '⚙️',
    'stats': '📊',
    'convert': '🔄',
    'file': '📦',
    'texture': '🎨',
    'sound': '🔊',
    'model': '🎮',
    'rocket': '🚀',
    'fire': '🔥',
    'gem': '💎',
    'lock': '🔒',
    'unlock': '🔓',
    'arrow': '➤',
    'dot': '•'
}

# Import converter
sys.path.append(os.path.dirname(__file__))
try:
    from ia_to_geyser_converter_v3 import IAToGeyserConverter
except ImportError:
    print("❌ Lỗi: Không tìm thấy file ia_to_geyser_converter.py!")
    sys.exit(1)

# ==================== DATABASE MANAGER ====================
class Database:
    def __init__(self, filepath):
        self.filepath = filepath
        self.data = self.load()
    
    def load(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "users": {},
            "vip_users": [],
            "approved_servers": [],
            "stats": {
                "total_conversions": 0,
                "total_items": 0,
                "total_textures": 0,
                "total_sounds": 0
            },
            "plan_limits": {"free": 5, "vip": 20}
        }
    
    def save(self):
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def is_vip(self, uid): 
        return int(uid) in self.data.get("vip_users", [])
    
    def get_user(self, uid):
        uid = str(uid)
        if uid not in self.data["users"]:
            self.data["users"][uid] = {
                "uses_today": 0,
                "last_reset": str(datetime.now().date()),
                "total": 0,
                "bonus": 0
            }
        return self.data["users"][uid]
    
    def is_server_approved(self, guild_id):
        return guild_id in self.data.get("approved_servers", [])

db = Database(DATABASE_FILE)

# ==================== EMBED BUILDER ====================
class EmbedBuilder:
    """Tạo embed đẹp và chuyên nghiệp"""
    
    @staticmethod
    def success(title: str, description: str, **kwargs) -> discord.Embed:
        embed = discord.Embed(
            title=f"{EMOJI['success']} {title}",
            description=description,
            color=Colors.SUCCESS,
            timestamp=datetime.now()
        )
        return EmbedBuilder._add_extras(embed, **kwargs)
    
    @staticmethod
    def error(title: str, description: str, **kwargs) -> discord.Embed:
        embed = discord.Embed(
            title=f"{EMOJI['error']} {title}",
            description=description,
            color=Colors.ERROR,
            timestamp=datetime.now()
        )
        return EmbedBuilder._add_extras(embed, **kwargs)
    
    @staticmethod
    def warning(title: str, description: str, **kwargs) -> discord.Embed:
        embed = discord.Embed(
            title=f"{EMOJI['warning']} {title}",
            description=description,
            color=Colors.WARNING,
            timestamp=datetime.now()
        )
        return EmbedBuilder._add_extras(embed, **kwargs)
    
    @staticmethod
    def info(title: str, description: str, **kwargs) -> discord.Embed:
        embed = discord.Embed(
            title=f"{EMOJI['info']} {title}",
            description=description,
            color=Colors.INFO,
            timestamp=datetime.now()
        )
        return EmbedBuilder._add_extras(embed, **kwargs)
    
    @staticmethod
    def premium(title: str, description: str, **kwargs) -> discord.Embed:
        embed = discord.Embed(
            title=f"{EMOJI['premium']} {title}",
            description=description,
            color=Colors.PREMIUM,
            timestamp=datetime.now()
        )
        return EmbedBuilder._add_extras(embed, **kwargs)
    
    @staticmethod
    def custom(title: str, description: str, color: int, icon: str = None, **kwargs) -> discord.Embed:
        if icon:
            title = f"{icon} {title}"
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.now()
        )
        return EmbedBuilder._add_extras(embed, **kwargs)
    
    @staticmethod
    def _add_extras(embed: discord.Embed, **kwargs) -> discord.Embed:
        """Thêm các thông tin phụ vào embed"""
        if 'fields' in kwargs:
            for field in kwargs['fields']:
                embed.add_field(
                    name=field.get('name', ''),
                    value=field.get('value', ''),
                    inline=field.get('inline', False)
                )
        
        if 'footer' in kwargs:
            embed.set_footer(text=kwargs['footer'])
        
        if 'thumbnail' in kwargs:
            embed.set_thumbnail(url=kwargs['thumbnail'])
        
        if 'image' in kwargs:
            embed.set_image(url=kwargs['image'])
        
        if 'author' in kwargs:
            embed.set_author(
                name=kwargs['author'].get('name', ''),
                icon_url=kwargs['author'].get('icon_url', None)
            )
        
        return embed

# ==================== BOT CORE ====================
class PackConverterBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!pack ",
            intents=discord.Intents.all(),
            help_command=None
        )
    
    async def setup_hook(self):
        await self.tree.sync()
        print(f"{EMOJI['success']} Đã đồng bộ lệnh Slash!")

bot = PackConverterBot()

# ==================== EVENTS ====================
@bot.event
async def on_ready():
    """Bot đã sẵn sàng"""
    print("\n" + "="*70)
    print(f"  {EMOJI['rocket']} BOT CHUYỂN ĐỔI ITEMSADDER SANG BEDROCK")
    print("="*70)
    print(f"{EMOJI['success']} Đăng nhập: {bot.user.name} ({bot.user.id})")
    print(f"{EMOJI['stats']} Servers: {len(bot.guilds)}")
    print(f"{EMOJI['stats']} Users: {len(bot.users)}")
    print(f"{EMOJI['fire']} Trạng thái: ONLINE")
    print("="*70 + "\n")
    
    # Set status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="/convert | /help"
        ),
        status=discord.Status.online
    )

@bot.event
async def on_guild_join(guild: discord.Guild):
    """Khi bot join server mới"""
    print(f"{EMOJI['info']} Joined: {guild.name} (ID: {guild.id})")
    
    # Tìm channel để gửi welcome message
    channel = guild.system_channel
    if not channel:
        for ch in guild.text_channels:
            if ch.permissions_for(guild.me).send_messages:
                channel = ch
                break
    
    if channel:
        embed = EmbedBuilder.custom(
            title="Chào mừng đến với Pack Converter Bot!",
            description=(
                f"Xin chào **{guild.name}**! {EMOJI['rocket']}\n\n"
                "Tôi là bot chuyên dụng **chuyển đổi ItemsAdder sang Bedrock Edition**\n"
                "với hỗ trợ đầy đủ 3D models, sounds, particles và animations!"
            ),
            color=Colors.PRIMARY,
            icon=EMOJI['gem']
        )
        
        embed.add_field(
            name=f"{EMOJI['lock']} Trạng thái máy chủ",
            value=(
                "⚠️ Server này **chưa được phê duyệt**\n\n"
                f"**Yêu cầu phê duyệt:**\n"
                f"{EMOJI['arrow']} Admin liên hệ bot owner\n"
                f"{EMOJI['arrow']} Hoặc dùng `/approve {guild.id}`\n\n"
                f"**Server ID:** `{guild.id}`"
            ),
            inline=False
        )
        
        embed.add_field(
            name=f"{EMOJI['info']} Lệnh cơ bản",
            value=(
                f"{EMOJI['convert']} `/convert` - Chuyển đổi pack\n"
                f"{EMOJI['stats']} `/status` - Xem trạng thái\n"
                f"{EMOJI['info']} `/help` - Hướng dẫn chi tiết\n"
                f"{EMOJI['rocket']} `/uptime` - Thông tin hệ thống"
            ),
            inline=False
        )
        
        embed.set_footer(text="Advanced Pack Converter v2.0")
        embed.set_thumbnail(url=bot.user.display_avatar.url if bot.user.avatar else None)
        
        try:
            await channel.send(embed=embed)
        except:
            pass

# ==================== HELPER FUNCTIONS ====================
def is_admin(interaction: discord.Interaction) -> bool:
    """Kiểm tra admin"""
    return interaction.user.id in ADMIN_IDS

def format_number(num: int) -> str:
    """Format số với dấu phẩy"""
    return f"{num:,}".replace(",", ".")

def get_user_tier(user_id: int) -> tuple:
    """Lấy tier và emoji của user"""
    if user_id in ADMIN_IDS:
        return "Admin", EMOJI['admin']
    elif db.is_vip(user_id):
        return "VIP", EMOJI['premium']
    else:
        return "Thường", EMOJI['free']

# ==================== USER COMMANDS ====================

@bot.tree.command(name="convert", description="🔄 Chuyển đổi pack ItemsAdder sang Bedrock Edition")
async def convert(
    interaction: discord.Interaction,
    file: Optional[discord.Attachment] = None,
    url: Optional[str] = None
):
    """Command chuyển đổi pack"""
    
    # Check server approval
    if interaction.guild and not db.is_server_approved(interaction.guild.id) and not is_admin(interaction):
        embed = EmbedBuilder.error(
            "Server chưa được phê duyệt",
            (
                f"Máy chủ **{interaction.guild.name}** chưa được phép sử dụng bot.\n\n"
                f"**Để được phê duyệt:**\n"
                f"{EMOJI['arrow']} Liên hệ admin bot\n"
                f"{EMOJI['arrow']} Cung cấp Server ID: `{interaction.guild.id}`\n\n"
                f"Admin có thể dùng `/approve {interaction.guild.id}`"
            )
        )
        embed.set_footer(text="Cần hỗ trợ? Liên hệ admin bot")
        return await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Check user limits
    user = db.get_user(interaction.user.id)
    
    # Reset daily if needed
    if user["last_reset"] != str(datetime.now().date()):
        user["uses_today"] = 0
        user["last_reset"] = str(datetime.now().date())
        db.save()
    
    # Get limits
    tier, tier_icon = get_user_tier(interaction.user.id)
    limit = db.data["plan_limits"]["vip"] if db.is_vip(interaction.user.id) else db.data["plan_limits"]["free"]
    
    # Check if can use
    if not is_admin(interaction):
        if user["bonus"] <= 0 and user["uses_today"] >= limit:
            embed = EmbedBuilder.error(
                "Đã hết lượt sử dụng",
                f"Bạn đã dùng hết **{limit}/{limit}** lượt chuyển đổi hôm nay."
            )
            
            embed.add_field(
                name=f"{EMOJI['gem']} Nâng cấp VIP",
                value=(
                    f"Upgrade lên **VIP** để nhận:\n"
                    f"{EMOJI['arrow']} **{db.data['plan_limits']['vip']} lượt/ngày**\n"
                    f"{EMOJI['arrow']} Ưu tiên xử lý\n"
                    f"{EMOJI['arrow']} Hỗ trợ 24/7"
                ),
                inline=False
            )
            
            embed.set_footer(text="Reset vào 00:00 UTC hàng ngày")
            return await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Validate input: phải có ít nhất 1 trong 2 (file hoặc url)
    if not file and not url:
        embed = EmbedBuilder.error(
            "Thiếu input",
            (
                "Vui lòng cung cấp **file ZIP** hoặc **URL link**!\n\n"
                f"**Cách dùng:**\n"
                f"{EMOJI['arrow']} Upload file: `/convert` + attach file\n"
                f"{EMOJI['arrow']} Paste link: `/convert url:<link>`\n\n"
                f"**Hỗ trợ:**\n"
                f"☁️ OneDrive\n"
                f"📦 Dropbox\n"
                f"💾 Google Drive\n"
                f"🔗 Direct download link"
            )
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Không cho phép cả 2 cùng lúc
    if file and url:
        embed = EmbedBuilder.error(
            "Input trùng lặp",
            "Vui lòng chỉ cung cấp **1 trong 2**: file upload HOẶC URL link!"
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Validate file nếu dùng upload
    if file and not file.filename.endswith('.zip'):
        embed = EmbedBuilder.error(
            "File không hợp lệ",
            f"Vui lòng upload file **ZIP**!\n\nFile của bạn: `{file.filename}`"
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Validate URL nếu dùng link
    if url:
        try:
            from file_download_helper import validate_download_url
        except ImportError:
            return await interaction.response.send_message(
                embed=EmbedBuilder.error(
                    "Thiếu module",
                    "Không tìm thấy `file_download_helper.py`!\nVui lòng đặt file này cùng thư mục với bot."
                ),
                ephemeral=True
            )
        
        valid, msg, source = validate_download_url(url)
        if not valid:
            embed = EmbedBuilder.error("URL không hợp lệ", msg)
            embed.add_field(
                name=f"{EMOJI['info']} Hỗ trợ",
                value=(
                    "☁️ OneDrive: `https://onedrive.live.com/...`\n"
                    "📦 Dropbox: `https://www.dropbox.com/...`\n"
                    "💾 Google Drive: `https://drive.google.com/file/d/...`\n"
                    "🔗 Direct link: `https://example.com/pack.zip`"
                ),
                inline=False
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Check file size (chỉ khi upload file, không check với URL)
    if file and file.size > 25 * 1024 * 1024:
        embed = EmbedBuilder.error(
            "File quá lớn",
            f"Kích thước tối đa: **25MB**\nFile của bạn: **{file.size / 1024 / 1024:.1f}MB**"
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Start processing - loading message khác nhau cho file/url
    if file:
        input_info = f"file `{file.filename}` ({file.size / 1024 / 1024:.1f} MB)"
        steps = [
            f"{EMOJI['dot']} Tải file từ Discord",
            f"{EMOJI['dot']} Phát hiện loại pack",
            f"{EMOJI['dot']} Quét resources",
            f"{EMOJI['dot']} Chuyển đổi → Bedrock",
            f"{EMOJI['dot']} Đóng gói files"
        ]
        time_est = "~10-30 giây"
    else:  # url
        input_info = f"link từ **{source.upper()}**"
        steps = [
            f"{EMOJI['dot']} Download từ {source}",
            f"{EMOJI['dot']} Phát hiện loại pack",
            f"{EMOJI['dot']} Quét resources",
            f"{EMOJI['dot']} Chuyển đổi → Bedrock",
            f"{EMOJI['dot']} Đóng gói files"
        ]
        time_est = "~30-90 giây (tùy tốc độ download)"
    
    loading_embed = EmbedBuilder.info(
        "Đang xử lý...",
        f"{EMOJI['loading']} Đang xử lý {input_info}\n\n"
        f"**Các bước:**\n" + "\n".join(steps) + f"\n\n⏱️ {time_est}"
    )
    loading_embed.set_footer(text=f"Yêu cầu bởi {interaction.user.name}")
    await interaction.response.send_message(embed=loading_embed, ephemeral=True)
    
    # Process
    work_dir = os.path.join(TEMP_DIR, f"{interaction.user.id}_{int(time.time())}")
    os.makedirs(work_dir, exist_ok=True)
    
    try:
        # Xác định input path và download nếu cần
        if file:
            # Upload từ Discord
            in_path = os.path.join(work_dir, file.filename)
            await file.save(in_path)
            download_size = file.size / (1024 * 1024)
        else:
            # Download từ URL
            from file_download_helper import download_file_from_url
            
            in_path = os.path.join(work_dir, f"pack_{int(time.time())}.zip")
            success, dl_msg, download_size = await asyncio.get_event_loop().run_in_executor(
                None, download_file_from_url, url, in_path, 300
            )
            
            if not success:
                raise Exception(f"Download thất bại: {dl_msg}")
            
            if download_size > 25:
                raise Exception(f"File quá lớn: {download_size:.1f} MB (max 25 MB)")
            
            # Update user biết download xong
            await interaction.edit_original_response(
                embed=EmbedBuilder.info(
                    "Downloaded! Converting...",
                    f"✅ Đã tải: {download_size:.2f} MB\n⏳ Đang convert..."
                )
            )
        
        # Convert
        out_path = os.path.join(work_dir, "output")
        converter = IAToGeyserConverter(in_path, out_path)
        
        await asyncio.get_event_loop().run_in_executor(None, converter.convert)
        
        # Find result files
        results = []
        mappings_file = None
        
        for root, _, files in os.walk(out_path):
            for f in files:
                full_path = os.path.join(root, f)
                
                # Add .mcpack and .zip files (not in geyser folder)
                if f.endswith((".mcpack", ".zip")) and "geyser" not in root:
                    if os.path.getsize(full_path) < 25 * 1024 * 1024:  # Under 25MB
                        results.append(discord.File(full_path, f))
                
                # Find custom_mappings.json
                elif f == "custom_mappings.json":
                    mappings_file = full_path
        
        # Add mappings file if exists
        if mappings_file and os.path.exists(mappings_file):
            results.append(discord.File(mappings_file, "custom_mappings.json"))
        
        if not results:
            raise Exception("Không tìm thấy file kết quả!")
        
        # Update database
        if not is_admin(interaction):
            if user["bonus"] > 0:
                user["bonus"] -= 1
            else:
                user["uses_today"] += 1
            user["total"] += 1
        
        # Update global stats (cả admin và user)
        db.data["stats"]["total_conversions"] = db.data["stats"].get("total_conversions", 0) + 1
        db.data["stats"]["total_items"] = db.data["stats"].get("total_items", 0) + len(converter.custom_models)
        db.data["stats"]["total_textures"] = db.data["stats"].get("total_textures", 0) + len(converter.textures)
        db.data["stats"]["total_sounds"] = db.data["stats"].get("total_sounds", 0) + len(getattr(converter, 'sounds', {}))
        db.save()
        
        # Create success embed
        if file:
            source_text = f"file **{file.filename}**"
        else:
            source_emoji = {
                'onedrive': '☁️',
                'dropbox': '📦',
                'google_drive': '💾',
                'direct': '🔗'
            }
            source_text = f"link {source_emoji.get(source, '🔗')} **{source.upper()}**"
        
        success_embed = EmbedBuilder.success(
            "Chuyển đổi thành công!",
            f"Pack từ {source_text} đã convert xong! {EMOJI['fire']}"
        )
        
        stats_text = (
            f"📦 **Size:** {download_size:.2f} MB\n"
            f"{EMOJI['model']} **Models:** {format_number(len(converter.custom_models))}\n"
            f"{EMOJI['texture']} **Textures:** {format_number(len(converter.textures))}\n"
            f"{EMOJI['sound']} **Sounds:** {format_number(len(getattr(converter, 'sounds', {})))}\n"
            f"{EMOJI['rocket']} **Animations:** {format_number(len(getattr(converter, 'animations', {})))}"
        )
        success_embed.add_field(
            name=f"{EMOJI['stats']} Thống kê",
            value=stats_text,
            inline=True
        )
        
        # Remaining uses
        if not is_admin(interaction):
            remaining = limit - user["uses_today"]
            if user["bonus"] > 0:
                remaining_text = f"{user['bonus']} lượt bonus"
            else:
                remaining_text = f"{remaining}/{limit} lượt còn lại"
            
            success_embed.add_field(
                name=f"{tier_icon} Trạng thái",
                value=(
                    f"**Tier:** {tier}\n"
                    f"**Hôm nay:** {remaining_text}\n"
                    f"**Tổng cộng:** {format_number(user['total'])} lượt"
                ),
                inline=True
            )
        
        success_embed.add_field(
            name=f"{EMOJI['file']} File đã tạo",
            value=(
                f"{EMOJI['dot']} `Bedrock_Pack.mcpack` - Cài trực tiếp vào Bedrock\n"
                f"{EMOJI['dot']} `bedrock_pack.zip` - Upload vào `Geyser/packs/`\n"
                f"{EMOJI['dot']} `custom_mappings.json` - Copy vào `Geyser/custom_mappings/`\n\n"
                f"**Hướng dẫn cài đặt:**\n"
                f"{EMOJI['arrow']} **Player Bedrock:** Mở `.mcpack` → Auto cài đặt\n"
                f"{EMOJI['arrow']} **Geyser Server:** Upload `.zip` + `.json` → `/geyser reload`"
            ),
            inline=False
        )
        
        success_embed.set_footer(
            text=f"Chuyển đổi bởi {interaction.user.name} • Advanced Pack Converter v2.0",
            icon_url=interaction.user.display_avatar.url
        )
        success_embed.set_thumbnail(url=bot.user.display_avatar.url if bot.user.avatar else None)
        
        # Send to DM - với Catbox cho file lớn
        try:
            # Tính tổng size của files
            total_size = 0
            file_paths = []
            for f in results:
                if hasattr(f.fp, 'name'):
                    fp = f.fp.name
                    file_paths.append(fp)
                    total_size += os.path.getsize(fp)
            
            # Discord limit: 25MB, nhưng an toàn là 8MB
            MAX_DISCORD_SIZE = 8 * 1024 * 1024
            
            if total_size > MAX_DISCORD_SIZE:
                # File quá lớn - upload lên Catbox
                upload_embed = EmbedBuilder.info(
                    "File quá lớn, đang upload lên Catbox...",
                    f"📦 Size: {total_size / (1024*1024):.2f} MB\n⏳ Đang upload..."
                )
                await interaction.edit_original_response(embed=upload_embed)
                
                # Upload lên Catbox
                # Upload với fallback: Catbox → Gofile
                upload_results = await asyncio.get_event_loop().run_in_executor(
                    None, upload_multiple_with_fallback, file_paths, 300
                )
                
                if upload_results['success']:
                    # Tạo embed với links
                    # Đếm service nào được dùng
                    catbox_count = sum(1 for item in upload_results['success'] if len(item) == 3 and item[2] == 'catbox')
                    gofile_count = sum(1 for item in upload_results['success'] if len(item) == 3 and item[2] == 'gofile')
                    
                    if gofile_count > 0:
                        service_text = f"Catbox ({catbox_count}) + Gofile ({gofile_count})"
                    else:
                        service_text = "Catbox"
                    
                    catbox_embed = EmbedBuilder.success(
                        "Files đã upload thành công!",
                        f"📦 Đã upload **{len(upload_results['success'])}** files lên **{service_text}**\n"
                        f"🔗 **Links vĩnh viễn, tải về miễn phí!**"
                    )
                    
                    links_text = ""
                    for item in upload_results['success']:
                        if len(item) == 3:  # (filename, url, service)
                            filename, url, service = item
                            service_emoji = '📦' if service == 'catbox' else '🗂️'
                            links_text += f"{service_emoji} **{filename}**\n└ {url}\n"
                        else:  # Backward compatibility
                            filename, url = item
                            links_text += f"**{filename}**\n└ {url}\n"
                        links_text += "\n"
                    
                    # Thêm stats (giống khi gửi trực tiếp)
                    stats_text = (
                        f"📦 **Size:** {download_size:.2f} MB\n"
                        f"{EMOJI['model']} **Models:** {format_number(len(converter.custom_models))}\n"
                        f"{EMOJI['texture']} **Textures:** {format_number(len(converter.textures))}\n"
                        f"{EMOJI['sound']} **Sounds:** {format_number(len(getattr(converter, 'sounds', {})))}\n"
                        f"{EMOJI['rocket']} **Animations:** {format_number(len(getattr(converter, 'animations', {})))}"
                    )
                    catbox_embed.add_field(
                        name=f"{EMOJI['stats']} Thống kê",
                        value=stats_text,
                        inline=True
                    )
                    
                    catbox_embed.add_field(
                        name=f"{EMOJI['file']} Download Links",
                        value=links_text[:1024],  # Discord field limit
                        inline=False
                    )
                    
                    if upload_results['failed']:
                        failed_text = "\n".join([f"❌ {fn}: {err}" for fn, err in upload_results['failed'][:3]])
                        catbox_embed.add_field(
                            name="⚠️ Lỗi upload",
                            value=failed_text,
                            inline=False
                        )
                    
                    catbox_embed.add_field(
                        name=f"{EMOJI['info']} Lưu ý",
                        value=(
                            f"{EMOJI['arrow']} Files được lưu **vĩnh viễn** trên Catbox\n"
                            f"{EMOJI['arrow']} Tải về **không giới hạn**\n"
                            f"{EMOJI['arrow']} **Lưu link** để tải lại sau"
                        ),
                        inline=False
                    )
                    
                    # Gửi DM
                    try:
                        await interaction.user.send(embed=catbox_embed)
                        await interaction.edit_original_response(
                            embed=EmbedBuilder.success(
                                "Đã gửi links vào DM!",
                                f"{EMOJI['gem']} Kiểm tra **DM** để nhận download links!"
                            )
                        )
                    except discord.Forbidden:
                        # Gửi trong channel
                        await interaction.edit_original_response(embed=catbox_embed)
                
                else:
                    # Upload failed
                    raise Exception(f"Upload Catbox thất bại: {upload_results['failed']}")
            
            else:
                # File nhỏ - gửi trực tiếp qua Discord
                await interaction.user.send(embed=success_embed, files=results)
                
                # Notify
                notify_embed = EmbedBuilder.success(
                    "File đã được gửi!",
                    f"{EMOJI['gem']} Kiểm tra **DM** của bạn để nhận file!"
                )
                notify_embed.set_footer(text="Nếu không nhận được DM, hãy bật nhận tin nhắn từ thành viên server")
                await interaction.edit_original_response(embed=notify_embed)
        
        except discord.Forbidden:
            # DM closed, send in channel
            warning_embed = EmbedBuilder.warning(
                "Không thể gửi DM",
                "DM của bạn đang đóng! File sẽ được gửi tại đây."
            )
            await interaction.edit_original_response(embed=warning_embed)
            
            # Nếu file nhỏ, gửi trực tiếp
            if total_size <= MAX_DISCORD_SIZE:
                await interaction.followup.send(embed=success_embed, files=results)
            else:
                # File lớn, đã có links trong catbox_embed
                await interaction.followup.send(embed=catbox_embed)
    
    except Exception as e:
        error_embed = EmbedBuilder.error(
            "Lỗi chuyển đổi",
            f"Đã xảy ra lỗi khi xử lý file:\n```{str(e)}```"
        )
        error_embed.add_field(
            name=f"{EMOJI['info']} Gợi ý",
            value=(
                f"{EMOJI['arrow']} Kiểm tra file ZIP có hợp lệ\n"
                f"{EMOJI['arrow']} Đảm bảo pack đúng định dạng\n"
                f"{EMOJI['arrow']} Thử lại hoặc liên hệ admin"
            ),
            inline=False
        )
        await interaction.edit_original_response(embed=error_embed)
    
    finally:
        # Cleanup
        shutil.rmtree(work_dir, ignore_errors=True)

@bot.tree.command(name="convert_models", description="🐾 Chuyển đổi riêng Model Quái (ModelEngine)")
async def convert_models(
    interaction: discord.Interaction,
    file: Optional[discord.Attachment] = None,
    url: Optional[str] = None
):
    """Lệnh riêng convert model quái - dùng mob_model_converter.py"""

    # Import tool convert model quái (file riêng biệt)
    try:
        from mob_model_converter import MobModelConverter
    except ImportError:
        return await interaction.response.send_message(
            embed=EmbedBuilder.error(
                "Thiếu file",
                "Không tìm thấy `mob_model_converter.py`!\nVui lòng đặt file này cùng thư mục với bot."
            ), ephemeral=True
        )

    # Check server approval
    if interaction.guild and not db.is_server_approved(interaction.guild.id) and not is_admin(interaction):
        return await interaction.response.send_message(
            embed=EmbedBuilder.error(
                "Server chưa được phê duyệt",
                f"Máy chủ chưa được phép sử dụng bot.\nServer ID: `{interaction.guild.id}`"
            ), ephemeral=True
        )

    # Check limit
    user = db.get_user(interaction.user.id)
    if user["last_reset"] != str(datetime.now().date()):
        user["uses_today"] = 0
        user["last_reset"] = str(datetime.now().date())
        db.save()

    limit = db.data["plan_limits"]["vip"] if db.is_vip(interaction.user.id) else db.data["plan_limits"]["free"]
    if not is_admin(interaction) and user["bonus"] <= 0 and user["uses_today"] >= limit:
        return await interaction.response.send_message(
            embed=EmbedBuilder.error("Hết lượt", f"Đã dùng hết **{limit}/{limit}** lượt hôm nay."),
            ephemeral=True
        )

    # Validate input
    if not file and not url:
        return await interaction.response.send_message(
            embed=EmbedBuilder.error(
                "Thiếu input",
                "Vui lòng cung cấp **file ZIP** hoặc **URL link**!\n\n"
                "☁️ OneDrive | 📦 Dropbox | 💾 Google Drive | 🔗 Direct link"
            ),
            ephemeral=True
        )
    
    if file and url:
        return await interaction.response.send_message(
            embed=EmbedBuilder.error("Input trùng", "Chỉ cung cấp 1 trong 2: file HOẶC url!"),
            ephemeral=True
        )
    
    if file and not file.filename.endswith(".zip"):
        return await interaction.response.send_message(
            embed=EmbedBuilder.error("File không hợp lệ", "Vui lòng upload file **ZIP**!"),
            ephemeral=True
        )
    
    # Validate URL
    if url:
        from file_download_helper import validate_download_url
        valid, msg, source = validate_download_url(url)
        if not valid:
            return await interaction.response.send_message(
                embed=EmbedBuilder.error("URL không hợp lệ", msg),
                ephemeral=True
            )

    # Loading - khác nhau cho file/url
    if file:
        input_desc = f"`{file.filename}`"
        steps_prefix = ""
    else:
        input_desc = f"link từ **{source.upper()}**"
        steps_prefix = f"{EMOJI['dot']} Download từ {source}\n"
    
    loading_embed = EmbedBuilder.custom(
        title="Đang convert model quái...",
        description=(
            f"{EMOJI['loading']} Đang xử lý {input_desc}\n\n"
            f"**Các bước:**\n"
            f"{steps_prefix}"
            f"{EMOJI['dot']} Giải nén pack\n"
            f"{EMOJI['dot']} Quét ModelEngine mobs\n"
            f"{EMOJI['dot']} Convert geometry → Bedrock\n"
            f"{EMOJI['dot']} Tạo entity + render controller\n"
            f"{EMOJI['dot']} Đóng gói .mcpack\n\n"
            f"⏱️ Dự kiến: ~15-90 giây"
        ),
        color=Colors.INFO,
        icon=EMOJI['model']
    )
    loading_embed.set_footer(text=f"Yêu cầu bởi {interaction.user.name}")
    await interaction.response.send_message(embed=loading_embed, ephemeral=True)

    work_dir = os.path.join(TEMP_DIR, f"mob_{interaction.user.id}_{int(time.time())}")
    os.makedirs(work_dir, exist_ok=True)

    try:
        # Download file hoặc url
        if file:
            in_path = os.path.join(work_dir, file.filename)
            await file.save(in_path)
            download_size = file.size / (1024 * 1024)
        else:
            from file_download_helper import download_file_from_url
            in_path = os.path.join(work_dir, f"pack_{int(time.time())}.zip")
            success, dl_msg, download_size = await asyncio.get_event_loop().run_in_executor(
                None, download_file_from_url, url, in_path, 300
            )
            if not success:
                raise Exception(f"Download lỗi: {dl_msg}")
            if download_size > 25:
                raise Exception(f"File quá lớn: {download_size:.1f} MB")
            
            await interaction.edit_original_response(
                embed=EmbedBuilder.info("Downloaded!", f"✅ {download_size:.2f} MB | ⏳ Converting...")
            )
        
        # Convert
        out_path = os.path.join(work_dir, "output")
        converter = MobModelConverter(in_path, out_path)
        result = await asyncio.get_event_loop().run_in_executor(None, converter.convert)

        # Không tìm thấy mob nào
        if result["converted"] == 0 and result["skipped"] == 0:
            await interaction.edit_original_response(
                embed=EmbedBuilder.warning(
                    "Không tìm thấy model quái",
                    (
                        f"Pack `{file.filename}` không có ModelEngine mob nào.\n\n"
                        f"**Lệnh này hỗ trợ pack có:**\n"
                        f"{EMOJI['arrow']} `assets/modelengine/models/<mob>/<part>.json`\n"
                        f"{EMOJI['arrow']} `assets/elitecreatures/models/<mob>/<part>.json`\n\n"
                        f"Dùng `/convert` để convert pack thông thường."
                    )
                )
            )
            return

        # Tìm files output
        results = []
        for root, _, files_list in os.walk(out_path):
            for fname in files_list:
                full = os.path.join(root, fname)
                size = os.path.getsize(full)
                if fname.endswith((".mcpack", ".zip")) and "_temp" not in root:
                    if size < 25 * 1024 * 1024:
                        results.append(discord.File(full, fname))
                # Bỏ qua MOB_REPORT.md - không gửi cho user
                elif fname == "MOB_REPORT.md":
                    pass  # Skip report file

        if not results:
            raise Exception("Không tạo được file output!")

        # Update usage
        if not is_admin(interaction):
            if user["bonus"] > 0:
                user["bonus"] -= 1
            else:
                user["uses_today"] += 1
            user["total"] += 1
        
        # Update global stats (cả admin và user)
        db.data["stats"]["total_conversions"] = db.data["stats"].get("total_conversions", 0) + 1
        db.save()

        # Success embed
        if file:
            source_text = f"file `{file.filename}`"
        else:
            source_text = f"link từ **{source.upper()}**"
        
        success_embed = EmbedBuilder.success(
            "Model Quái đã được chuyển đổi!",
            f"Đã convert model quái từ {source_text} {EMOJI['fire']}"
        )
        success_embed.add_field(
            name=f"{EMOJI['model']} Kết quả",
            value=(
                f"✅ **Thành công:** {result['converted']} mobs\n"
                f"⚠️ **Bỏ qua:** {result['skipped']} mobs\n"
                f"❌ **Lỗi:** {len(result['errors'])} mobs"
            ),
            inline=True
        )
        success_embed.add_field(
            name=f"{EMOJI['file']} Files",
            value=(
                f"{EMOJI['dot']} `MobModels_Bedrock.mcpack`\n"
                f"  └ Cài trực tiếp vào Bedrock\n"
                f"{EMOJI['dot']} `mob_models_geyser.zip`\n"
                f"  └ Upload vào `Geyser/packs/`"
            ),
            inline=True
        )

        # Hiện lỗi nếu có
        if result["errors"]:
            errs = result["errors"][:5]
            err_lines = [f"`{m}`: {e}" for m, e in errs]
            if len(result["errors"]) > 5:
                err_lines.append(f"... và {len(result['errors'])-5} lỗi khác")
            success_embed.add_field(
                name=f"{EMOJI['warning']} Chi tiết lỗi",
                value="\n".join(err_lines),
                inline=False
            )

        success_embed.set_footer(
            text=f"Mob Model Converter • {interaction.user.name}",
            icon_url=interaction.user.display_avatar.url
        )

        # Gửi DM - với Catbox cho file lớn
        try:
            # Tính size
            total_size = 0
            file_paths = []
            for f in results:
                if hasattr(f.fp, 'name'):
                    fp = f.fp.name
                    file_paths.append(fp)
                    total_size += os.path.getsize(fp)
            
            MAX_DISCORD_SIZE = 8 * 1024 * 1024
            
            if total_size > MAX_DISCORD_SIZE:
                # Upload lên Catbox
                upload_embed = EmbedBuilder.info(
                    "File quá lớn, đang upload lên Catbox...",
                    f"📦 Size: {total_size / (1024*1024):.2f} MB\n⏳ Uploading..."
                )
                await interaction.edit_original_response(embed=upload_embed)
                
                # Upload với fallback: Catbox → Gofile
                upload_results = await asyncio.get_event_loop().run_in_executor(
                    None, upload_multiple_with_fallback, file_paths, 300
                )
                
                if upload_results['success']:
                    catbox_embed = EmbedBuilder.success(
                        "Files đã upload lên Catbox!",
                        f"📦 Đã upload **{len(upload_results['success'])}** files model quái"
                    )
                    
                    # Stats
                    catbox_embed.add_field(
                        name=f"{EMOJI['model']} Kết quả",
                        value=(
                            f"✅ **Thành công:** {result['converted']} mobs\n"
                            f"⚠️  **Bỏ qua:** {result['skipped']} mobs\n"
                            f"❌ **Lỗi:** {len(result['errors'])} mobs"
                        ),
                        inline=True
                    )
                    
                    # Links
                    links = ""
                    for item in upload_results['success']:
                        if len(item) == 3:
                            fn, url, service = item
                            service_emoji = '📦' if service == 'catbox' else '🗂️'
                            links += f"{service_emoji} **{fn}**\n└ {url}\n\n"
                        else:
                            fn, url = item
                            links += f"**{fn}**\n└ {url}\n\n"
                    
                    catbox_embed.add_field(
                        name=f"{EMOJI['file']} Download Links",
                        value=links[:1024],
                        inline=False
                    )
                    
                    catbox_embed.add_field(
                        name=f"{EMOJI['info']} Lưu ý",
                        value=(
                            f"{EMOJI['arrow']} Files được lưu **vĩnh viễn**\n"
                            f"{EMOJI['arrow']} Tải về **không giới hạn**\n"
                            f"{EMOJI['arrow']} **Lưu link** để tải lại sau"
                        ),
                        inline=False
                    )
                    
                    try:
                        await interaction.user.send(embed=catbox_embed)
                        await interaction.edit_original_response(
                            embed=EmbedBuilder.success("Đã gửi links vào DM!", "Check DM!")
                        )
                    except discord.Forbidden:
                        await interaction.edit_original_response(embed=catbox_embed)
                else:
                    raise Exception(f"Catbox upload failed")
            else:
                # File nhỏ - gửi trực tiếp
                await interaction.user.send(embed=success_embed, files=results)
                await interaction.edit_original_response(
                    embed=EmbedBuilder.success(
                        "Đã gửi vào DM!",
                        f"{EMOJI['gem']} Kiểm tra **DM** để nhận files model quái!"
                    )
                )
        except discord.Forbidden:
            if total_size <= MAX_DISCORD_SIZE:
                await interaction.edit_original_response(embed=success_embed)
                await interaction.followup.send(files=results)
            else:
                await interaction.edit_original_response(embed=catbox_embed)

    except Exception as e:
        error_embed = EmbedBuilder.error(
            "Lỗi convert model quái",
            f"```{str(e)[:800]}```"
        )
        error_embed.add_field(
            name=f"{EMOJI['info']} Debug",
            value=(
                f"{EMOJI['arrow']} File `mob_model_converter.py` có đúng chỗ chưa?\n"
                f"{EMOJI['arrow']} Pack có chứa folder `models/<mob>/<part>.json`?\n"
                f"{EMOJI['arrow']} Xem log bot để biết thêm chi tiết"
            ),
            inline=False
        )
        await interaction.edit_original_response(embed=error_embed)

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)



@bot.tree.command(name="status", description="📊 Xem trạng thái và lượt sử dụng của bạn")
async def status(interaction: discord.Interaction):
    """Xem status cá nhân"""
    
    user = db.get_user(interaction.user.id)
    tier, tier_icon = get_user_tier(interaction.user.id)
    is_vip = db.is_vip(interaction.user.id)
    
    # Check reset
    if user["last_reset"] != str(datetime.now().date()):
        user["uses_today"] = 0
        user["last_reset"] = str(datetime.now().date())
        db.save()
    
    # Get limits
    if interaction.user.id in ADMIN_IDS:
        limit_text = "Không giới hạn"
        uses_text = "∞"
        color = Colors.PRIMARY
    else:
        limit = db.data["plan_limits"]["vip"] if is_vip else db.data["plan_limits"]["free"]
        limit_text = f"{limit} lượt/ngày"
        uses_text = f"{user['uses_today']}/{limit}"
        color = Colors.PREMIUM if is_vip else Colors.INFO
    
    embed = discord.Embed(
        title=f"{tier_icon} Thông tin tài khoản",
        description=f"Thông tin chi tiết của **{interaction.user.name}**",
        color=color,
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name=f"{EMOJI['gem']} Hạng thành viên",
        value=f"**{tier}**",
        inline=True
    )
    
    embed.add_field(
        name=f"{EMOJI['fire']} Giới hạn",
        value=limit_text,
        inline=True
    )
    
    embed.add_field(
        name=f"{EMOJI['stats']} Đã dùng hôm nay",
        value=uses_text,
        inline=True
    )
    
    if user.get("bonus", 0) > 0:
        embed.add_field(
            name=f"{EMOJI['gem']} Lượt thưởng",
            value=f"**{user['bonus']}** lượt",
            inline=True
        )
    
    embed.add_field(
        name=f"{EMOJI['rocket']} Tổng chuyển đổi",
        value=f"**{format_number(user.get('total', 0))}** lần",
        inline=True
    )
    
    # Progress bar
    if interaction.user.id not in ADMIN_IDS:
        limit = db.data["plan_limits"]["vip"] if is_vip else db.data["plan_limits"]["free"]
        used = user["uses_today"]
        percent = min(int((used / limit) * 10), 10)
        bar = "█" * percent + "░" * (10 - percent)
        
        embed.add_field(
            name=f"{EMOJI['stats']} Tiến trình sử dụng",
            value=f"`{bar}` {used}/{limit}",
            inline=False
        )
    
    # VIP benefits
    if not is_vip and interaction.user.id not in ADMIN_IDS:
        embed.add_field(
            name=f"{EMOJI['premium']} Nâng cấp VIP",
            value=(
                f"{EMOJI['arrow']} **20 lượt/ngày** (thay vì 5)\n"
                f"{EMOJI['arrow']} Ưu tiên xử lý nhanh hơn\n"
                f"{EMOJI['arrow']} Hỗ trợ ưu tiên 24/7\n"
                f"{EMOJI['arrow']} Badge đặc biệt\n\n"
                f"Liên hệ admin để nâng cấp!"
            ),
            inline=False
        )
    
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.set_footer(text=f"Reset hàng ngày lúc 00:00 UTC • User ID: {interaction.user.id}")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="uptime", description="👑 [ADMIN] Xem thông tin hệ thống chi tiết")
async def uptime(interaction: discord.Interaction):
    """System information - ADMIN ONLY"""
    
    # Check admin
    if not is_admin(interaction):
        return await interaction.response.send_message(
            embed=EmbedBuilder.error("Truy cập bị từ chối", "Chỉ admin mới dùng được lệnh này!"),
            ephemeral=True
        )
    
    uptime_seconds = int(time.time() - START_TIME)
    uptime_str = str(timedelta(seconds=uptime_seconds))
    
    # Lấy thông tin hệ thống chi tiết
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    cpu_freq = psutil.cpu_freq()
    
    mem = psutil.virtual_memory()
    mem_total_gb = mem.total / (1024**3)
    mem_used_gb = mem.used / (1024**3)
    mem_available_gb = mem.available / (1024**3)
    
    disk = psutil.disk_usage('/')
    disk_total_gb = disk.total / (1024**3)
    disk_used_gb = disk.used / (1024**3)
    disk_free_gb = disk.free / (1024**3)
    
    # Create progress bars
    def create_bar(percent):
        filled = int(percent / 10)
        return "█" * filled + "░" * (10 - filled)
    
    embed = discord.Embed(
        title=f"{EMOJI['admin']} Thông tin hệ thống (Admin)",
        description="Trạng thái và hiệu suất chi tiết của bot",
        color=Colors.PRIMARY,
        timestamp=datetime.now()
    )
    
    # Uptime
    embed.add_field(
        name=f"{EMOJI['fire']} Thời gian hoạt động",
        value=f"```{uptime_str}```",
        inline=False
    )
    
    # CPU
    cpu_freq_str = f"{cpu_freq.current:.0f} MHz" if cpu_freq else "N/A"
    embed.add_field(
        name=f"{EMOJI['settings']} CPU",
        value=(
            f"`{create_bar(cpu_percent)}` **{cpu_percent}%**\n"
            f"**Cores:** {cpu_count} cores\n"
            f"**Frequency:** {cpu_freq_str}"
        ),
        inline=False
    )
    
    # RAM
    embed.add_field(
        name=f"{EMOJI['settings']} RAM",
        value=(
            f"`{create_bar(mem.percent)}` **{mem.percent}%**\n"
            f"**Sử dụng:** {mem_used_gb:.2f} GB / {mem_total_gb:.2f} GB\n"
            f"**Còn trống:** {mem_available_gb:.2f} GB"
        ),
        inline=False
    )
    
    # Disk
    embed.add_field(
        name=f"{EMOJI['settings']} Disk",
        value=(
            f"`{create_bar(disk.percent)}` **{disk.percent}%**\n"
            f"**Sử dụng:** {disk_used_gb:.2f} GB / {disk_total_gb:.2f} GB\n"
            f"**Còn trống:** {disk_free_gb:.2f} GB"
        ),
        inline=False
    )
    
    # Bot stats
    embed.add_field(
        name=f"{EMOJI['stats']} Servers & Users",
        value=(
            f"**Servers:** {len(bot.guilds)}\n"
            f"**Users:** {format_number(len(bot.users))}\n"
            f"**Approved Servers:** {len(db.data.get('approved_servers', []))}"
        ),
        inline=True
    )
    
    stats = db.data["stats"]
    embed.add_field(
        name=f"{EMOJI['convert']} Conversions",
        value=(
            f"**Total:** {format_number(stats.get('total_conversions', 0))}\n"
            f"**Items:** {format_number(stats.get('total_items', 0))}\n"
            f"**Textures:** {format_number(stats.get('total_textures', 0))}\n"
            f"**Sounds:** {format_number(stats.get('total_sounds', 0))}"
        ),
        inline=True
    )
    
    embed.set_thumbnail(url=bot.user.display_avatar.url if bot.user.avatar else None)
    embed.set_footer(text="Advanced Pack Converter v2.0 • Admin View")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="help", description="ℹ️ Xem hướng dẫn sử dụng bot")
async def help_command(interaction: discord.Interaction):
    """Help command"""
    
    is_admin_user = is_admin(interaction)
    
    embed = discord.Embed(
        title=f"{EMOJI['info']} Hướng dẫn sử dụng Bot",
        description=(
            "**Bot chuyển đổi ItemsAdder sang Bedrock Edition**\n"
            "Hỗ trợ đầy đủ 3D models, sounds, particles và animations!"
        ),
        color=Colors.PRIMARY,
        timestamp=datetime.now()
    )
    
    # User commands
    embed.add_field(
        name=f"{EMOJI['convert']} Lệnh người dùng",
        value=(
            f"`/convert` - Convert pack (file hoặc link)\n"
            f"`/convert_models` - Chỉ convert model quái\n"
            f"`/status` - Xem thông tin tài khoản\n"
            f"`/help` - Xem hướng dẫn này"
        ),
        inline=False
    )
    
    # How to use
    embed.add_field(
        name=f"{EMOJI['info']} Cách sử dụng",
        value=(
            f"{EMOJI['arrow']} **Bước 1:** Chạy `/ia zip` trong server Minecraft\n"
            f"{EMOJI['arrow']} **Bước 2a:** Upload file: `/convert` + attach file ZIP\n"
            f"            **HOẶC**\n"
            f"{EMOJI['arrow']} **Bước 2b:** Paste link: `/convert url:<link>`\n"
            f"{EMOJI['arrow']} **Bước 3:** Nhận file trong DM\n"
            f"{EMOJI['arrow']} **Bước 4:** Cài đặt vào Bedrock/Geyser\n\n"
            f"☁️ **Hỗ trợ:** OneDrive, Dropbox, Google Drive, Direct link"
        ),
        inline=False
    )
    
    # Plans
    free_limit = db.data["plan_limits"]["free"]
    vip_limit = db.data["plan_limits"]["vip"]
    
    embed.add_field(
        name=f"{EMOJI['free']} Gói Miễn phí",
        value=f"{EMOJI['arrow']} **{free_limit} lượt/ngày**\n{EMOJI['arrow']} Hỗ trợ cơ bản",
        inline=True
    )
    
    embed.add_field(
        name=f"{EMOJI['premium']} Gói VIP",
        value=f"{EMOJI['arrow']} **{vip_limit} lượt/ngày**\n{EMOJI['arrow']} Ưu tiên xử lý\n{EMOJI['arrow']} Hỗ trợ 24/7",
        inline=True
    )
    
    if is_admin_user:
        embed.add_field(
            name=f"{EMOJI['admin']} Lệnh Admin",
            value=(
                "`/approve` - Duyệt server\n"
                "`/unapprove` - Gỡ duyệt\n"
                "`/addvip` - Thêm VIP\n"
                "`/removevip` - Xóa VIP\n"
                "`/adduses` - Tặng lượt\n"
                "`/setlimit` - Đặt giới hạn\n"
                "`/stats` - Thống kê bot\n"
                "`/check_user` - Kiểm tra user\n"
                "`/reset_user` - Reset user\n"
                "`/listservers` - Danh sách server\n"
                "`/broadcast` - Thông báo toàn server"
            ),
            inline=False
        )
    
    # Features
    embed.add_field(
        name=f"{EMOJI['fire']} Tính năng nổi bật",
        value=(
            f"{EMOJI['model']} Chuyển đổi 3D models\n"
            f"{EMOJI['texture']} Xử lý textures\n"
            f"{EMOJI['sound']} Hỗ trợ sounds\n"
            f"{EMOJI['rocket']} Particles & animations\n"
            f"{EMOJI['gem']} Tạo Geyser mappings"
        ),
        inline=False
    )
    
    embed.set_thumbnail(url=bot.user.display_avatar.url if bot.user.avatar else None)
    embed.set_footer(text="Advanced Pack Converter v2.0 • Cần hỗ trợ? Liên hệ admin")
    
    await interaction.response.send_message(embed=embed)

# ==================== ADMIN COMMANDS ====================

@bot.tree.command(name="stats", description="👑 [ADMIN] Xem thống kê tổng quan bot")
async def stats_admin(interaction: discord.Interaction):
    """Admin stats"""
    if not is_admin(interaction):
        return await interaction.response.send_message(
            embed=EmbedBuilder.error("Truy cập bị từ chối", "Chỉ admin mới dùng được lệnh này!"),
            ephemeral=True
        )
    
    stats = db.data["stats"]
    total_users = len(db.data["users"])
    vip_count = len(db.data["vip_users"])
    free_count = total_users - vip_count
    approved_servers = len(db.data["approved_servers"])
    
    embed = EmbedBuilder.custom(
        title="Thống kê Bot",
        description="Tổng quan hoạt động của bot",
        color=Colors.PRIMARY,
        icon=EMOJI['stats']
    )
    
    embed.add_field(
        name=f"{EMOJI['stats']} Người dùng",
        value=(
            f"**Tổng:** {format_number(total_users)}\n"
            f"{EMOJI['premium']} **VIP:** {format_number(vip_count)}\n"
            f"{EMOJI['free']} **Free:** {format_number(free_count)}"
        ),
        inline=True
    )
    
    embed.add_field(
        name=f"{EMOJI['convert']} Chuyển đổi",
        value=(
            f"**Tổng:** {format_number(stats.get('total_conversions', 0))}\n"
            f"{EMOJI['model']} **Items:** {format_number(stats.get('total_items', 0))}\n"
            f"{EMOJI['texture']} **Textures:** {format_number(stats.get('total_textures', 0))}\n"
            f"{EMOJI['sound']} **Sounds:** {format_number(stats.get('total_sounds', 0))}"
        ),
        inline=True
    )
    
    embed.add_field(
        name=f"{EMOJI['rocket']} Hệ thống",
        value=(
            f"**Servers:** {len(bot.guilds)}\n"
            f"{EMOJI['unlock']} **Approved:** {approved_servers}\n"
            f"**Users:** {format_number(len(bot.users))}"
        ),
        inline=True
    )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="approve", description="👑 [ADMIN] Phê duyệt server sử dụng bot")
async def approve(interaction: discord.Interaction, server_id: Optional[str] = None):
    """Approve server"""
    if not is_admin(interaction):
        return await interaction.response.send_message(
            embed=EmbedBuilder.error("Truy cập bị từ chối", "Chỉ admin mới dùng được lệnh này!"),
            ephemeral=True
        )
    
    sid = int(server_id) if server_id else interaction.guild.id
    
    if sid in db.data["approved_servers"]:
        embed = EmbedBuilder.warning(
            "Server đã được duyệt",
            f"Server `{sid}` đã nằm trong danh sách phê duyệt."
        )
    else:
        db.data["approved_servers"].append(sid)
        db.save()
        
        guild = bot.get_guild(sid)
        guild_name = guild.name if guild else f"Unknown ({sid})"
        
        embed = EmbedBuilder.success(
            "Phê duyệt thành công!",
            f"Server **{guild_name}** đã được phép sử dụng bot."
        )
        embed.add_field(name="Server ID", value=f"`{sid}`")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="unapprove", description="👑 [ADMIN] Gỡ phê duyệt server")
async def unapprove(interaction: discord.Interaction, server_id: str):
    """Unapprove server"""
    if not is_admin(interaction):
        return await interaction.response.send_message(
            embed=EmbedBuilder.error("Truy cập bị từ chối", "Chỉ admin mới dùng được lệnh này!"),
            ephemeral=True
        )
    
    sid = int(server_id)
    
    if sid not in db.data["approved_servers"]:
        embed = EmbedBuilder.warning(
            "Server chưa được duyệt",
            f"Server `{sid}` không nằm trong danh sách."
        )
    else:
        db.data["approved_servers"].remove(sid)
        db.save()
        
        guild = bot.get_guild(sid)
        guild_name = guild.name if guild else f"Unknown ({sid})"
        
        embed = EmbedBuilder.success(
            "Đã gỡ phê duyệt",
            f"Server **{guild_name}** không còn quyền sử dụng bot."
        )
        embed.add_field(name="Server ID", value=f"`{sid}`")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="listservers", description="👑 [ADMIN] Danh sách tất cả servers bot đang ở")
async def listservers(interaction: discord.Interaction):
    """List all servers - approved and not approved"""
    if not is_admin(interaction):
        return await interaction.response.send_message(
            embed=EmbedBuilder.error("Truy cập bị từ chối", "Chỉ admin mới dùng được lệnh này!"),
            ephemeral=True
        )
    
    approved_ids = set(db.data.get("approved_servers", []))
    all_guilds = sorted(bot.guilds, key=lambda g: g.name.lower())
    
    approved_list = []
    not_approved_list = []
    
    for guild in all_guilds:
        guild_info = f"{EMOJI['dot']} **{guild.name}**\n   ID: `{guild.id}` | Members: {guild.member_count}"
        
        if guild.id in approved_ids:
            approved_list.append(f"{EMOJI['unlock']} {guild_info}")
        else:
            not_approved_list.append(f"{EMOJI['lock']} {guild_info}")
    
    # Tạo embed
    embed = EmbedBuilder.custom(
        title="Danh sách tất cả Servers",
        description=(
            f"**Tổng:** {len(all_guilds)} servers\n"
            f"{EMOJI['unlock']} **Đã duyệt:** {len(approved_list)}\n"
            f"{EMOJI['lock']} **Chưa duyệt:** {len(not_approved_list)}"
        ),
        color=Colors.PRIMARY,
        icon=EMOJI['stats']
    )
    
    # Hiển thị approved servers (tối đa 10)
    if approved_list:
        approved_text = "\n".join(approved_list[:10])
        if len(approved_list) > 10:
            approved_text += f"\n\n... và {len(approved_list)-10} servers khác"
        embed.add_field(
            name=f"{EMOJI['unlock']} Servers đã duyệt ({len(approved_list)})",
            value=approved_text,
            inline=False
        )
    
    # Hiển thị not approved servers (tối đa 10)
    if not_approved_list:
        not_approved_text = "\n".join(not_approved_list[:10])
        if len(not_approved_list) > 10:
            not_approved_text += f"\n\n... và {len(not_approved_list)-10} servers khác"
        embed.add_field(
            name=f"{EMOJI['lock']} Servers chưa duyệt ({len(not_approved_list)})",
            value=not_approved_text,
            inline=False
        )
    
    # Nếu không có server nào
    if not all_guilds:
        embed.description = "Bot chưa ở trong server nào!"
    
    embed.set_footer(text=f"Tổng: {len(all_guilds)} servers • Dùng /approve <id> để phê duyệt")
    embed.set_thumbnail(url=bot.user.display_avatar.url if bot.user.avatar else None)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="addvip", description="👑 [ADMIN] Thêm VIP cho user")
async def addvip(interaction: discord.Interaction, user: discord.User):
    """Add VIP"""
    if not is_admin(interaction):
        return await interaction.response.send_message(
            embed=EmbedBuilder.error("Truy cập bị từ chối", "Chỉ admin mới dùng được lệnh này!"),
            ephemeral=True
        )
    
    if user.id in db.data["vip_users"]:
        embed = EmbedBuilder.warning(
            "User đã là VIP",
            f"{user.mention} đã có quyền VIP rồi."
        )
    else:
        db.data["vip_users"].append(user.id)
        db.save()
        
        embed = EmbedBuilder.premium(
            "Đã thêm VIP!",
            f"{user.mention} giờ đã là thành viên **VIP**!"
        )
        embed.add_field(
            name="Quyền lợi VIP",
            value=f"{EMOJI['arrow']} {db.data['plan_limits']['vip']} lượt/ngày\n{EMOJI['arrow']} Ưu tiên xử lý"
        )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="removevip", description="👑 [ADMIN] Xóa VIP của user")
async def removevip(interaction: discord.Interaction, user: discord.User):
    """Remove VIP"""
    if not is_admin(interaction):
        return await interaction.response.send_message(
            embed=EmbedBuilder.error("Truy cập bị từ chối", "Chỉ admin mới dùng được lệnh này!"),
            ephemeral=True
        )
    
    if user.id not in db.data["vip_users"]:
        embed = EmbedBuilder.warning(
            "User không phải VIP",
            f"{user.mention} không có quyền VIP."
        )
    else:
        db.data["vip_users"].remove(user.id)
        db.save()
        
        embed = EmbedBuilder.info(
            "Đã xóa VIP",
            f"{user.mention} về lại gói Free."
        )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="adduses", description="👑 [ADMIN] Tặng lượt thưởng cho user")
async def adduses(interaction: discord.Interaction, user: discord.User, amount: int):
    """Add bonus uses"""
    if not is_admin(interaction):
        return await interaction.response.send_message(
            embed=EmbedBuilder.error("Truy cập bị từ chối", "Chỉ admin mới dùng được lệnh này!"),
            ephemeral=True
        )
    
    if amount <= 0:
        return await interaction.response.send_message(
            embed=EmbedBuilder.error("Số lượng không hợp lệ", "Vui lòng nhập số dương!"),
            ephemeral=True
        )
    
    u = db.get_user(user.id)
    u["bonus"] += amount
    db.save()
    
    embed = EmbedBuilder.success(
        "Đã tặng lượt thưởng!",
        f"{user.mention} nhận được **{amount}** lượt chuyển đổi!"
    )
    embed.add_field(
        name="Tổng lượt thưởng",
        value=f"**{u['bonus']}** lượt"
    )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="setlimit", description="👑 [ADMIN] Đặt giới hạn cho gói")
async def setlimit(interaction: discord.Interaction, plan: str, limit: int):
    """Set plan limit"""
    if not is_admin(interaction):
        return await interaction.response.send_message(
            embed=EmbedBuilder.error("Truy cập bị từ chối", "Chỉ admin mới dùng được lệnh này!"),
            ephemeral=True
        )
    
    if plan.lower() not in ["free", "vip"]:
        return await interaction.response.send_message(
            embed=EmbedBuilder.error("Gói không hợp lệ", "Chỉ có `free` hoặc `vip`!"),
            ephemeral=True
        )
    
    if limit < 0:
        return await interaction.response.send_message(
            embed=EmbedBuilder.error("Số không hợp lệ", "Giới hạn phải >= 0!"),
            ephemeral=True
        )
    
    old_limit = db.data["plan_limits"][plan.lower()]
    db.data["plan_limits"][plan.lower()] = limit
    db.save()
    
    embed = EmbedBuilder.success(
        "Đã cập nhật giới hạn!",
        f"Gói **{plan.upper()}** giờ có giới hạn mới."
    )
    embed.add_field(name="Giới hạn cũ", value=f"{old_limit} lượt/ngày", inline=True)
    embed.add_field(name="Giới hạn mới", value=f"{limit} lượt/ngày", inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="check_user", description="👑 [ADMIN] Kiểm tra thông tin user")
async def check_user(interaction: discord.Interaction, user: discord.User):
    """Check user info"""
    if not is_admin(interaction):
        return await interaction.response.send_message(
            embed=EmbedBuilder.error("Truy cập bị từ chối", "Chỉ admin mới dùng được lệnh này!"),
            ephemeral=True
        )
    
    u = db.get_user(user.id)
    tier, tier_icon = get_user_tier(user.id)
    
    embed = EmbedBuilder.custom(
        title=f"Thông tin {user.name}",
        description=f"User ID: `{user.id}`",
        color=Colors.PRIMARY,
        icon=EMOJI['stats']
    )
    
    embed.add_field(name="Hạng", value=f"{tier_icon} {tier}", inline=True)
    embed.add_field(name="Hôm nay", value=f"{u['uses_today']} lượt", inline=True)
    embed.add_field(name="Tổng cộng", value=f"{format_number(u['total'])} lượt", inline=True)
    embed.add_field(name="Lượt thưởng", value=f"{u['bonus']} lượt", inline=True)
    embed.add_field(name="Reset lần cuối", value=u['last_reset'], inline=True)
    
    embed.set_thumbnail(url=user.display_avatar.url)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="reset_user", description="👑 [ADMIN] Reset toàn bộ dữ liệu user")
async def reset_user(interaction: discord.Interaction, user: discord.User):
    """Reset user data"""
    if not is_admin(interaction):
        return await interaction.response.send_message(
            embed=EmbedBuilder.error("Truy cập bị từ chối", "Chỉ admin mới dùng được lệnh này!"),
            ephemeral=True
        )
    
    uid = str(user.id)
    
    if uid in db.data["users"]:
        del db.data["users"][uid]
    
    if user.id in db.data["vip_users"]:
        db.data["vip_users"].remove(user.id)
    
    db.save()
    
    embed = EmbedBuilder.success(
        "Đã reset user!",
        f"Toàn bộ dữ liệu của {user.mention} đã bị xóa."
    )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="broadcast", description="👑 [ADMIN] Gửi thông báo toàn server")
async def broadcast(interaction: discord.Interaction, message: str):
    """Broadcast message"""
    if not is_admin(interaction):
        return await interaction.response.send_message(
            embed=EmbedBuilder.error("Truy cập bị từ chối", "Chỉ admin mới dùng được lệnh này!"),
            ephemeral=True
        )
    
    await interaction.response.send_message(
        embed=EmbedBuilder.info("Đang gửi thông báo...", "Vui lòng đợi...")
    )
    
    success = 0
    failed = 0
    
    broadcast_embed = EmbedBuilder.custom(
        title="Thông báo từ Bot Admin",
        description=message,
        color=Colors.WARNING,
        icon=EMOJI['info']
    )
    broadcast_embed.set_footer(text="Advanced Pack Converter v2.0")
    
    for guild in bot.guilds:
        channel = guild.system_channel
        if not channel:
            for ch in guild.text_channels:
                if ch.permissions_for(guild.me).send_messages:
                    channel = ch
                    break
        
        if channel:
            try:
                await channel.send(embed=broadcast_embed)
                success += 1
            except:
                failed += 1
        else:
            failed += 1
    
    result_embed = EmbedBuilder.success(
        "Hoàn tất gửi thông báo!",
        f"Đã gửi đến **{success}/{len(bot.guilds)}** servers."
    )
    result_embed.add_field(name="Thành công", value=str(success), inline=True)
    result_embed.add_field(name="Thất bại", value=str(failed), inline=True)
    
    await interaction.edit_original_response(embed=result_embed)

# ==================== RUN BOT ====================
if __name__ == "__main__":
    print("\n" + "="*70)
    print(f"  {EMOJI['rocket']} KHỞI ĐỘNG BOT CHUYỂN ĐỔI PACK")
    print("="*70)
    
    if TOKEN == "MTMyMDgxOTE4NjI2MjA5Nzk5MA.GJ9K5P.sI0A7ySF6wWh5jb9uSI5G2FzvvIDPjmSlGCsNU":
        print(f"\n{EMOJI['error']} CẢNH BÁO: Vui lòng thay TOKEN của bạn vào dòng 24!")
        print(f"{EMOJI['info']} Tìm TOKEN tại: Discord Developer Portal → Bot → Token\n")
        sys.exit(1)
    
    print(f"{EMOJI['loading']} Đang kết nối...\n")
    
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print(f"\n{EMOJI['error']} TOKEN không hợp lệ! Vui lòng kiểm tra lại.\n")
    except Exception as e:
        print(f"\n{EMOJI['error']} Lỗi: {e}\n")
