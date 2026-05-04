import os
import re
import requests
from datetime import datetime, timezone, timedelta

def main():
    # 获取东八区（北京时间）的当前日期，格式为 YYYY-MM-DD
    tz = timezone(timedelta(hours=8))
    current_date = datetime.now(tz).strftime("%Y-%m-%d")
    filename = f"{current_date}.txt"

    # 目标URL
    url = "https://api.uouin.com/cloudflare.html"
    
    # 设置请求头，模拟浏览器访问，防止被拦截
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        text_content = response.text
    except Exception as e:
        print(f"获取网页失败: {e}")
        return

    # 使用正则表达式提取所有的 IPv4 地址
    # 正则规则：提取类似 1.1.1.1 格式的合法/完整 IP 字符串
    ip_pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    new_ips = set(re.findall(ip_pattern, text_content))
    print(f"网页中提取到 {len(new_ips)} 个 IP。")

    existing_ips = set()
    
    # 如果当天的 txt 文件已经存在，读取里面的历史 IP 用于去重
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                ip = line.strip()
                if ip:
                    existing_ips.add(ip)

    # 将新获取的 IP 与已存在的 IP 合并去重
    all_ips = existing_ips.union(new_ips)

    # 将去重后的所有 IP 写回文件（覆盖写入，并进行排序以便查阅）
    with open(filename, "w", encoding="utf-8") as f:
        for ip in sorted(all_ips):
            f.write(ip + "\n")
            
    print(f"更新完成: {filename}。当前共存储去重后 IP: {len(all_ips)} 个。")

if __name__ == "__main__":
    main()
