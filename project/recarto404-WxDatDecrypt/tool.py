from multiprocessing import freeze_support
import os
import json
from pathlib import Path
import datetime

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.theme import Theme
from rich.table import Table

from key import find_key, CONFIG_FILE

# 创建带有自定义主题的控制台
theme = Theme({
    "info": "cyan",
    "success": "green",
    "error": "red bold",
    "warning": "yellow",
    "title": "cyan bold"
})
console = Console(theme=theme)

def load_config() -> dict:
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"xor": 0, "aes": "", "cache": []}

def save_config(config: dict) -> None:
    """保存配置文件"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def display_cached_keys(cache: list) -> None:
    """显示缓存的密钥记录"""
    if not cache:
        console.print("没有缓存的密钥记录", style="info")
        return

    table = Table(title="历史密钥记录", show_header=True, header_style="bold magenta")
    table.add_column("时间", style="cyan")
    table.add_column("XOR密钥", style="green")
    table.add_column("AES密钥", style="yellow")

    for entry in cache:
        table.add_row(
            entry.get("timestamp", "未知"),
            f"0x{entry.get('xor', 0):02X}",
            entry.get("aes", "")[:16]
        )

    console.print(table)

def main():
    """主程序"""
    # 显示欢迎信息
    console.print(Panel.fit(
        "微信数据解密工具",
        title="WxDatDecrypt",
        border_style="cyan"
    ))

    # 加载配置
    config = load_config()
    
    # 显示历史记录
    if config.get("cache"):
        display_cached_keys(config["cache"])
        console.print()

    # 当前密钥
    if config.get("xor") and config.get("aes"):
        console.print("当前密钥:", style="info")
        console.print(f"XOR: 0x{config['xor']:02X}", style="success")
        console.print(f"AES: {config['aes'][:16]}", style="success")
        console.print()

    # 让用户输入自定义路径
    while True:
        path_str = Prompt.ask("请输入微信缓存目录的完整路径")
        custom_path = Path(path_str)
        
        if not custom_path.exists():
            console.print("✗ 目录不存在", style="error")
            if not Confirm.ask("是否重新输入?", default=True):
                return
            continue
            
        if not custom_path.is_dir():
            console.print("✗ 不是有效的目录", style="error")
            if not Confirm.ask("是否重新输入?", default=True):
                return
            continue
        
        weixin_dir = custom_path
        break
    
    console.print(f"✓ 使用目录: {weixin_dir}", style="success")
    console.print()

    # 选择微信版本
    version = int(Prompt.ask(
        "选择微信版本",
        choices=["3", "4"],
        default="4"
    ))

    console.print()
    # 检查当前密钥和历史缓存的密钥
    keys_to_verify = []
    
    if "cache" in config:
        for cache_entry in config["cache"]:
            if cache_entry["xor"] != 0 and cache_entry["aes"]:
                key_pair = (cache_entry["xor"], cache_entry["aes"])
                if key_pair not in keys_to_verify:
                    keys_to_verify.append(key_pair)
    
    if keys_to_verify and Confirm.ask("检测到已缓存的密钥，是否验证?", default=True):
        for xor_key_, aes_key_str in keys_to_verify:
            try:
                console.print(f"\n正在验证密钥 XOR: 0x{xor_key_:02X}, AES: {aes_key_str[:16]}", style="info")
                xor_key, aes_key = find_key(
                    weixin_dir,
                    version=version,
                    xor_key_=xor_key_,
                    aes_key_=aes_key_str.encode()[:16]
                )
                console.print("✓ 密钥验证成功！", style="success")
                # 更新当前密钥为验证成功的密钥
                config["xor"] = xor_key_
                config["aes"] = aes_key_str
                save_config(config)
                return
            except Exception as e:
                console.print(f"✗ 该密钥验证失败: {e}", style="error")
                continue
        
        # 如果所有密钥都验证失败
        if not Confirm.ask("所有缓存密钥验证失败，是否获取新密钥?", default=True):
            return
    
    # 寻找新的密钥
    try:
        console.print("正在寻找新密钥...", style="info")
        xor_key, aes_key = find_key(weixin_dir, version=version)
        
        # 将新密钥添加到缓存
        if aes_key is not None:
            new_cache_entry = {
                "xor": xor_key,
                "aes": aes_key.decode(),
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            if "cache" not in config:
                config["cache"] = []
                
            # 检查是否已存在相同的密钥对
            exists = False
            for entry in config["cache"]:
                if entry["xor"] == xor_key and entry["aes"] == aes_key.decode():
                    exists = True
                    break
            
            if not exists:
                config["cache"].append(new_cache_entry)
                
            # 只保留最近的30个缓存记录
            if len(config["cache"]) > 30:
                config["cache"] = config["cache"][-30:]
        
        # 更新当前密钥
        config["xor"] = xor_key
        if aes_key is not None:
            config["aes"] = aes_key.decode()

            # 保存配置
            save_config(config)
            
            console.print("\n新密钥获取成功！", style="success")
            console.print(f"XOR: 0x{xor_key:02X}", style="success")
            console.print(f"AES: {aes_key.decode()[:16]}", style="success")
            console.print("\n按任意键退出...", style="info")
            os.system("pause > nul")
        else:
            console.print("警告：未获取到 AES 密钥", style="warning")
            console.print("\n按任意键退出...", style="info")
            os.system("pause > nul")
        
    except Exception as e:
        console.print(f"获取密钥失败: {e}", style="error")
        console.print("\n按任意键退出...", style="info")
        os.system("pause > nul")

if __name__ == "__main__":
    freeze_support()
    
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n程序已取消", style="warning")
    except Exception as e:
        console.print(f"发生错误: {e}", style="error")
