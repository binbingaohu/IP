import os
import re
import base64
import requests
from datetime import datetime, timezone, timedelta

def decode_base64(data):
    """尝试解密 base64 字符串（很多订阅节点是base64编码的）"""
    try:
        # 补齐 padding
        missing_padding = len(data) % 4
        if missing_padding:
            data += '=' * (4 - missing_padding)
        return base64.b64decode(data).decode('utf-8', errors='ignore')
    except Exception:
        return ""

def main():
    # 获取北京时间日期
    tz = timezone(timedelta(hours=8))
    current_date = datetime.now(tz).strftime("%Y-%m-%d")
    # 为了和之前的IP文件区分，这里加上 proxies_ 前缀
    filename = f"proxies_{current_date}.txt"

    # 目标仓库文件的 Raw 地址列表 (根据你截图中的文件名)
    base_urls = [
        "https://raw.githubusercontent.com/Vanic24/VPN/main/8EB",
        "https://raw.githubusercontent.com/Vanic24/VPN/main/9PB",
        "https://raw.githubusercontent.com/Vanic24/VPN/main/Filter",
        "https://raw.githubusercontent.com/Vanic24/VPN/main/Lifetime",
        "https://raw.githubusercontent.com/Vanic24/VPN/main/MIX",
        "https://raw.githubusercontent.com/Vanic24/VPN/main/Sub3"
    ]
    
    # 匹配各类代理节点链接的正则表达式 (支持 vmess, vless, trojan, ss, ssr, hysteria, tuic等)
    proxy_pattern = re.compile(r'(?i)(?:vmess|vless|trojan|ss|ssr|hysteria2?|tuic)://[^\s\'"<>]+')
    
    new_proxies = set()
    
    # 逐个访问文件并提取节点
    for url in base_urls:
        try:
            resp = requests.get(url, timeout=15)
            # 如果 main 分支找不到，尝试 master 分支
            if resp.status_code == 404:
                url = url.replace("/main/", "/master/")
                resp = requests.get(url, timeout=15)
                
            if resp.status_code == 200:
                text = resp.text
                # 1. 尝试直接提取明文链接
                links = proxy_pattern.findall(text)
                new_proxies.update(links)
                
                # 2. 如果没有找到明文链接，说明可能是 Base64 编码的订阅文件，尝试解码后提取
                if not links:
                    decoded_text = decode_base64(text.strip())
                    if decoded_text:
                        new_proxies.update(proxy_pattern.findall(decoded_text))
        except Exception as e:
            print(f"获取 {url} 失败: {e}")

    print(f"本次从目标仓库提取到 {len(new_proxies)} 个代理节点。")

    # 读取本地当天的历史记录进行去重
    existing_proxies = set()
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                node = line.strip()
                if node:
                    existing_proxies.add(node)

    # 合并并去重
    all_proxies = existing_proxies.union(new_proxies)

    # 排序并保存回文件
    with open(filename, "w", encoding="utf-8") as f:
        for node in sorted(all_proxies):
            f.write(node + "\n")
            
    print(f"更新完成: {filename}。当前共存储去重后节点: {len(all_proxies)} 个。")

if __name__ == "__main__":
    main()
