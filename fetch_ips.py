import os
import re
import requests
import glob      # 新增：用于查找文件
import zipfile   # 新增：用于生成压缩包
from datetime import datetime, timezone, timedelta

def archive_last_month_files(tz):
    """每月1号自动打包上个月的提取文件为 ZIP，并删除原 TXT 文件"""
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
        zip_name = f"IP{month_prefix}.zip"             # 命名规则：IP加上年月
        
        # 如果检测到 ZIP 已存在，说明今天已经打包过了，直接跳过
        if os.path.exists(zip_name):
            return
            
        # 查找上个月的格式为 YYYY-MM-DD.txt 的所有文件
        target_files = glob.glob(f"{month_prefix}-*.txt")
        
        if target_files:
            print(f"检测到今天是 1 号，开始将上个月 ({month_prefix}) 的 {len(target_files)} 个 IP 文件打包...")
            
            # 1. 写入 ZIP 压缩包
            with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in target_files:
                    zipf.write(file_path)
                    
            # 2. 删除原 TXT 文件
            for file_path in target_files:
                os.remove(file_path)
                
            print(f"归档完成！已生成压缩包: {zip_name}，并清空了旧 TXT 文件。")

def main():
    # 获取东八区（北京时间）的当前日期
    tz = timezone(timedelta(hours=8))
    
    # 在抓取今天的新 IP 前，先执行每月的归档检查
    archive_last_month_files(tz)
    
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
