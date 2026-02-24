# 🚂 Deploy Bot lên Railway

Hướng dẫn chi tiết deploy Discord bot lên Railway.app

---

## 📋 Yêu Cầu

### 1. Tài Khoản Railway
- Đăng ký tại: https://railway.app
- **Railway Pro** ($5/tháng) - RECOMMENDED cho bot này
  - 500 hours/month execution time
  - $5 credit included
  - Priority support
  
- **Railway Free** (Hobby)
  - 500 hours/month
  - $0 credit (phải add credit card)
  - Có thể bị giới hạn

### 2. GitHub Account
- Cần có GitHub để deploy từ repo

---

## 🚀 Bước 1: Chuẩn Bị Code

### Option A: Upload lên GitHub (RECOMMENDED)

```bash
# 1. Tạo repo mới trên GitHub
# - Vào https://github.com/new
# - Tên repo: discord-itemsadder-bot (hoặc tên khác)
# - Chọn Private (nếu muốn giữ bí mật)

# 2. Clone repo về máy
git clone https://github.com/YOUR_USERNAME/discord-itemsadder-bot.git
cd discord-itemsadder-bot

# 3. Copy tất cả files bot vào folder
# Copy 7 files:
# - discord_bot.py
# - ia_to_geyser_converter_v3.py
# - mob_model_converter.py
# - file_download_helper.py
# - catbox_uploader.py
# - requirements.txt
# - Procfile
# - railway.json
# - runtime.txt
# - .gitignore
# - README.md
# - RAILWAY_DEPLOY.md

# 4. Commit và push
git add .
git commit -m "Initial commit - Discord bot"
git push origin main
```

### Option B: Railway CLI (Advanced)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
railway init
railway up
```

---

## 🚀 Bước 2: Deploy từ GitHub

### 1. Vào Railway Dashboard
- Mở https://railway.app/dashboard
- Click **"New Project"**

### 2. Chọn Deploy from GitHub
- Click **"Deploy from GitHub repo"**
- Authorize Railway access GitHub (lần đầu)
- Chọn repo: `discord-itemsadder-bot`
- Click **"Deploy Now"**

### 3. Railway tự động:
```
✅ Detect Python project
✅ Install dependencies từ requirements.txt
✅ Run Procfile command: python discord_bot.py
```

---

## ⚙️ Bước 3: Setup Environment Variables

### 1. Vào Project Settings
- Click vào project vừa tạo
- Click **"Variables"** tab

### 2. Thêm biến môi trường:

#### **DISCORD_TOKEN** (BẮT BUỘC)
```
Key: DISCORD_TOKEN
Value: YOUR_BOT_TOKEN_HERE
```

#### **ADMIN_IDS** (BẮT BUỘC)
```
Key: ADMIN_IDS
Value: 123456789,987654321
```
*Ngăn cách bởi dấu phẩy, không có dấu cách*

#### **DATABASE_FILE** (Optional)
```
Key: DATABASE_FILE
Value: /data/bot_database.json
```

### 3. Save Variables
- Click **"Add"** cho mỗi variable
- Railway tự động restart bot

---

## 🔧 Bước 4: Sửa Code Để Đọc Env Variables

### Update `discord_bot.py`:

```python
import os

# Đọc từ environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_FALLBACK_TOKEN")

# ADMIN_IDS - parse từ string thành list
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
if ADMIN_IDS_STR:
    ADMIN_IDS = [int(id.strip()) for id in ADMIN_IDS_STR.split(",")]
else:
    ADMIN_IDS = [123456789]  # Fallback

# Database file
DATABASE_FILE = os.getenv("DATABASE_FILE", "bot_database.json")
```

### Commit & Push:
```bash
git add discord_bot.py
git commit -m "Use environment variables"
git push origin main
```

Railway tự động deploy lại!

---

## 📊 Bước 5: Kiểm Tra Logs

### 1. Xem Logs Real-time
- Trong Railway dashboard
- Click **"View Logs"**
- Hoặc dùng CLI: `railway logs`

### 2. Kiểm tra bot đã online:
```
✅ Logged in as YourBot#1234
✅ Bot is in X servers
✅ Ready to convert!
```

### 3. Test bot trên Discord:
```
/help
/status
/convert
```

---

## 💾 Bước 6: Setup Persistent Storage (QUAN TRỌNG!)

Railway mặc định **KHÔNG LƯU FILE** khi restart!

### Option A: Railway Volumes (Pro Plan)

```bash
# 1. Vào Project Settings
# 2. Click "Volumes"
# 3. Click "+ New Volume"
# 4. Mount Path: /data
# 5. Size: 1 GB

# 6. Update code để lưu vào /data
DATABASE_FILE = "/data/bot_database.json"
TEMP_DIR = "/data/temp"
```

### Option B: External Database (Free Alternative)

```bash
# Dùng MongoDB Atlas (Free 512MB)
# https://www.mongodb.com/cloud/atlas/register

# Hoặc PostgreSQL trên Railway
# Add PostgreSQL service → Auto get DATABASE_URL
```

---

## 💰 Pricing & Resource Usage

### Railway Pro ($5/month):
```
✅ 500 hours execution time (~20 days uptime)
✅ $5 usage credit included
✅ 8GB RAM
✅ 8 vCPU
✅ Volumes support
```

### Estimated Monthly Cost:
```
Compute:
- Always-on bot: ~$0.000463/min × 43,200 min = ~$20/month
- Với $5 credit → Trả thêm ~$15/month

Volumes (nếu dùng):
- 1 GB: ~$0.25/GB/month

Total: ~$15-20/month cho Pro plan
```

### Cost Optimization:
```
✅ Dùng lightweight database (JSON file thay vì DB server)
✅ Cleanup temp files thường xuyên
✅ Giới hạn file upload size
✅ Set timeout cho conversions
```

---

## 🔍 Monitoring & Maintenance

### 1. Check Resource Usage
```
Railway Dashboard → Metrics:
- CPU usage
- RAM usage
- Network I/O
- Build time
```

### 2. Auto Restart on Crash
```json
// railway.json đã config
{
  "deploy": {
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 3. Health Check (Add to bot)
```python
@bot.event
async def on_ready():
    print(f"✅ Bot online: {bot.user.name}")
    print(f"📊 Servers: {len(bot.guilds)}")
    print(f"👥 Users: {sum(g.member_count for g in bot.guilds)}")
```

---

## 🐛 Troubleshooting

### Bot không online?
```bash
# Check logs
railway logs

# Common issues:
❌ DISCORD_TOKEN invalid → Check env variables
❌ Import error → Check requirements.txt
❌ Permission denied → Check file paths
```

### Bot bị crash?
```bash
# Check restart count
railway status

# If >10 crashes → Check logs for errors
railway logs --tail 100
```

### Database bị mất?
```bash
# Chưa setup volume!
# → Follow "Bước 6: Setup Persistent Storage"
```

### Out of credit?
```bash
# Check usage
railway dashboard → Usage

# Add more credit hoặc optimize code
```

---

## 📝 Checklist Deployment

```
✅ Code uploaded to GitHub
✅ Railway project created
✅ Environment variables set:
   ✅ DISCORD_TOKEN
   ✅ ADMIN_IDS
✅ Bot deployed successfully
✅ Logs show "Bot online"
✅ Tested /help command
✅ Tested /convert command
✅ Persistent storage setup (volume/database)
✅ Monitoring enabled
```

---

## 🎯 Next Steps

### After Deployment:
1. ✅ Test tất cả commands
2. ✅ Approve servers cần thiết
3. ✅ Setup VIP users nếu có
4. ✅ Monitor resource usage
5. ✅ Backup database thường xuyên

### Scaling Up:
```
- Nhiều users → Upgrade Railway plan
- Nhiều files → Add more storage
- Nhiều servers → Optimize code
```

---

## 🆘 Support

### Railway Support:
- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway
- Status: https://status.railway.app

### Bot Issues:
- Check logs first
- Review code
- Contact admin

---

**Pro Tips:**
- 🔒 Luôn dùng Private GitHub repo (bảo mật token)
- 💾 Setup volumes ngay từ đầu (tránh mất data)
- 📊 Monitor usage để control costs
- 🔄 Enable auto-deploy khi push code mới
- 📧 Setup email alerts cho crashes

Good luck! 🚀
