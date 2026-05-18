import os
import re
import json
import base64
import urllib.parse
import requests
import yaml
import glob      # 新增：用于查找匹配的文件
import zipfile   # 新增：用于生成压缩包
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

def clash_to_uri(p):
    """将 Clash 字典格式翻译成 V2ray/Nekobox 支持的 URI 标准链接格式"""
    try:
        ptype = p.get('type')
        name = urllib.parse.quote(p.get('name', 'node'))
        server = p.get('server', '')
        port = p.get('port', '')
        
        if ptype == 'vless':
            uuid = p.get('uuid', '')
            params = {}
            if p.get('network'): params['type'] = p.get('network')
            if str(p.get('tls', '')).lower() == 'true': params['security'] = 'tls'
            if p.get('sni') or p.get('servername'): params['sni'] = p.get('sni') or p.get('servername')
            
            if p.get('network') == 'ws':
                ws_opts = p.get('ws-opts', {})
                if ws_opts.get('path'): params['path'] = urllib.parse.quote(ws_opts.get('path'))
                if ws_opts.get('headers', {}).get('Host'): params['host'] = urllib.parse.quote(ws_opts.get('headers')['Host'])
            
            query = urllib.parse.urlencode(params, safe='=')
            url = f"vless://{uuid}@{server}:{port}"
            return f"{url}?{query}#{name}" if query else f"{url}#{name}"

        elif ptype == 'vmess':
            v_dict = {
                "v": "2", "ps": p.get('name', 'vmess'), "add": server, "port": port,
                "id": p.get('uuid', ''), "aid": p.get('alterId', 0),
                "scy": p.get('cipher', 'auto'), "net": p.get('network', 'tcp'),
                "type": "none", "tls": "tls" if str(p.get('tls', '')).lower() == 'true' else ""
            }
            if p.get('sni') or p.get('servername'): v_dict['sni'] = p.get('sni') or p.get('servername')
            if p.get('network') == 'ws':
                ws_opts = p.get('ws-opts', {})
                v_dict['path'] = ws_opts.get('path', '')
                v_dict['host'] = ws_opts.get('headers', {}).get('Host', '')
            
            b64 = base64.b64encode(json.dumps(v_dict, separators=(',', ':')).encode('utf-8')).decode('utf-8')
            return f"vmess://{b64}"

        elif ptype == 'ss':
            cipher = p.get('cipher', '')
            password = p.get('password', '')
            b64_user_pass = base64.b64encode(f"{cipher}:{password}".encode('utf-8')).decode('utf-8')
            return f"ss://{b64_user_pass}@{server}:{port}#{name}"

        elif ptype == 'trojan':
            password = p.get('password', '')
            params = {}
            if p.get('sni'): params['sni'] = p.get('sni')
            if p.get('network'): params['type'] = p.get('network')
            if p.get('network') == 'ws':
                ws_opts = p.get('ws-opts', {})
                if ws_opts.get('path'): params['path'] = urllib.parse.quote(ws_opts.get('path'))
                if ws_opts.get('headers', {}).get('Host'): params['host'] = urllib.parse.quote(ws_opts.get('headers')['Host'])
            
            query = urllib.parse.urlencode(params, safe='=')
            url = f"trojan://{password}@{server}:{port}"
            return f"{url}?{query}#{name}" if query else f"{url}#{name}"

    except Exception:
        pass
    return None

def archive_last_month_files(tz):
    """每月1号自动打包上个月的文件为 ZIP，并删除原 TXT 文件"""
    now = datetime.now(tz)
    
    # 仅在每月 1 号执行
    if now.day == 1:
        # 计算上个月的年份和月份
        if now.month == 1:
            last_year = now.year - 1
            last_month = 12
        else:
            last_year = now.year
            last_month = now.month - 1
            
        month_prefix = f"{last_year}-{last_month:02d}" # 例如：2023-10
        zip_name = f"{month_prefix}.zip"
        
        # 因为每天会运行多次，如果检测到 ZIP 已存在，说明今天已经打包过了，直接跳过
        if os.path.exists(zip_name):
            return
            
        # 查找上个月的所有明文和订阅 TXT 文件
        target_files = glob.glob(f"*_{month_prefix}-*.txt")
        
        if target_files:
            print(f"检测到今天是 1 号，开始将上个月 ({month_prefix}) 的 {len(target_files)} 个文件打包...")
            
            # 1. 写入 ZIP 压缩包
            with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in target_files:
                    zipf.write(file_path)
                    
            # 2. 删除原 TXT 文件
            for file_path in target_files:
                os.remove(file_path)
                
            print(f"归档完成！已生成压缩包: {zip_name}，并清空了旧 TXT 文件。")

def main():
    tz = timezone(timedelta(hours=8))
    
    # 在抓取新节点前，先执行归档检查
    archive_last_month_files(tz)
    
    current_date = datetime.now(tz).strftime("%Y-%m-%d")
    
    # 将会生成两个文件，一个是明文供复制，一个是 Base64 供作为订阅链接导入
    filename = f"proxies_{current_date}.txt"
    b64_filename = f"sub_{current_date}.txt"

    base_urls = [
        "https://raw.githubusercontent.com/Vanic24/VPN/main/8EB",
        "https://raw.githubusercontent.com/Vanic24/VPN/main/9PB",
        "https://raw.githubusercontent.com/Vanic24/VPN/main/Filter",
        "https://raw.githubusercontent.com/Vanic24/VPN/main/Lifetime",
        "https://raw.githubusercontent.com/Vanic24/VPN/main/MIX",
        "https://raw.githubusercontent.com/Vanic24/VPN/main/Sub3"
    ]
    
    uri_pattern = re.compile(r'(?i)(?:vmess|vless|trojan|ss|ssr|hysteria2?|tuic)://[^\s\'"<>]+')
    new_proxies = set()
    
    for url in base_urls:
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 404:
                url = url.replace("/main/", "/master/")
                resp = requests.get(url, timeout=15)
                
            if resp.status_code == 200:
                text = resp.text
                
                # 1. 尝试直接提取明文 URI
                uris = uri_pattern.findall(text)
                new_proxies.update(uris)
                
                # 2. 核心：通过 YAML 解析 Clash 节点并进行翻译
                try:
                    config = yaml.safe_load(text)
                    if isinstance(config, dict) and 'proxies' in config:
                        for p in config['proxies']:
                            uri = clash_to_uri(p)
                            if uri:
                                new_proxies.add(uri)
                except Exception:
                    pass
                
                # 3. 尝试 Base64 解码提取
                if not uris:
                    decoded_text = decode_base64(text.strip())
                    if decoded_text:
                        new_proxies.update(uri_pattern.findall(decoded_text))
                        
        except Exception as e:
            print(f"获取 {url} 失败: {e}")

    # 读取本地历史记录去重
    existing_proxies = set()
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                node = line.strip()
                if node:
                    existing_proxies.add(node)

    all_proxies = existing_proxies.union(new_proxies)

    # 1. 保存为明文 txt (你可以直接全选复制粘贴进 Nekobox)
    with open(filename, "w", encoding="utf-8") as f:
        for node in sorted(all_proxies):
            f.write(node + "\n")
            
    # 2. 保存为 Base64 订阅 txt
    with open(b64_filename, "w", encoding="utf-8") as f:
        all_text = "\n".join(sorted(all_proxies))
        b64_content = base64.b64encode(all_text.encode('utf-8')).decode('utf-8')
        f.write(b64_content)
            
    print(f"更新完成！生成明文文件: {filename} 和 订阅文件: {b64_filename}。当前节点: {len(all_proxies)} 个。")

if __name__ == "__main__":
    main()
