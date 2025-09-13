"""
Nginx日志分析 - 简化版本
专门统计：
1. HTTPS请求中domain1.com的数量
2. 指定日期的HTTP成功请求比例

示例日志格式：
47.29.201.179 - - [28/Feb/2019:13:17:10 +0000] "GET /?p=1 HTTP/2.0" 200 5316 "https://domain1.com/?p=1" "Mozilla/5.0 ..." "2.75"
"""

import re
from datetime import datetime
from typing import Tuple
from collections import defaultdict


def analyze_nginx_logs(log_file_path: str, target_date: str = None) -> Tuple[int, float]:
    """
    分析Nginx日志文件
    
    Args:
        log_file_path: 日志文件路径
        target_date: 目标日期，格式为'YYYY-MM-DD' (UTC时间)，如果为None则计算所有日期
    
    Returns:
        (domain1.com的HTTPS请求数量, 指定日期的成功率百分比)
    """
    
    # 编译正则表达式，用于解析日志行
    log_pattern = re.compile(
        r'(\d+\.\d+\.\d+\.\d+) - - \[([^\]]+)\] "([^"]*)" (\d+) (\d+|-) "([^"]*)" "([^"]*)" "([^"]*)"'
    )
    
    # 统计变量
    https_domain1_count = 0
    daily_stats = defaultdict(lambda: {'total': 0, 'success': 0})
    
    # 成功状态码 (2xx)
    success_codes = set(range(200, 300))
    
    print(f"开始分析日志文件: {log_file_path}")
    
    try:
        with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as file:
            line_count = 0
            
            for line in file:
                line_count += 1
                
                # 每处理10万行显示一次进度
                if line_count % 100000 == 0:
                    print(f"已处理 {line_count:,} 行...")
                
                # 解析日志行
                match = log_pattern.match(line.strip())
                if not match:
                    continue
                
                try:
                    ip, timestamp_str, request, status_code, size, referer, user_agent, response_time = match.groups()
                    
                    # 1. 统计HTTPS domain1.com请求
                    if referer.startswith('https://domain1.com'):
                        https_domain1_count += 1
                    
                    # 2. 统计每日成功率
                    # 解析时间戳
                    timestamp = datetime.strptime(timestamp_str, '%d/%b/%Y:%H:%M:%S %z')
                    
                    # 转换为UTC日期
                    utc_date = timestamp.utctimetuple()
                    date_key = f"{utc_date.tm_year:04d}-{utc_date.tm_mon:02d}-{utc_date.tm_mday:02d}"
                    
                    # 更新统计
                    daily_stats[date_key]['total'] += 1
                    
                    status = int(status_code)
                    if status in success_codes:
                        daily_stats[date_key]['success'] += 1
                
                except (ValueError, IndexError):
                    # 跳过无法解析的行
                    continue
            
            print(f"完成！总共处理了 {line_count:,} 行")
    
    except FileNotFoundError:
        print(f"错误: 找不到文件 {log_file_path}")
        return 0, 0.0
    
    except Exception as e:
        print(f"处理文件时出错: {e}")
        return 0, 0.0
    
    # 计算指定日期的成功率
    success_rate = 0.0
    if target_date and target_date in daily_stats:
        stats = daily_stats[target_date]
        if stats['total'] > 0:
            success_rate = (stats['success'] / stats['total']) * 100
    elif target_date:
        print(f"警告: 在日期 {target_date} 没有找到任何请求记录")
    
    return https_domain1_count, success_rate


def print_detailed_statistics(log_file_path: str):
    """
    打印详细的统计信息
    
    Args:
        log_file_path: 日志文件路径
    """
    
    # 编译正则表达式
    log_pattern = re.compile(
        r'(\d+\.\d+\.\d+\.\d+) - - \[([^\]]+)\] "([^"]*)" (\d+) (\d+|-) "([^"]*)" "([^"]*)" "([^"]*)"'
    )
    
    # 统计变量
    https_domain1_count = 0
    daily_stats = defaultdict(lambda: {'total': 0, 'success': 0})
    status_code_stats = defaultdict(int)
    
    success_codes = set(range(200, 300))
    
    print(f"正在分析日志文件: {log_file_path}")
    
    try:
        with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as file:
            line_count = 0
            valid_lines = 0
            
            for line in file:
                line_count += 1
                
                if line_count % 100000 == 0:
                    print(f"已处理 {line_count:,} 行...")
                
                match = log_pattern.match(line.strip())
                if not match:
                    continue
                
                valid_lines += 1
                
                try:
                    ip, timestamp_str, request, status_code, size, referer, user_agent, response_time = match.groups()
                    
                    # 统计HTTPS domain1.com请求
                    if referer.startswith('https://domain1.com'):
                        https_domain1_count += 1
                    
                    # 解析时间戳并统计每日数据
                    timestamp = datetime.strptime(timestamp_str, '%d/%b/%Y:%H:%M:%S %z')
                    utc_date = timestamp.utctimetuple()
                    date_key = f"{utc_date.tm_year:04d}-{utc_date.tm_mon:02d}-{utc_date.tm_mday:02d}"
                    
                    daily_stats[date_key]['total'] += 1
                    
                    status = int(status_code)
                    status_code_stats[status] += 1
                    
                    if status in success_codes:
                        daily_stats[date_key]['success'] += 1
                
                except (ValueError, IndexError):
                    continue
    
    except Exception as e:
        print(f"处理文件时出错: {e}")
        return
    
    print(f"\n{'='*60}")
    print("详细统计结果")
    print(f"{'='*60}")
    
    print(f"\n基本信息:")
    print(f"  总行数: {line_count:,}")
    print(f"  有效日志行数: {valid_lines:,}")
    print(f"  解析成功率: {(valid_lines/line_count*100):.2f}%")
    
    print(f"\n1. HTTPS domain1.com 请求统计:")
    print(f"  请求数量: {https_domain1_count:,}")
    
    print(f"\n2. 每日请求成功率统计 (UTC时间):")
    if daily_stats:
        print(f"  {'日期':<12} {'总请求':<10} {'成功请求':<10} {'成功率':<8}")
        print(f"  {'-'*42}")
        
        total_all = 0
        success_all = 0
        
        for date in sorted(daily_stats.keys()):
            stats = daily_stats[date]
            total = stats['total']
            success = stats['success']
            rate = (success / total * 100) if total > 0 else 0
            
            print(f"  {date:<12} {total:<10,} {success:<10,} {rate:<7.2f}%")
            
            total_all += total
            success_all += success
        
        overall_rate = (success_all / total_all * 100) if total_all > 0 else 0
        print(f"  {'-'*42}")
        print(f"  {'总计':<12} {total_all:<10,} {success_all:<10,} {overall_rate:<7.2f}%")
    
    print(f"\n3. HTTP状态码分布:")
    if status_code_stats:
        sorted_codes = sorted(status_code_stats.items())
        for code, count in sorted_codes:
            percentage = (count / valid_lines * 100) if valid_lines > 0 else 0
            print(f"  {code}: {count:,} ({percentage:.2f}%)")


def quick_analysis(log_file_path: str, date: str = None):
    """
    快速分析函数 - 针对题目要求的两个指标
    
    Args:
        log_file_path: 日志文件路径
        date: 目标日期 (格式: YYYY-MM-DD)
    """
    https_count, success_rate = analyze_nginx_logs(log_file_path, date)
    
    print(f"\n{'='*50}")
    print("Nginx日志分析结果")
    print(f"{'='*50}")
    
    print(f"\n1. HTTPS请求统计:")
    print(f"   domain1.com的HTTPS请求数量: {https_count:,}")
    
    if date:
        print(f"\n2. 指定日期 ({date}) 成功率统计:")
        if success_rate > 0:
            print(f"   成功率: {success_rate:.2f}%")
        else:
            print(f"   在指定日期没有找到数据")
    else:
        print(f"\n2. 如需查看特定日期的成功率，请提供日期参数")


# 示例使用
if __name__ == "__main__":
    import sys
    
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python simple_nginx_analyzer.py <日志文件路径> [日期(YYYY-MM-DD)]")
        print("\n示例:")
        print("  python simple_nginx_analyzer.py nginx.log")
        print("  python simple_nginx_analyzer.py nginx.log 2019-02-28")
        
        # 创建示例文件进行演示
        print("\n正在创建示例日志文件...")
        sample_logs = [
            '47.29.201.179 - - [28/Feb/2019:13:17:10 +0000] "GET /?p=1 HTTP/2.0" 200 5316 "https://domain1.com/?p=1" "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36" "2.75"',
            '192.168.1.100 - - [28/Feb/2019:13:18:15 +0000] "POST /api/login HTTP/1.1" 200 1234 "https://domain1.com/login" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" "1.23"',
            '10.0.0.50 - - [28/Feb/2019:13:19:20 +0000] "GET /images/logo.png HTTP/1.1" 404 0 "http://domain2.com/" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36" "0.45"',
            '203.0.113.45 - - [01/Mar/2019:09:30:45 +0000] "GET /admin/dashboard HTTP/1.1" 500 2048 "https://domain1.com/admin" "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:65.0) Gecko/20100101 Firefox/65.0" "5.67"',
            '198.51.100.25 - - [01/Mar/2019:14:22:33 +0000] "GET /api/users HTTP/2.0" 200 8192 "https://domain1.com/api" "curl/7.58.0" "0.89"',
            '172.16.0.10 - - [02/Mar/2019:08:15:12 +0000] "PUT /api/profile HTTP/1.1" 201 512 "https://domain1.com/profile" "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" "1.45"',
            '47.29.201.180 - - [28/Feb/2019:14:20:30 +0000] "GET /search HTTP/1.1" 200 2048 "http://google.com/" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" "1.15"',
            '47.29.201.181 - - [28/Feb/2019:15:25:45 +0000] "POST /contact HTTP/1.1" 500 1024 "https://domain1.com/contact" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" "2.45"'
        ]
        
        with open('sample_nginx.log', 'w', encoding='utf-8') as f:
            for log in sample_logs:
                f.write(log + '\n')
        
        print("示例文件已创建: sample_nginx.log")
        print("运行示例分析...")
        
        # 分析示例文件
        quick_analysis('sample_nginx.log', '2019-02-28')
        print_detailed_statistics('sample_nginx.log')
        
    else:
        log_file = sys.argv[1]
        target_date = sys.argv[2] if len(sys.argv) > 2 else None
        
        # 快速分析
        quick_analysis(log_file, target_date)
        
        # 详细统计
        print("\n" + "="*50)
        print("详细统计信息")
        print("="*50)
        print_detailed_statistics(log_file)
