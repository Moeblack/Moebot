import subprocess
import os
import sys
import signal
import atexit
from ncatbot.core import BotClient
from bot_agent.handlers import register_handlers

# 全局变量存储监控进程
monitor_process = None

def stop_monitor():
    """停止监控后台进程"""
    global monitor_process
    if monitor_process and monitor_process.poll() is None:
        print("\n[System] 正在停止监控网页后台...")
        monitor_process.terminate()
        try:
            monitor_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print("[System] 监控后台未能在时间内停止，正在强制结束...")
            monitor_process.kill()
        print("[System] 监控网页后台已停止。")
        monitor_process = None

def start_monitor():
    """在后台启动监控网页后台"""
    global monitor_process
    monitor_path = os.path.join("scripts", "monitor_web.py")
    python_exe = os.path.join(".venv", "bin", "python")
    
    if not os.path.exists(python_exe):
        # 降级处理，如果找不到虚拟环境则尝试使用当前解释器
        python_exe = sys.executable

    print(f"[System] 正在启动监控网页后台: {python_exe} {monitor_path}")
    try:
        # 使用 Popen 启动子进程，移除 start_new_session 以便生命周期管理
        monitor_process = subprocess.Popen(
            [python_exe, monitor_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        # 注册退出钩子
        atexit.register(stop_monitor)
        print("[System] 监控网页后台已启动，监听地址: http://0.0.0.0:8000")
    except Exception as e:
        print(f"[System] 启动监控后台失败: {e}")

def signal_handler(sig, frame):
    """处理终止信号"""
    print(f"\n[System] 收到信号 {sig}，准备退出...")
    stop_monitor()
    sys.exit(0)

def main():
    # 注册信号处理 (SIGINT 和 SIGTERM)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 0. 自动启动监控后台
    start_monitor()

    # 1. 初始化机器人
    bot = BotClient()

    # 2. 注册处理器
    register_handlers(bot)

    # 3. 运行机器人
    print("[System] 机器人正在启动...")
    try:
        bot.run_frontend()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"[System] 机器人运行崩溃: {e}")
    finally:
        stop_monitor()

if __name__ == "__main__":
    main()
