# 🎮 ItemsAdder to Bedrock Converter Bot v3.0

Discord bot chuyển đổi ItemsAdder resource packs sang Bedrock Edition với đầy đủ tính năng.

## ✨ Features

### 🔄 Convert Commands
- **`/convert`** - Chuyển đổi TOÀN BỘ pack (models, textures, sounds, animations)
  - Nhận: File upload HOẶC URL link (OneDrive/Dropbox/Google Drive)
  - Output: .mcpack + .zip + custom_mappings.json
  
- **`/convert_models`** - Chuyển đổi riêng Model Quái (ModelEngine)
  - Nhận: File upload HOẶC URL link
  - Output: MobModels_Bedrock.mcpack + mob_models_geyser.zip

### 📤 Smart Upload
- **File nhỏ (<8MB)**: Gửi trực tiếp qua Discord DM
- **File lớn (>8MB)**: Tự động upload lên cloud
  - **Catbox.moe** (ưu tiên) - Lưu vĩnh viễn, 200MB max
  - **Gofile.io** (fallback) - Lưu 10 ngày, 100GB max

### 📊 Stats & Management
- **`/status`** - Xem thông tin tài khoản, lượt sử dụng
- **`/uptime`** - [Admin] Thông tin hệ thống chi tiết (CPU, RAM, Disk)
- **`/help`** - Hướng dẫn sử dụng
- **`/listservers`** - [Admin] Danh sách servers
- **`/approve <server_id>`** - [Admin] Phê duyệt server

### 🎯 Converter v3.0
- ✅ Models (3,674+)
- ✅ Textures (4,513+)
- ✅ Sounds (235+) - **MỚI!**
- ✅ Animations (9+) - **MỚI!**
- ✅ Particles support - **MỚI!**

---

## 📦 Installation

### 1. Requirements
```bash
# Python 3.8+
python --version

# Install dependencies
pip install -r requirements.txt
```

### 2. Files Structure
```
your_bot/
├── discord_bot.py                      # Bot chính
├── ia_to_geyser_converter_v3.py        # Converter v3 (đầy đủ sounds)
├── mob_model_converter.py              # Model quái converter
├── file_download_helper.py             # Download từ OneDrive/Dropbox/GDrive
├── catbox_uploader.py                  # Upload lên Catbox/Gofile
├── requirements.txt                    # Dependencies
├── bot_database.json                   # Auto tạo khi chạy
└── README.md                           # File này
```

### 3. Configuration

Mở `discord_bot.py` và sửa:

```python
# Dòng 19-21: Bot Token
DISCORD_TOKEN = "YOUR_BOT_TOKEN_HERE"

# Dòng 23-24: Admin IDs
ADMIN_IDS = [123456789, 987654321]  # Thay bằng Discord User ID của bạn
```

### 4. Get Discord Bot Token

1. Vào https://discord.com/developers/applications
2. Create New Application
3. Bot → Add Bot
4. Token → Copy
5. Paste vào `DISCORD_TOKEN`

### 5. Get Your Discord ID

1. Discord → Settings → Advanced → Enable Developer Mode
2. Click chuột phải vào tên bạn → Copy ID
3. Paste vào `ADMIN_IDS`

---

## 🚀 Usage

### Start Bot
```bash
python discord_bot.py
```

### Commands

#### For Users:
```
/convert file:<attach_pack.zip>
/convert url:https://dropbox.com/.../pack.zip

/convert_models file:<attach_pack.zip>
/convert_models url:https://onedrive.live.com/.../pack.zip

/status
/help
```

#### For Admins:
```
/approve 123456789012345678
/listservers
/uptime
```

---

## 📊 Stats Display

### When uploading to Catbox/Gofile:
```
✅ Files đã upload thành công!
📦 Uploaded 3 files lên Catbox

📊 Thống kê
📦 Size: 12.55 MB
🎮 Models: 3,674
🎨 Textures: 4,513
🔊 Sounds: 235
🚀 Animations: 9

📁 Download Links
📦 ItemsAdder_Bedrock.mcpack
└ https://files.catbox.moe/abc123.mcpack

📦 bedrock_pack.zip
└ https://files.catbox.moe/def456.zip

📦 custom_mappings.json
└ https://files.catbox.moe/ghi789.json
```

---

## 🎯 Supported Download Sources

### OneDrive
```
https://onedrive.live.com/download?...
https://1drv.ms/u/s!...
```

### Dropbox
```
https://www.dropbox.com/s/...?dl=0
https://www.dropbox.com/sh/...
```

### Google Drive
```
https://drive.google.com/file/d/FILE_ID/view
https://drive.google.com/open?id=FILE_ID
```

### Direct Link
```
https://example.com/pack.zip
```

---

## ⚙️ Configuration Options

### Plan Limits (trong bot_database.json)
```json
{
  "plan_limits": {
    "free": 5,    // Lượt/ngày cho user free
    "vip": 20     // Lượt/ngày cho VIP
  }
}
```

### Admin Functions
```python
# Thêm VIP user
db.data["vip_users"].append(USER_ID)
db.save()

# Approve server
db.data["approved_servers"].append(SERVER_ID)
db.save()

# Add bonus uses
user = db.get_user(USER_ID)
user["bonus"] = 10  # Thêm 10 lượt bonus
db.save()
```

---

## 🐛 Troubleshooting

### Bot không online?
```bash
# Check token
echo $DISCORD_TOKEN

# Check Python version
python --version  # Cần 3.8+

# Check dependencies
pip list | grep discord
```

### Convert lỗi?
```bash
# Check files tồn tại
ls -la *.py

# Check permissions
chmod +x discord_bot.py

# Check logs
tail -f bot.log  # Nếu có logging
```

### Upload lỗi?
```bash
# Check internet
ping catbox.moe
ping gofile.io

# Check file size
# Discord: 8MB max
# Catbox: 200MB max
# Gofile: 100GB max
```

---

## 📝 Notes

### Converter v3 vs v2
- **v2**: Chỉ models + textures
- **v3**: Models + textures + sounds + animations + particles

### Catbox vs Gofile
- **Catbox**: Lưu vĩnh viễn, 200MB, nhanh
- **Gofile**: Lưu 10 ngày, 100GB, fallback

### Model Mob vs Full Pack
- **Model Mob**: Không cần custom_mappings.json
- **Full Pack**: CẦN custom_mappings.json cho items

---

## 🎉 Credits

- **Converter Engine**: Custom built for ItemsAdder → Bedrock
- **Cloud Upload**: Catbox.moe, Gofile.io
- **Discord.py**: https://github.com/Rapptz/discord.py

---

## 📞 Support

Nếu gặp vấn đề, liên hệ admin bot hoặc tạo issue!

---

**Version**: 3.0  
**Last Updated**: February 2026  
**Made with ❤️ for Minecraft Bedrock Community**
