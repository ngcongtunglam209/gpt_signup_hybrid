<!-- =====================================================================
  gpt_signup_hybrid — Multi-language README
  Languages: 🇻🇳 VN · 🇬🇧 EN · 🇨🇳 CN · 🇮🇩 ID · 🇮🇳 IN
  ===================================================================== -->

<div align="center">

# 🤖 gpt_signup_hybrid

**Automated ChatGPT signup pipeline · FastAPI + Camoufox + SQLite**

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![Docker Ready](https://img.shields.io/badge/docker-ready-2496ED.svg?logo=docker)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-private-red.svg)](#)
[![Version](https://img.shields.io/badge/version-3.5.0-green.svg)](./CHANGELOG.md)

</div>

---

## 💖 Donate / Support · 捐赠 · Dukungan · दान

> 🇻🇳 Nếu dự án giúp bạn — hãy donate ủng hộ tác giả tiếp tục maintain.
> 🇬🇧 If this project helps you, please consider supporting the author.
> 🇨🇳 如果项目对您有帮助，请考虑赞助作者。
> 🇮🇩 Jika project ini membantu Anda, mohon dukung penulis.
> 🇮🇳 अगर ये project आपके काम आया तो author को support करें।

| Method | Address |
|---|---|
| 🟡 **Binance ID** | `356552242` |
| 🟢 **USDT (BEP20)** | `0x137a3bfa30ee426127367773dfce16aefce04e02` |
| 🔴 **USDT (TRC20)** | `TFy5d1EDT4WBKgtoypx7Ua2dCZhPHMSDNs` |
| ✈️ **Telegram** | [@prr9293](https://t.me/prr9293) |
| 👥 **Telegram Group** | [t.me/+C6eafntO-Eo1Njdl](https://t.me/+C6eafntO-Eo1Njdl) |

---

## 🌐 Choose Your Language · 选择语言 · Pilih Bahasa · भाषा चुनें

- 🇻🇳 [**Tiếng Việt**](#-tiếng-việt) — Hướng dẫn đầy đủ bằng tiếng Việt
- 🇬🇧 [**English**](#-english) — Full documentation in English
- 🇨🇳 [**中文**](#-中文) — 完整中文文档
- 🇮🇩 [**Bahasa Indonesia**](#-bahasa-indonesia) — Dokumentasi lengkap Bahasa Indonesia
- 🇮🇳 [**हिन्दी / Hindi**](#-हिन्दी--hindi) — पूरी हिंदी documentation

---

## ⚡ TL;DR — One-line Docker Start

```bash
git clone https://github.com/6c696e68/gpt_signup_hybrid.git && cd gpt_signup_hybrid \
  && cp .env.docker.example .env \
  && sed -i.bak "s/change-me-strong-random/$(openssl rand -hex 32)/" .env \
  && docker compose up -d \
  && echo "Open: http://127.0.0.1:8083/?token=$(grep GPT_SIGNUP_WEB_TOKEN .env | cut -d= -f2)"
```

> ⚠️ **Quan trọng / Important**: Để nhận **ưu đãi giá ChatGPT Plus**, hãy chạy trên **VPS Nhật Bản (JP)** hoặc **Việt Nam (VN)**, hoặc tunnel qua VPN JP/VN. Khu vực khác giá đắt hơn hoặc bị geo-block.


---

<a id="-tiếng-việt"></a>
# 🇻🇳 Tiếng Việt

## 📖 Giới thiệu

`gpt_signup_hybrid` là pipeline tự động đăng ký tài khoản ChatGPT có giao diện web local, bao gồm:

- 🎯 **Hybrid registration** — kết hợp Camoufox (Firefox-shaped browser) + curl_cffi (TLS impersonation) né detection
- 📧 **Mail provider** đa dạng: iCloud HME v3, Outlook pool, Gmail, custom Worker API
- 💳 **Payment automation**: ChatGPT Plus checkout, Stripe, GoPay/Midtrans, UPI
- 🔐 **MFA/TOTP** tự động enable 2FA sau signup
- 🍎 **iCloud Hide My Email pool** — tự sinh email + rotate profile
- 🔄 **AutoReg loop** — sinh HME → tạo account → enable MFA tự động
- 🌐 **Local web UI** (FastAPI) với realtime SSE log, settings store, proxy pool
- 🦀 **Rust UPI bot** (`rust_upi_bot/`) cho payment automation tốc độ cao

## ✨ Tính năng nổi bật

| Feature | Mô tả |
|---|---|
| **3 chế độ đăng ký** | `pure_request` (HTTP-only nhanh nhất), `browser` (Camoufox full), `hybrid` (khuyên dùng) |
| **Anti-ban** | Sentinel sidecar K2/K2c, persona cookies, Datadog RUM injection, human typing |
| **Concurrent** | Chạy song song nhiều job, share Camoufox instance theo proxy để tiết kiệm RAM |
| **Persist** | SQLite WAL với migration version-based, backup/restore an toàn |
| **Settings Store** | Single source of truth, no localStorage runtime config |
| **Geo-locale auto** | Detect proxy IP → set locale/timezone/persona phù hợp |

## 🐳 Cài đặt với Docker (Khuyên dùng — ai cũng chạy được)

### Yêu cầu

- **Docker Desktop** (Windows/macOS) hoặc **Docker Engine** + **Docker Compose** (Linux)
- RAM tối thiểu **4GB** (khuyến nghị 8GB nếu chạy concurrent ≥ 3)
- Internet ổn định
- **VPS đặt tại JP hoặc VN** để nhận **giá ChatGPT Plus ưu đãi** (xem mục VPN bên dưới)

### Bước 1 — Cài Docker

**Windows / macOS:**
```
Tải Docker Desktop: https://www.docker.com/products/docker-desktop/
Cài → Khởi động → Kiểm tra: docker --version
```

**Linux (Ubuntu/Debian):**
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker
docker --version
```

### Bước 2 — Clone repo

```bash
git clone https://github.com/6c696e68/gpt_signup_hybrid.git
cd gpt_signup_hybrid
```

### Bước 3 — Tạo file `.env`

```bash
cp .env.docker.example .env
```

Mở `.env` bằng editor và **bắt buộc** sửa `GPT_SIGNUP_WEB_TOKEN`:

```dotenv
# Sinh token mạnh — Linux/macOS:
GPT_SIGNUP_WEB_TOKEN=$(openssl rand -hex 32)

# Windows PowerShell:
# [Convert]::ToHexString((1..32 | %{Get-Random -Max 256}))
```

Hoặc dùng one-liner:

```bash
# Linux / macOS
sed -i.bak "s/change-me-strong-random/$(openssl rand -hex 32)/" .env

# Windows (Git Bash)
sed -i "s/change-me-strong-random/$(openssl rand -hex 32)/" .env
```

### Bước 4 — Build và chạy

```bash
# Build image (lần đầu, mất 5-10 phút vì download Camoufox + Playwright Firefox)
docker compose build

# Chạy background
docker compose up -d

# Xem log realtime
docker compose logs -f web
```

> 🟢 **Apple Silicon (M1/M2/M3) deploy lên VPS amd64**: dùng buildx
> ```bash
> docker buildx build --platform linux/amd64 -t gsh:latest --load .
> ```

### Bước 5 — Truy cập Web UI

```bash
# Lấy token từ .env
TOKEN=$(grep GPT_SIGNUP_WEB_TOKEN .env | cut -d= -f2)
echo "http://127.0.0.1:8083/?token=$TOKEN"
```

Mở URL trên trong trình duyệt. UI có các tab:
- **Register** — đăng ký account mới
- **Session** — lấy session JSON từ combo email/pass
- **Link** — tạo checkout URL ChatGPT Plus / GoPay
- **HME** — quản lý iCloud Hide My Email pool
- **AutoReg** — vòng lặp tự động sinh HME → đăng ký
- **Settings** — cấu hình runtime (proxy, concurrency, mail mode, ...)

### Bước 6 — Bật iCloud HME runner (tuỳ chọn)

```bash
# Chạy thêm container icloud-hme generator loop
docker compose --profile hme up -d
```

### Lệnh quản lý hữu ích

```bash
docker compose ps                  # xem status container
docker compose logs -f web         # tail log web
docker compose restart web         # restart
docker compose down                # dừng (giữ volume data)
docker compose down -v             # dừng + xóa data (cẩn thận!)
docker compose pull && docker compose up -d --build   # update
```

### Backup / Restore dữ liệu

Dữ liệu nằm trong named volume `gsh-runtime`:

```bash
# Backup
docker run --rm -v gpt_signup_hybrid_gsh-runtime:/data -v $(pwd):/backup \
  alpine tar czf /backup/runtime-backup-$(date +%Y%m%d).tar.gz -C /data .

# Restore
docker run --rm -v gpt_signup_hybrid_gsh-runtime:/data -v $(pwd):/backup \
  alpine tar xzf /backup/runtime-backup-YYYYMMDD.tar.gz -C /data
```

## 🌏 VPN / VPS để nhận ưu đãi giá ChatGPT Plus

ChatGPT Plus áp dụng **purchasing power parity (PPP)** — giá thay đổi theo quốc gia. Các khu vực **giá rẻ nhất** thường là:

| Vùng | Đặc điểm | Khuyến nghị |
|---|---|---|
| 🇯🇵 **Japan (JP)** | Giá ổn định, ít bị check chéo | **Tốt nhất cho production** |
| 🇻🇳 **Vietnam (VN)** | Giá rẻ nhất khu vực, payment dễ qua | **Tốt nhất cho test** |
| 🇮🇳 India | Giá rẻ nhưng phải UPI + có thể bị ban datacenter | Cần proxy residential |
| 🇮🇩 Indonesia | GoPay/Midtrans flow, giá trung bình | Hỗ trợ sẵn trong code |

### Cách 1: Thuê VPS đặt tại JP/VN

Các nhà cung cấp khuyến nghị:
- **Vultr**: chọn Tokyo/Osaka location
- **Linode/Akamai**: Tokyo
- **DigitalOcean**: Singapore (gần JP, latency thấp)
- **VPS Việt Nam**: Viettel IDC, FPT Cloud, BizflyCloud

Cấu hình tối thiểu: **2 vCPU / 4GB RAM / 40GB SSD / Ubuntu 22.04+**

### Cách 2: VPN gateway

Nếu phải chạy ở vùng khác, tunnel qua VPN JP/VN:
- **WireGuard** server đặt tại JP/VN
- **OpenVPN** với gateway JP/VN
- **Residential proxy JP/VN** (Bright Data, Soax, NetNut)

Cấu hình proxy trong UI: **Settings → Proxies** hoặc set `HYBRID_OUTLOOK_PROXY=http://user:pass@jp-proxy:port` trong `.env`.

## 🛠️ Cài thủ công (không Docker)

```bash
# Yêu cầu Python 3.13+
git clone https://github.com/6c696e68/gpt_signup_hybrid.git
cd gpt_signup_hybrid

# Linux/macOS
bash setup.sh

# Windows
setup.bat
```

`setup.sh` sẽ: tạo `.venv`, install requirements, install Playwright Firefox + Camoufox, khởi động web server tại `http://127.0.0.1:8083/`.

## 🔧 Troubleshooting

| Lỗi | Nguyên nhân & Cách xử lý |
|---|---|
| `GPT_SIGNUP_WEB_TOKEN bắt buộc` | Chưa set token trong `.env` — chạy lại Bước 3 |
| Container `unhealthy` | Check `docker compose logs web`, thường do thiếu RAM hoặc Camoufox download chưa xong |
| `Cannot bind 0.0.0.0` | Compose đã dùng `--unsafe-expose-network` mặc định, đừng bỏ flag này |
| Web UI trắng | Truy cập kèm `?token=...`, hoặc xem `docker compose logs web` |
| Job stuck `running` | Restart: `docker compose restart web`, hoặc check proxy pool trong Settings |
| Captcha/Turnstile fail | Cần **residential proxy** (đặc biệt cho India region) |
| Apple Silicon build chậm | Build trực tiếp trên VPS amd64 thay vì buildx cross-arch |

## 📁 Cấu trúc dự án

```
gpt_signup_hybrid/
├── cli.py                # Typer CLI chính (web, signup, migrate, ...)
├── signup.py             # Orchestrator đăng ký
├── browser_phase.py      # Camoufox browser flow
├── request_phase.py      # Pure HTTP flow
├── session_phase.py      # Session JSON extraction
├── payment_link.py       # Checkout + Stripe + GoPay
├── pay_upi_http.py       # UPI test (pure HTTP)
├── db/                   # SQLite engine, repositories, schema migration
├── web/                  # FastAPI server + static UI
│   ├── server.py
│   ├── manager.py
│   └── static/           # HTML/JS/CSS UI
├── icloud_hme/           # iCloud Hide My Email pool
├── autoreg/              # AutoReg flow runner
├── rust_upi_bot/         # Rust UPI bot (build riêng)
├── test/                 # Verify/smoke/check scripts
└── docs/                 # Tài liệu chi tiết
```

## 📜 Convention

- File test/debug → `test/`
- File markdown user yêu cầu → `docs/`
- Mọi runtime config qua `SettingsRepository` (SQLite), không hardcode
- Fail-fast, không fallback che lỗi

Xem chi tiết tại `AGENTS.md` và `.kiro/steering/`.


---

<a id="-english"></a>
# 🇬🇧 English

## 📖 Introduction

`gpt_signup_hybrid` is an automated ChatGPT account signup pipeline with a local web UI, featuring:

- 🎯 **Hybrid registration** — Camoufox (Firefox-shaped browser) + curl_cffi (TLS impersonation) to bypass detection
- 📧 **Mail providers**: iCloud HME v3, Outlook pool, Gmail, custom Worker API
- 💳 **Payment automation**: ChatGPT Plus checkout, Stripe, GoPay/Midtrans, UPI
- 🔐 **MFA/TOTP** auto-enable after signup
- 🍎 **iCloud Hide My Email pool** — auto-generate emails + rotate profiles
- 🔄 **AutoReg loop** — generate HME → create account → enable MFA automatically
- 🌐 **Local web UI** (FastAPI) with realtime SSE logs, settings store, proxy pool
- 🦀 **Rust UPI bot** (`rust_upi_bot/`) for high-throughput payment automation

## ✨ Key Features

| Feature | Description |
|---|---|
| **3 registration modes** | `pure_request` (HTTP-only, fastest), `browser` (Camoufox full), `hybrid` (recommended) |
| **Anti-ban** | Sentinel sidecar K2/K2c, persona cookies, Datadog RUM injection, human typing |
| **Concurrency** | Run multiple jobs in parallel, share Camoufox instance per proxy to save RAM |
| **Persistence** | SQLite WAL with version-based migration, safe backup/restore |
| **Settings Store** | Single source of truth, no localStorage runtime config |
| **Geo-locale auto** | Detect proxy IP → set matching locale/timezone/persona |

## 🐳 Docker Setup (Recommended — works for everyone)

### Requirements

- **Docker Desktop** (Windows/macOS) or **Docker Engine** + **Docker Compose** (Linux)
- Minimum **4GB RAM** (8GB recommended if concurrency ≥ 3)
- Stable internet
- **VPS in JP or VN** for **ChatGPT Plus discounted pricing** (see VPN section)

### Step 1 — Install Docker

**Windows / macOS:**
```
Download Docker Desktop: https://www.docker.com/products/docker-desktop/
Install → Start → Verify: docker --version
```

**Linux (Ubuntu/Debian):**
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker
docker --version
```

### Step 2 — Clone the repo

```bash
git clone https://github.com/6c696e68/gpt_signup_hybrid.git
cd gpt_signup_hybrid
```

### Step 3 — Create `.env`

```bash
cp .env.docker.example .env
```

Edit `.env` and **mandatorily** set `GPT_SIGNUP_WEB_TOKEN`:

```dotenv
# Generate a strong token — Linux/macOS:
GPT_SIGNUP_WEB_TOKEN=$(openssl rand -hex 32)
```

One-liner:

```bash
# Linux / macOS
sed -i.bak "s/change-me-strong-random/$(openssl rand -hex 32)/" .env
```

### Step 4 — Build and run

```bash
# Build image (first time takes 5-10 min: Camoufox + Playwright Firefox download)
docker compose build

# Run in background
docker compose up -d

# Tail logs
docker compose logs -f web
```

> 🟢 **Apple Silicon (M1/M2/M3) deploying to amd64 VPS**: use buildx
> ```bash
> docker buildx build --platform linux/amd64 -t gsh:latest --load .
> ```

### Step 5 — Access Web UI

```bash
TOKEN=$(grep GPT_SIGNUP_WEB_TOKEN .env | cut -d= -f2)
echo "http://127.0.0.1:8083/?token=$TOKEN"
```

UI tabs: **Register · Session · Link · HME · AutoReg · Settings**

### Step 6 — Enable iCloud HME runner (optional)

```bash
docker compose --profile hme up -d
```

### Useful commands

```bash
docker compose ps                                     # status
docker compose logs -f web                            # tail logs
docker compose restart web                            # restart
docker compose down                                   # stop (keep volume)
docker compose down -v                                # stop + delete data (careful!)
docker compose pull && docker compose up -d --build   # update
```

### Backup / Restore

```bash
# Backup
docker run --rm -v gpt_signup_hybrid_gsh-runtime:/data -v $(pwd):/backup \
  alpine tar czf /backup/runtime-backup-$(date +%Y%m%d).tar.gz -C /data .

# Restore
docker run --rm -v gpt_signup_hybrid_gsh-runtime:/data -v $(pwd):/backup \
  alpine tar xzf /backup/runtime-backup-YYYYMMDD.tar.gz -C /data
```

## 🌏 VPN / VPS for ChatGPT Plus discounts

ChatGPT Plus uses **purchasing power parity (PPP)** — prices vary by country. **Cheapest regions**:

| Region | Notes | Recommendation |
|---|---|---|
| 🇯🇵 **Japan (JP)** | Stable pricing, less cross-check | **Best for production** |
| 🇻🇳 **Vietnam (VN)** | Cheapest in region, easy payment | **Best for testing** |
| 🇮🇳 India | Cheap but UPI-only + datacenter ban risk | Needs residential proxy |
| 🇮🇩 Indonesia | GoPay/Midtrans flow, medium price | Built-in support |

### Option 1: Rent VPS in JP/VN

Recommended providers:
- **Vultr**: Tokyo/Osaka
- **Linode/Akamai**: Tokyo
- **DigitalOcean**: Singapore (close to JP, low latency)
- **Vietnam VPS**: Viettel IDC, FPT Cloud, BizflyCloud

Minimum spec: **2 vCPU / 4GB RAM / 40GB SSD / Ubuntu 22.04+**

### Option 2: VPN gateway

If you must run elsewhere, tunnel via JP/VN VPN:
- **WireGuard** server in JP/VN
- **OpenVPN** with JP/VN gateway
- **Residential proxy JP/VN** (Bright Data, Soax, NetNut)

Configure proxy in UI: **Settings → Proxies** or set `HYBRID_OUTLOOK_PROXY=http://user:pass@jp-proxy:port` in `.env`.

## 🛠️ Manual install (no Docker)

```bash
# Requires Python 3.13+
git clone https://github.com/6c696e68/gpt_signup_hybrid.git
cd gpt_signup_hybrid

# Linux/macOS
bash setup.sh

# Windows
setup.bat
```

## 🔧 Troubleshooting

| Error | Cause & Fix |
|---|---|
| `GPT_SIGNUP_WEB_TOKEN required` | Token not set in `.env` — redo Step 3 |
| Container `unhealthy` | Check `docker compose logs web`, often low RAM or Camoufox download incomplete |
| `Cannot bind 0.0.0.0` | Compose uses `--unsafe-expose-network` by default — don't remove it |
| Blank Web UI | Add `?token=...`, or check `docker compose logs web` |
| Job stuck `running` | Restart: `docker compose restart web`, or check proxy pool in Settings |
| Captcha/Turnstile fail | Need **residential proxy** (especially for India region) |
| Apple Silicon slow build | Build directly on amd64 VPS instead of cross-arch buildx |


---

<a id="-中文"></a>
# 🇨🇳 中文

## 📖 项目介绍

`gpt_signup_hybrid` 是一个带本地 Web UI 的 ChatGPT 账号自动注册流水线，主要功能：

- 🎯 **混合注册模式** — Camoufox（Firefox 形态浏览器）+ curl_cffi（TLS 指纹伪装）绕过检测
- 📧 **邮件提供商**：iCloud HME v3、Outlook 池、Gmail、自定义 Worker API
- 💳 **支付自动化**：ChatGPT Plus 结账、Stripe、GoPay/Midtrans、UPI
- 🔐 注册后**自动启用 MFA/TOTP**
- 🍎 **iCloud Hide My Email 池** — 自动生成邮箱 + 轮换 profile
- 🔄 **AutoReg 循环** — 自动生成 HME → 创建账号 → 启用 MFA
- 🌐 **本地 Web UI**（FastAPI）支持实时 SSE 日志、设置存储、代理池
- 🦀 **Rust UPI bot**（`rust_upi_bot/`）高吞吐支付自动化

## ✨ 核心特性

| 特性 | 说明 |
|---|---|
| **3 种注册模式** | `pure_request`（纯 HTTP，最快）、`browser`（完整 Camoufox）、`hybrid`（推荐） |
| **反封禁** | Sentinel sidecar K2/K2c、persona cookies、Datadog RUM 注入、人类打字模拟 |
| **并发** | 多任务并行，按代理共享 Camoufox 实例节省内存 |
| **持久化** | SQLite WAL，基于版本的迁移，安全备份/恢复 |
| **设置存储** | 单一数据源，runtime 配置不放 localStorage |
| **自动地理定位** | 检测代理 IP → 设置匹配的 locale/时区/persona |

## 🐳 Docker 部署（推荐 — 所有人都能跑）

### 前置要求

- **Docker Desktop**（Windows/macOS）或 **Docker Engine** + **Docker Compose**（Linux）
- 最低 **4GB 内存**（并发 ≥ 3 建议 8GB）
- 稳定网络
- **VPS 部署在日本 (JP) 或越南 (VN)** 可获得 **ChatGPT Plus 优惠价**（见下方 VPN 章节）

### 步骤 1 — 安装 Docker

**Windows / macOS:**
```
下载 Docker Desktop: https://www.docker.com/products/docker-desktop/
安装 → 启动 → 验证: docker --version
```

**Linux (Ubuntu/Debian):**
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker
docker --version
```

### 步骤 2 — 克隆仓库

```bash
git clone https://github.com/6c696e68/gpt_signup_hybrid.git
cd gpt_signup_hybrid
```

### 步骤 3 — 创建 `.env`

```bash
cp .env.docker.example .env
```

编辑 `.env` 并**必须**设置 `GPT_SIGNUP_WEB_TOKEN`：

```bash
sed -i.bak "s/change-me-strong-random/$(openssl rand -hex 32)/" .env
```

### 步骤 4 — 构建并运行

```bash
# 首次构建（需要 5-10 分钟，下载 Camoufox + Playwright Firefox）
docker compose build

# 后台运行
docker compose up -d

# 查看实时日志
docker compose logs -f web
```

> 🟢 **Apple Silicon (M1/M2/M3) 部署到 amd64 VPS**: 用 buildx
> ```bash
> docker buildx build --platform linux/amd64 -t gsh:latest --load .
> ```

### 步骤 5 — 访问 Web UI

```bash
TOKEN=$(grep GPT_SIGNUP_WEB_TOKEN .env | cut -d= -f2)
echo "http://127.0.0.1:8083/?token=$TOKEN"
```

UI 标签页：**注册 · Session · Link · HME · AutoReg · 设置**

### 步骤 6 — 启用 iCloud HME runner（可选）

```bash
docker compose --profile hme up -d
```

### 常用命令

```bash
docker compose ps                                     # 查看状态
docker compose logs -f web                            # 跟踪日志
docker compose restart web                            # 重启
docker compose down                                   # 停止（保留 volume）
docker compose down -v                                # 停止 + 删数据（小心！）
docker compose pull && docker compose up -d --build   # 更新
```

### 数据备份 / 恢复

```bash
# 备份
docker run --rm -v gpt_signup_hybrid_gsh-runtime:/data -v $(pwd):/backup \
  alpine tar czf /backup/runtime-backup-$(date +%Y%m%d).tar.gz -C /data .

# 恢复
docker run --rm -v gpt_signup_hybrid_gsh-runtime:/data -v $(pwd):/backup \
  alpine tar xzf /backup/runtime-backup-YYYYMMDD.tar.gz -C /data
```

## 🌏 VPN / VPS 获取 ChatGPT Plus 优惠

ChatGPT Plus 采用 **购买力平价 (PPP)** 定价 — 价格因国家而异。**最便宜的地区**：

| 地区 | 说明 | 推荐 |
|---|---|---|
| 🇯🇵 **日本 (JP)** | 价格稳定，交叉验证少 | **生产环境最佳** |
| 🇻🇳 **越南 (VN)** | 地区最低价，支付方便 | **测试环境最佳** |
| 🇮🇳 印度 | 便宜但仅 UPI + 数据中心 IP 易被封 | 需住宅代理 |
| 🇮🇩 印度尼西亚 | GoPay/Midtrans 流程，中等价格 | 代码内置支持 |

### 方案 1：租用 JP/VN VPS

推荐服务商：
- **Vultr**：东京/大阪
- **Linode/Akamai**：东京
- **DigitalOcean**：新加坡（距离 JP 近，延迟低）
- **越南 VPS**：Viettel IDC、FPT Cloud、BizflyCloud

最低配置：**2 vCPU / 4GB 内存 / 40GB SSD / Ubuntu 22.04+**

### 方案 2：VPN 网关

如果必须在其他地区运行，通过 JP/VN VPN 隧道：
- **WireGuard** 服务器在 JP/VN
- **OpenVPN** 接 JP/VN 网关
- **JP/VN 住宅代理**（Bright Data、Soax、NetNut）

UI 配置：**Settings → Proxies**，或在 `.env` 设置 `HYBRID_OUTLOOK_PROXY=http://user:pass@jp-proxy:port`。

## 🛠️ 手动安装（不用 Docker）

```bash
# 需要 Python 3.13+
git clone https://github.com/6c696e68/gpt_signup_hybrid.git
cd gpt_signup_hybrid

# Linux/macOS
bash setup.sh

# Windows
setup.bat
```

## 🔧 故障排查

| 错误 | 原因 & 解决 |
|---|---|
| `GPT_SIGNUP_WEB_TOKEN required` | `.env` 没设置 token — 重做步骤 3 |
| 容器 `unhealthy` | 检查 `docker compose logs web`，常因内存不足或 Camoufox 下载未完成 |
| `Cannot bind 0.0.0.0` | Compose 默认带 `--unsafe-expose-network`，不要删除 |
| Web UI 空白 | URL 加 `?token=...`，或查看日志 |
| 任务卡在 `running` | 重启 `docker compose restart web`，或检查代理池 |
| Captcha/Turnstile 失败 | 需要**住宅代理**（特别是印度区域） |
| Apple Silicon 构建慢 | 直接在 amd64 VPS 上构建，不要用跨架构 buildx |


---

<a id="-bahasa-indonesia"></a>
# 🇮🇩 Bahasa Indonesia

## 📖 Pengenalan

`gpt_signup_hybrid` adalah pipeline pendaftaran akun ChatGPT otomatis dengan local web UI, mencakup:

- 🎯 **Hybrid registration** — Camoufox (browser bentuk Firefox) + curl_cffi (TLS impersonation) untuk bypass deteksi
- 📧 **Mail providers**: iCloud HME v3, Outlook pool, Gmail, custom Worker API
- 💳 **Otomasi pembayaran**: ChatGPT Plus checkout, Stripe, **GoPay/Midtrans** (Indonesia), UPI
- 🔐 **MFA/TOTP** auto-enable setelah signup
- 🍎 **iCloud Hide My Email pool** — auto-generate email + rotasi profile
- 🔄 **AutoReg loop** — generate HME → buat akun → enable MFA otomatis
- 🌐 **Local web UI** (FastAPI) dengan log SSE realtime, settings store, proxy pool
- 🦀 **Rust UPI bot** (`rust_upi_bot/`) untuk otomasi pembayaran throughput tinggi

## ✨ Fitur Utama

| Fitur | Deskripsi |
|---|---|
| **3 mode registrasi** | `pure_request` (HTTP-only, tercepat), `browser` (Camoufox penuh), `hybrid` (direkomendasikan) |
| **Anti-ban** | Sentinel sidecar K2/K2c, persona cookies, Datadog RUM injection, human typing |
| **Concurrency** | Jalankan beberapa job paralel, share Camoufox per proxy untuk hemat RAM |
| **Persistence** | SQLite WAL dengan migrasi version-based, backup/restore aman |
| **Settings Store** | Single source of truth, runtime config tidak di localStorage |
| **Geo-locale auto** | Deteksi proxy IP → set locale/timezone/persona yang cocok |

## 🐳 Setup Docker (Direkomendasikan — semua orang bisa jalankan)

### Kebutuhan

- **Docker Desktop** (Windows/macOS) atau **Docker Engine** + **Docker Compose** (Linux)
- RAM minimum **4GB** (rekomendasi 8GB jika concurrency ≥ 3)
- Internet stabil
- **VPS di JP atau VN** untuk **harga diskon ChatGPT Plus** (lihat bagian VPN)

### Langkah 1 — Install Docker

**Windows / macOS:**
```
Download Docker Desktop: https://www.docker.com/products/docker-desktop/
Install → Start → Cek: docker --version
```

**Linux (Ubuntu/Debian):**
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker
docker --version
```

### Langkah 2 — Clone repo

```bash
git clone https://github.com/6c696e68/gpt_signup_hybrid.git
cd gpt_signup_hybrid
```

### Langkah 3 — Buat `.env`

```bash
cp .env.docker.example .env
```

Edit `.env` dan **wajib** set `GPT_SIGNUP_WEB_TOKEN`:

```bash
sed -i.bak "s/change-me-strong-random/$(openssl rand -hex 32)/" .env
```

### Langkah 4 — Build dan jalankan

```bash
# Build image pertama kali (5-10 menit, download Camoufox + Playwright Firefox)
docker compose build

# Jalankan background
docker compose up -d

# Lihat log realtime
docker compose logs -f web
```

> 🟢 **Apple Silicon (M1/M2/M3) deploy ke VPS amd64**: pakai buildx
> ```bash
> docker buildx build --platform linux/amd64 -t gsh:latest --load .
> ```

### Langkah 5 — Akses Web UI

```bash
TOKEN=$(grep GPT_SIGNUP_WEB_TOKEN .env | cut -d= -f2)
echo "http://127.0.0.1:8083/?token=$TOKEN"
```

Tab UI: **Register · Session · Link · HME · AutoReg · Settings**

### Langkah 6 — Aktifkan iCloud HME runner (opsional)

```bash
docker compose --profile hme up -d
```

### Perintah berguna

```bash
docker compose ps                                     # status
docker compose logs -f web                            # tail logs
docker compose restart web                            # restart
docker compose down                                   # stop (volume tetap)
docker compose down -v                                # stop + hapus data (hati-hati!)
docker compose pull && docker compose up -d --build   # update
```

### Backup / Restore data

```bash
# Backup
docker run --rm -v gpt_signup_hybrid_gsh-runtime:/data -v $(pwd):/backup \
  alpine tar czf /backup/runtime-backup-$(date +%Y%m%d).tar.gz -C /data .

# Restore
docker run --rm -v gpt_signup_hybrid_gsh-runtime:/data -v $(pwd):/backup \
  alpine tar xzf /backup/runtime-backup-YYYYMMDD.tar.gz -C /data
```

## 🌏 VPN / VPS untuk diskon ChatGPT Plus

ChatGPT Plus pakai **purchasing power parity (PPP)** — harga berbeda per negara. **Region termurah**:

| Region | Catatan | Rekomendasi |
|---|---|---|
| 🇯🇵 **Jepang (JP)** | Harga stabil, jarang cross-check | **Terbaik untuk production** |
| 🇻🇳 **Vietnam (VN)** | Termurah di region, payment mudah | **Terbaik untuk testing** |
| 🇮🇳 India | Murah tapi UPI-only + risiko datacenter ban | Butuh residential proxy |
| 🇮🇩 **Indonesia** | GoPay/Midtrans, harga menengah | **Support built-in di kode** |

### Opsi 1: Sewa VPS di JP/VN

Provider rekomendasi:
- **Vultr**: Tokyo/Osaka
- **Linode/Akamai**: Tokyo
- **DigitalOcean**: Singapore (dekat JP, latency rendah)
- **VPS Vietnam**: Viettel IDC, FPT Cloud, BizflyCloud

Spesifikasi minimum: **2 vCPU / 4GB RAM / 40GB SSD / Ubuntu 22.04+**

### Opsi 2: VPN gateway

Jika harus jalan di region lain, tunnel via VPN JP/VN:
- **WireGuard** server di JP/VN
- **OpenVPN** dengan gateway JP/VN
- **Residential proxy JP/VN** (Bright Data, Soax, NetNut)

Konfigurasi proxy di UI: **Settings → Proxies** atau set `HYBRID_OUTLOOK_PROXY=http://user:pass@jp-proxy:port` di `.env`.

## 🛠️ Install manual (tanpa Docker)

```bash
# Butuh Python 3.13+
git clone https://github.com/6c696e68/gpt_signup_hybrid.git
cd gpt_signup_hybrid

# Linux/macOS
bash setup.sh

# Windows
setup.bat
```

## 🔧 Troubleshooting

| Error | Penyebab & Solusi |
|---|---|
| `GPT_SIGNUP_WEB_TOKEN required` | Token belum di-set di `.env` — ulangi Langkah 3 |
| Container `unhealthy` | Cek `docker compose logs web`, biasanya RAM kurang atau Camoufox download belum selesai |
| `Cannot bind 0.0.0.0` | Compose default pakai `--unsafe-expose-network` — jangan dihapus |
| Web UI kosong | Akses pakai `?token=...`, atau cek logs |
| Job stuck `running` | Restart `docker compose restart web`, atau cek proxy pool di Settings |
| Captcha/Turnstile gagal | Butuh **residential proxy** (terutama untuk region India) |
| Build lambat di Apple Silicon | Build langsung di VPS amd64, jangan cross-arch buildx |


---

<a id="-हिन्दी--hindi"></a>
# 🇮🇳 हिन्दी / Hindi

## 📖 परिचय

`gpt_signup_hybrid` एक automated ChatGPT account signup pipeline है जिसमें local web UI शामिल है:

- 🎯 **Hybrid registration** — Camoufox (Firefox-shape browser) + curl_cffi (TLS impersonation) detection bypass करने के लिए
- 📧 **Mail providers**: iCloud HME v3, Outlook pool, Gmail, custom Worker API
- 💳 **Payment automation**: ChatGPT Plus checkout, Stripe, GoPay/Midtrans, **UPI (India)**
- 🔐 **MFA/TOTP** signup के बाद auto-enable
- 🍎 **iCloud Hide My Email pool** — auto-generate emails + profile rotation
- 🔄 **AutoReg loop** — HME generate → account create → MFA enable automatically
- 🌐 **Local web UI** (FastAPI) realtime SSE logs, settings store, proxy pool के साथ
- 🦀 **Rust UPI bot** (`rust_upi_bot/`) high-throughput payment automation के लिए

## ✨ मुख्य Features

| Feature | विवरण |
|---|---|
| **3 registration modes** | `pure_request` (HTTP-only, सबसे fast), `browser` (Camoufox full), `hybrid` (recommended) |
| **Anti-ban** | Sentinel sidecar K2/K2c, persona cookies, Datadog RUM injection, human typing |
| **Concurrency** | Multiple jobs parallel, per-proxy Camoufox share करके RAM बचाएँ |
| **Persistence** | SQLite WAL with version-based migration, safe backup/restore |
| **Settings Store** | Single source of truth, runtime config localStorage में नहीं |
| **Geo-locale auto** | Proxy IP detect → matching locale/timezone/persona set |

## 🐳 Docker Setup (Recommended — सबके लिए काम करता है)

### Requirements

- **Docker Desktop** (Windows/macOS) या **Docker Engine** + **Docker Compose** (Linux)
- Minimum **4GB RAM** (concurrency ≥ 3 के लिए 8GB recommended)
- Stable internet
- **JP या VN में VPS** — **ChatGPT Plus discounted pricing** के लिए (नीचे VPN section देखें)

### Step 1 — Docker install करें

**Windows / macOS:**
```
Docker Desktop download करें: https://www.docker.com/products/docker-desktop/
Install → Start → Verify: docker --version
```

**Linux (Ubuntu/Debian):**
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker
docker --version
```

### Step 2 — Repo clone करें

```bash
git clone https://github.com/6c696e68/gpt_signup_hybrid.git
cd gpt_signup_hybrid
```

### Step 3 — `.env` create करें

```bash
cp .env.docker.example .env
```

`.env` edit करें और **mandatorily** `GPT_SIGNUP_WEB_TOKEN` set करें:

```bash
sed -i.bak "s/change-me-strong-random/$(openssl rand -hex 32)/" .env
```

### Step 4 — Build और run करें

```bash
# पहली बार build (5-10 minutes लगेंगे, Camoufox + Playwright Firefox download होगा)
docker compose build

# Background में run
docker compose up -d

# Realtime logs
docker compose logs -f web
```

> 🟢 **Apple Silicon (M1/M2/M3) से amd64 VPS पर deploy**: buildx use करें
> ```bash
> docker buildx build --platform linux/amd64 -t gsh:latest --load .
> ```

### Step 5 — Web UI access करें

```bash
TOKEN=$(grep GPT_SIGNUP_WEB_TOKEN .env | cut -d= -f2)
echo "http://127.0.0.1:8083/?token=$TOKEN"
```

UI tabs: **Register · Session · Link · HME · AutoReg · Settings**

### Step 6 — iCloud HME runner enable करें (optional)

```bash
docker compose --profile hme up -d
```

### Useful commands

```bash
docker compose ps                                     # status
docker compose logs -f web                            # tail logs
docker compose restart web                            # restart
docker compose down                                   # stop (volume safe)
docker compose down -v                                # stop + delete data (सावधान!)
docker compose pull && docker compose up -d --build   # update
```

### Backup / Restore data

```bash
# Backup
docker run --rm -v gpt_signup_hybrid_gsh-runtime:/data -v $(pwd):/backup \
  alpine tar czf /backup/runtime-backup-$(date +%Y%m%d).tar.gz -C /data .

# Restore
docker run --rm -v gpt_signup_hybrid_gsh-runtime:/data -v $(pwd):/backup \
  alpine tar xzf /backup/runtime-backup-YYYYMMDD.tar.gz -C /data
```

## 🌏 ChatGPT Plus discounts के लिए VPN / VPS

ChatGPT Plus **purchasing power parity (PPP)** pricing use करता है — country-wise prices अलग होते हैं। **सबसे सस्ते regions**:

| Region | Notes | Recommendation |
|---|---|---|
| 🇯🇵 **Japan (JP)** | Stable pricing, कम cross-check | **Production के लिए best** |
| 🇻🇳 **Vietnam (VN)** | Region में सबसे सस्ता, easy payment | **Testing के लिए best** |
| 🇮🇳 **India** | सस्ता but UPI-only + datacenter ban risk | **Residential proxy ज़रूरी** |
| 🇮🇩 Indonesia | GoPay/Midtrans flow, medium price | Code में built-in support |

### Option 1: JP/VN में VPS किराए पर लें

Recommended providers:
- **Vultr**: Tokyo/Osaka
- **Linode/Akamai**: Tokyo
- **DigitalOcean**: Singapore (JP के पास, low latency)
- **Vietnam VPS**: Viettel IDC, FPT Cloud, BizflyCloud

Minimum spec: **2 vCPU / 4GB RAM / 40GB SSD / Ubuntu 22.04+**

### Option 2: VPN gateway

अगर दूसरी जगह run करना है, JP/VN VPN के through tunnel करें:
- **WireGuard** server JP/VN में
- **OpenVPN** JP/VN gateway के साथ
- **Residential proxy JP/VN** (Bright Data, Soax, NetNut)

UI में configure करें: **Settings → Proxies** या `.env` में `HYBRID_OUTLOOK_PROXY=http://user:pass@jp-proxy:port` set करें।

### India users के लिए विशेष notes

- ChatGPT Plus India में **UPI payment** से purchase होता है — code में built-in support
- **Residential proxy ज़रूरी** है (datacenter IPs अक्सर ban हो जाते हैं Turnstile पर)
- `rust_upi_bot/` में dedicated UPI automation tool है
- Test scripts: `test/check_har_signup_deep.py`, `pay_upi_http.py`

## 🛠️ Manual install (Docker के बिना)

```bash
# Python 3.13+ required
git clone https://github.com/6c696e68/gpt_signup_hybrid.git
cd gpt_signup_hybrid

# Linux/macOS
bash setup.sh

# Windows
setup.bat
```

## 🔧 Troubleshooting

| Error | Cause & Fix |
|---|---|
| `GPT_SIGNUP_WEB_TOKEN required` | `.env` में token नहीं set — Step 3 दोबारा करें |
| Container `unhealthy` | `docker compose logs web` check करें, अक्सर RAM कम या Camoufox download incomplete |
| `Cannot bind 0.0.0.0` | Compose default में `--unsafe-expose-network` use करता है — remove मत करें |
| Blank Web UI | URL में `?token=...` add करें, या logs check करें |
| Job stuck `running` | Restart: `docker compose restart web`, या Settings में proxy pool check करें |
| Captcha/Turnstile fail | **Residential proxy** चाहिए (especially India region) |
| Apple Silicon slow build | Cross-arch buildx के बजाय directly amd64 VPS पर build करें |

---

## 📚 Additional Resources

- 📖 **Detailed docs**: `docs/`
- 🏗️ **Architecture**: `.planning/codebase/ARCHITECTURE.md`
- 📋 **Changelog**: `CHANGELOG.md`
- 🤖 **Agent guide**: `AGENTS.md` (Claude/Codex/Kiro instructions)
- 🧪 **Tests**: `test/check_*.py`, `test/smoke_*.py`, `test/test_*.py`

## ⚖️ Disclaimer

This tool is provided for **educational and authorized testing purposes only**. Users are responsible for complying with OpenAI Terms of Service and local laws. The author is not responsible for misuse.

---

<div align="center">

**Made with ❤️ · Star ⭐ if useful · [Telegram Group](https://t.me/+C6eafntO-Eo1Njdl)**

</div>
