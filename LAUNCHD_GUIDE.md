# 🤖 macOS launchd 定时任务配置指南

本指南说明如何在 macOS 上设置自动定时任务，让加密货币分析系统每天自动运行。

---

## ✨ 特点

- ✅ **合盖也能运行**：Mac 睡眠时会自动唤醒执行任务
- ✅ **功耗极低**：每天只唤醒 1 分钟，额外耗电约 0.2-0.5%
- ✅ **完全自动化**：无需手动干预
- ✅ **日志记录**：所有执行记录都会保存

---

## 🚀 快速开始

### 1. 启动定时任务

```bash
./launchd_setup.sh start
```

### 2. 查看状态

```bash
./launchd_setup.sh status
```

### 3. 测试执行

```bash
# 立即执行一次（不等到明天 8:00）
./launchd_setup.sh test

# 查看实时日志
./launchd_setup.sh logs
```

---

## 📋 管理命令

| 命令 | 说明 |
|------|------|
| `./launchd_setup.sh start` | 启动定时任务 |
| `./launchd_setup.sh stop` | 停止定时任务 |
| `./launchd_setup.sh restart` | 重启定时任务 |
| `./launchd_setup.sh status` | 查看运行状态和最近日志 |
| `./launchd_setup.sh logs` | 实时查看日志输出 |
| `./launchd_setup.sh test` | 立即执行一次测试 |

---

## 📁 文件位置

```
配置文件: ~/Library/LaunchAgents/com.crypto.daily.analysis.plist
日志目录: ./logs/
  ├── launchd_stdout.log  # 标准输出日志
  └── launchd_stderr.log  # 错误日志
```

---

## ⚙️ 修改执行时间

### 方法 1：编辑 plist 文件

```bash
# 编辑配置文件
nano ~/Library/LaunchAgents/com.crypto.daily.analysis.plist

# 找到这部分并修改：
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>8</integer>      <!-- 修改这里：0-23 -->
    <key>Minute</key>
    <integer>0</integer>      <!-- 修改这里：0-59 -->
</dict>

# 重启服务使配置生效
./launchd_setup.sh restart
```

### 方法 2：设置多个执行时间

如果想每天执行多次（例如早上 8:00 和晚上 20:00）：

```xml
<!-- 替换 StartCalendarInterval 为数组 -->
<key>StartCalendarInterval</key>
<array>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <dict>
        <key>Hour</key>
        <integer>20</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</array>
```

---

## 🔋 电量消耗说明

### 工作原理

```
正常状态：Mac 睡眠中 💤
         ↓
08:00 到了：Mac 自动唤醒 ⏰
         ↓
执行任务：运行 30-60 秒 🚀
  - 获取币价数据
  - 获取新闻
  - AI 分析
  - 生成报告
  - 发送邮件（如果启用）
         ↓
任务完成：Mac 自动重新睡眠 💤
```

### 功耗影响

- **每天额外耗电**：约 0.2-0.5%
- **3 天合盖**：从剩余 50% → 剩余 48-49%
- **影响**：几乎可以忽略不计 ✅

### 注意事项

⚠️ **需要网络连接**：
- Mac 睡眠时 WiFi 可能断开
- 建议设置：系统设置 → 电池 → 选项 → 取消勾选"电池供电时，启用节能模式"

⚠️ **需要有电**：
- 如果电池耗尽，任务会停止
- 建议：长期使用时接通电源

---

## 🐛 故障排查

### 问题 1：任务没有执行

```bash
# 1. 检查服务状态
./launchd_setup.sh status

# 2. 查看错误日志
cat logs/launchd_stderr.log

# 3. 手动测试执行
python main.py

# 4. 检查 Python 路径
which python3
# 应该是：/opt/anaconda3/bin/python3
```

### 问题 2：找不到 .env 文件

launchd 不会自动加载 shell 环境变量，需要确保：
- `.env` 文件在项目根目录
- `main.py` 使用 `python-dotenv` 加载环境变量（已实现 ✅）

### 问题 3：网络连接失败

```bash
# 检查 Mac 睡眠时是否保持网络连接
# 系统设置 → 电池 → 选项
# 取消勾选"电池供电时，启用节能模式"
```

---

## 🔧 高级配置

### 只在接通电源时执行

编辑 plist 文件，添加：

```xml
<key>StartOnMount</key>
<false/>

<key>RequiresNetwork</key>
<true/>
```

### 设置重试机制

如果任务失败自动重试：

```xml
<key>KeepAlive</key>
<dict>
    <key>SuccessfulExit</key>
    <false/>
</dict>

<key>ThrottleInterval</key>
<integer>300</integer>  <!-- 失败后 5 分钟重试 -->
```

---

## 🗑️ 完全卸载

```bash
# 1. 停止服务
./launchd_setup.sh stop

# 2. 删除配置文件
rm ~/Library/LaunchAgents/com.crypto.daily.analysis.plist

# 3. 删除日志（可选）
rm -rf logs/
```

---

## 📚 参考资料

- [launchd 官方文档](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html)
- [launchd.plist 手册](https://www.launchd.info/)

---

## ⚠️ 注意事项

1. **不要在 plist 文件中包含敏感信息**（API Key 等）
2. **定期检查日志**，确保任务正常执行
3. **如果长时间不用**，建议停止定时任务以节省电量
4. **系统更新后**，可能需要重新加载服务

---

## 🌍 Language

- [中文指南](LAUNCHD_GUIDE.md)
- For English users: This guide explains how to set up automated daily cryptocurrency analysis using macOS launchd. The system will wake your Mac from sleep at 08:00 daily, run the analysis (30-60 seconds), and go back to sleep. Power consumption impact is minimal (~0.2-0.5% per day).
