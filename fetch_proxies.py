import os
import re
import base64
import requests
from datetime import datetime, timezone, timedelta

def decode_base64(data):
    """尝试解密 base64 字符串"""
    try:
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
    filename = f"proxies_{current_date}.txt"

    base_urls = [
        "https://raw.githubusercontent.com/Vanic24/VPN/main/8EB",
        "https://raw.githubusercontent.com/Vanic24/VPN/main/9PB",
        "https://raw.githubusercontent.com/Vanic24/VPN/main/Filter",
        "https://raw.githubusercontent.com/Vanic24/VPN/main/Lifetime",
        "https://raw.githubusercontent.com/Vanic24/VPN/main/MIX",
        "https://raw.githubusercontent.com/Vanic24/VPN/main/Sub3"
    ]
    
    # 规则1：匹配传统的 URI 格式 (例如 vmess://..., vless://...)
    uri_pattern = re.compile(r'(?i)(?:vmess|vless|trojan|ss|ssr|hysteria2?|tuic)://[^\s\'"<>]+')
    
    # 规则2：匹配 Clash 的 YAML 字典格式 (例如 - {name: "...", type: "vless", ...})
    # 这个正则会把 - { ... } 这一整行提取出来
    clash_pattern = re.compile(r'-\s*\{.*?type:\s*["\']?(?:vmess|vless|trojan|ss|ssr|hysteria2?|tuic|http|socks5)["\']?.*?\}', re.IGNORECASE)
    
    new_proxies = set()
    
    for url in base_urls:
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 404:
                url = url.replace("/main/", "/master/")
                resp = requests.get(url, timeout=15)
                
            if resp.status_code == 200:
                text = resp.text
                
                # 1. 提取 URI 格式节点
                uris = uri_pattern.findall(text)
                new_proxies.update(uris)
                
                # 2. 提取 Clash 格式节点
                clash_nodes = clash_pattern.findall(text)
                # 清理一下 Clash 节点前后的空格和多余字符，保持格式整洁
                clash_nodes = [node.strip() for node in clash_nodes]
                new_proxies.update(clash_nodes)
                
                # 3. 如果明文既没有 URI 也没有 Clash 格式，尝试 Base64 解码
                if not uris and not clash_nodes:
                    decoded_text = decode_base64(text.strip())
                    if decoded_text:
                        new_proxies.update(uri_pattern.findall(decoded_text))
                        
        except Exception as e:
            print(f"获取 {url} 失败: {e}")

    print(f"本次从目标仓库提取到 {len(new_proxies)} 个代理节点。")

    # 读取本地历史记录进行去重
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
