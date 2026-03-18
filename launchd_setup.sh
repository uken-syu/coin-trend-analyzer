#!/bin/bash
# launchd 定时任务管理脚本

PLIST_PATH="$HOME/Library/LaunchAgents/com.crypto.daily.analysis.plist"
SERVICE_NAME="com.crypto.daily.analysis"

case "$1" in
    start)
        echo "🚀 启动 launchd 定时任务..."
        launchctl load "$PLIST_PATH"
        echo "✅ 定时任务已启动（每天 08:00 自动执行）"
        echo "📋 查看状态: ./launchd_setup.sh status"
        ;;

    stop)
        echo "⏹️  停止 launchd 定时任务..."
        launchctl unload "$PLIST_PATH"
        echo "✅ 定时任务已停止"
        ;;

    restart)
        echo "🔄 重启 launchd 定时任务..."
        launchctl unload "$PLIST_PATH" 2>/dev/null
        launchctl load "$PLIST_PATH"
        echo "✅ 定时任务已重启"
        ;;

    status)
        echo "📊 launchd 定时任务状态："
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        if launchctl list | grep -q "$SERVICE_NAME"; then
            echo "✅ 状态: 运行中"
            launchctl list | grep "$SERVICE_NAME"
        else
            echo "❌ 状态: 未运行"
        fi
        echo ""
        echo "📝 配置文件: $PLIST_PATH"
        echo "📂 日志目录: $(pwd)/logs/"
        echo ""
        echo "📋 最近的日志："
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        if [ -f "logs/launchd_stdout.log" ]; then
            echo "📄 标准输出 (最后 10 行):"
            tail -10 logs/launchd_stdout.log
        else
            echo "📄 标准输出: 暂无日志"
        fi
        echo ""
        if [ -f "logs/launchd_stderr.log" ]; then
            echo "⚠️  错误输出 (最后 10 行):"
            tail -10 logs/launchd_stderr.log
        else
            echo "⚠️  错误输出: 暂无日志"
        fi
        ;;

    logs)
        echo "📋 查看实时日志（Ctrl+C 退出）："
        tail -f logs/launchd_stdout.log
        ;;

    test)
        echo "🧪 立即测试执行一次..."
        launchctl start "$SERVICE_NAME"
        echo "✅ 测试任务已触发，请查看日志："
        echo "   tail -f logs/launchd_stdout.log"
        ;;

    *)
        echo "🪙 加密货币分析 - launchd 定时任务管理"
        echo ""
        echo "用法: $0 {start|stop|restart|status|logs|test}"
        echo ""
        echo "命令说明："
        echo "  start   - 启动定时任务（每天 08:00 自动执行）"
        echo "  stop    - 停止定时任务"
        echo "  restart - 重启定时任务"
        echo "  status  - 查看运行状态和最近日志"
        echo "  logs    - 实时查看日志输出"
        echo "  test    - 立即执行一次测试"
        echo ""
        echo "示例："
        echo "  $0 start    # 启动定时任务"
        echo "  $0 status   # 查看状态"
        echo "  $0 test     # 测试执行"
        exit 1
        ;;
esac
