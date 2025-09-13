"""
Nginx日志分析工具
分析大型Nginx日志文件，统计HTTPS请求和成功率指标

日志格式说明：
IP地址 - - [时间戳] "请求方法 URL HTTP版本" 状态码 响应大小 "Referer" "User-Agent" "响应时间"

示例日志：
47.29.201.179 - - [28/Feb/2019:13:17:10 +0000] "GET /?p=1 HTTP/2.0" 200 5316 "https://domain1.com/?p=1" "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36" "2.75"
"""

import re
import sys
from datetime import datetime
from typing import Dict, Tuple, Optional
import argparse
from collections import defaultdict
import time


class NginxLogAnalyzer:
    """Nginx日志分析器"""
    
    def __init__(self):
        # 编译正则表达式，提高性能
        self.log_pattern = re.compile(
            r'(\d+\.\d+\.\d+\.\d+) - - \[([^\]]+)\] "([^"]*)" (\d+) (\d+|-) "([^"]*)" "([^"]*)" "([^"]*)"'
        )
        
        # HTTP成功状态码范围 (2xx)
        self.success_status_codes = set(range(200, 300))
        
        # 统计计数器
        self.https_domain1_count = 0
        self.daily_stats = defaultdict(lambda: {'total': 0, 'success': 0})
        
    def parse_log_line(self, line: str) -> Optional[Dict]:
        """
        解析单行日志
        
        Args:
            line: 日志行
            
        Returns:
            解析后的日志字典，如果解析失败返回None
        """
        match = self.log_pattern.match(line.strip())
        if not match:
            return None
            
        try:
            ip, timestamp_str, request, status_code, size, referer, user_agent, response_time = match.groups()
            
            # 解析时间戳
            timestamp = datetime.strptime(timestamp_str, '%d/%b/%Y:%H:%M:%S %z')
            
            # 解析请求
            request_parts = request.split(' ', 2)
            method = request_parts[0] if len(request_parts) > 0 else ''
            url = request_parts[1] if len(request_parts) > 1 else ''
            protocol = request_parts[2] if len(request_parts) > 2 else ''
            
            return {
                'ip': ip,
                'timestamp': timestamp,
                'method': method,
                'url': url,
                'protocol': protocol,
                'status_code': int(status_code),
                'size': int(size) if size != '-' else 0,
                'referer': referer,
                'user_agent': user_agent,
                'response_time': float(response_time) if response_time != '-' else 0.0
            }
        except (ValueError, IndexError) as e:
            print(f"解析日志行时出错: {e}")
            print(f"问题行: {line[:100]}...")
            return None
    
    def is_https_domain1_request(self, log_entry: Dict) -> bool:
        """
        检查是否为HTTPS domain1.com请求
        
        Args:
            log_entry: 解析后的日志条目
            
        Returns:
            如果是HTTPS domain1.com请求返回True
        """
        referer = log_entry.get('referer', '')
        
        # 检查referer是否以https://domain1.com开头
        return referer.startswith('https://domain1.com')
    
    def get_date_key(self, timestamp: datetime) -> str:
        """
        获取日期键 (UTC日期)
        
        Args:
            timestamp: 时间戳
            
        Returns:
            格式为YYYY-MM-DD的日期字符串
        """
        # 转换为UTC时间并格式化为日期
        utc_time = timestamp.utctimetuple()
        return f"{utc_time.tm_year:04d}-{utc_time.tm_mon:02d}-{utc_time.tm_mday:02d}"
    
    def is_success_status(self, status_code: int) -> bool:
        """
        检查是否为成功状态码
        
        Args:
            status_code: HTTP状态码
            
        Returns:
            如果是成功状态码(2xx)返回True
        """
        return status_code in self.success_status_codes
    
    def process_log_file(self, file_path: str, chunk_size: int = 10000) -> None:
        """
        处理日志文件
        
        Args:
            file_path: 日志文件路径
            chunk_size: 每次处理的行数
        """
        print(f"开始处理日志文件: {file_path}")
        print(f"处理块大小: {chunk_size} 行")
        
        total_lines = 0
        processed_lines = 0
        start_time = time.time()
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                batch_lines = []
                
                for line in file:
                    total_lines += 1
                    batch_lines.append(line)
                    
                    # 当达到批处理大小时处理这批数据
                    if len(batch_lines) >= chunk_size:
                        processed_lines += self._process_batch(batch_lines)
                        batch_lines = []
                        
                        # 显示进度
                        if total_lines % (chunk_size * 10) == 0:
                            elapsed = time.time() - start_time
                            speed = total_lines / elapsed if elapsed > 0 else 0
                            print(f"已处理 {total_lines:,} 行，成功解析 {processed_lines:,} 行，"
                                  f"处理速度: {speed:.0f} 行/秒")
                
                # 处理剩余的行
                if batch_lines:
                    processed_lines += self._process_batch(batch_lines)
        
        except FileNotFoundError:
            print(f"错误: 找不到文件 {file_path}")
            return
        except Exception as e:
            print(f"处理文件时出错: {e}")
            return
        
        elapsed = time.time() - start_time
        print(f"\n处理完成!")
        print(f"总计处理 {total_lines:,} 行，成功解析 {processed_lines:,} 行")
        print(f"总耗时: {elapsed:.2f} 秒")
        print(f"平均速度: {total_lines/elapsed:.0f} 行/秒")
    
    def _process_batch(self, lines: list) -> int:
        """
        处理一批日志行
        
        Args:
            lines: 日志行列表
            
        Returns:
            成功处理的行数
        """
        processed_count = 0
        
        for line in lines:
            log_entry = self.parse_log_line(line)
            if log_entry is None:
                continue
                
            processed_count += 1
            
            # 统计HTTPS domain1.com请求
            if self.is_https_domain1_request(log_entry):
                self.https_domain1_count += 1
            
            # 统计每日成功率
            date_key = self.get_date_key(log_entry['timestamp'])
            self.daily_stats[date_key]['total'] += 1
            
            if self.is_success_status(log_entry['status_code']):
                self.daily_stats[date_key]['success'] += 1
        
        return processed_count
    
    def get_https_domain1_count(self) -> int:
        """
        获取HTTPS domain1.com请求数量
        
        Returns:
            HTTPS domain1.com请求的总数
        """
        return self.https_domain1_count
    
    def get_daily_success_rate(self, date: str) -> Tuple[float, int, int]:
        """
        获取指定日期的成功率
        
        Args:
            date: 日期字符串，格式为YYYY-MM-DD
            
        Returns:
            (成功率, 成功请求数, 总请求数)
        """
        if date not in self.daily_stats:
            return 0.0, 0, 0
        
        stats = self.daily_stats[date]
        total = stats['total']
        success = stats['success']
        
        success_rate = (success / total * 100) if total > 0 else 0.0
        
        return success_rate, success, total
    
    def get_all_dates_summary(self) -> Dict:
        """
        获取所有日期的汇总统计
        
        Returns:
            包含所有日期统计信息的字典
        """
        summary = {}
        
        for date, stats in sorted(self.daily_stats.items()):
            total = stats['total']
            success = stats['success']
            success_rate = (success / total * 100) if total > 0 else 0.0
            
            summary[date] = {
                'total_requests': total,
                'successful_requests': success,
                'success_rate': round(success_rate, 2)
            }
        
        return summary
    
    def print_statistics(self) -> None:
        """打印统计结果"""
        print("\n" + "="*60)
        print("Nginx日志分析结果")
        print("="*60)
        
        # HTTPS domain1.com统计
        print(f"\n1. HTTPS请求统计:")
        print(f"   domain1.com的HTTPS请求数量: {self.https_domain1_count:,}")
        
        # 每日成功率统计
        print(f"\n2. 每日请求成功率统计 (UTC时间):")
        if not self.daily_stats:
            print("   没有找到有效的日志数据")
            return
        
        print(f"   {'日期':<12} {'总请求数':<10} {'成功请求数':<10} {'成功率':<8}")
        print("   " + "-"*45)
        
        total_requests = 0
        total_success = 0
        
        for date in sorted(self.daily_stats.keys()):
            success_rate, success, total = self.get_daily_success_rate(date)
            print(f"   {date:<12} {total:<10,} {success:<10,} {success_rate:<7.2f}%")
            
            total_requests += total
            total_success += success
        
        # 总体统计
        overall_success_rate = (total_success / total_requests * 100) if total_requests > 0 else 0.0
        print("   " + "-"*45)
        print(f"   {'总计':<12} {total_requests:<10,} {total_success:<10,} {overall_success_rate:<7.2f}%")


def create_sample_log_file(file_path: str, num_lines: int = 1000) -> None:
    """
    创建示例日志文件用于测试
    
    Args:
        file_path: 文件路径
        num_lines: 生成的日志行数
    """
    import random
    
    sample_logs = [
        '47.29.201.179 - - [28/Feb/2019:13:17:10 +0000] "GET /?p=1 HTTP/2.0" 200 5316 "https://domain1.com/?p=1" "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36" "2.75"',
        '192.168.1.100 - - [28/Feb/2019:13:18:15 +0000] "POST /api/login HTTP/1.1" 200 1234 "https://domain1.com/login" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" "1.23"',
        '10.0.0.50 - - [28/Feb/2019:13:19:20 +0000] "GET /images/logo.png HTTP/1.1" 404 0 "http://domain2.com/" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36" "0.45"',
        '203.0.113.45 - - [01/Mar/2019:09:30:45 +0000] "GET /admin/dashboard HTTP/1.1" 500 2048 "https://domain1.com/admin" "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:65.0) Gecko/20100101 Firefox/65.0" "5.67"',
        '198.51.100.25 - - [01/Mar/2019:14:22:33 +0000] "GET /api/users HTTP/2.0" 200 8192 "https://api.domain1.com/" "curl/7.58.0" "0.89"',
        '172.16.0.10 - - [02/Mar/2019:08:15:12 +0000] "PUT /api/profile HTTP/1.1" 201 512 "https://domain1.com/profile" "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" "1.45"'
    ]
    
    ips = ['47.29.201.179', '192.168.1.100', '10.0.0.50', '203.0.113.45', '198.51.100.25', '172.16.0.10']
    methods = ['GET', 'POST', 'PUT', 'DELETE']
    urls = ['/', '/api/login', '/images/logo.png', '/admin/dashboard', '/api/users', '/profile']
    status_codes = [200, 201, 404, 500, 302, 403]
    referers = [
        'https://domain1.com/',
        'https://domain1.com/login', 
        'http://domain2.com/',
        'https://domain1.com/admin',
        'https://api.domain1.com/',
        'https://domain1.com/profile',
        '-'
    ]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        for i in range(num_lines):
            # 选择基础模板并进行随机化
            if i < len(sample_logs):
                f.write(sample_logs[i] + '\n')
            else:
                # 生成随机日志
                ip = random.choice(ips)
                day = random.randint(28, 31)
                month = random.choice(['Feb', 'Mar'])
                hour = random.randint(0, 23)
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                method = random.choice(methods)
                url = random.choice(urls)
                status = random.choice(status_codes)
                size = random.randint(100, 10000)
                referer = random.choice(referers)
                response_time = round(random.uniform(0.1, 10.0), 2)
                
                log_line = f'{ip} - - [{day:02d}/{month}/2019:{hour:02d}:{minute:02d}:{second:02d} +0000] "{method} {url} HTTP/1.1" {status} {size} "{referer}" "Mozilla/5.0 (Test)" "{response_time}"'
                f.write(log_line + '\n')
    
    print(f"创建了包含 {num_lines} 行的示例日志文件: {file_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Nginx日志分析工具')
    parser.add_argument('log_file', nargs='?', help='Nginx日志文件路径')
    parser.add_argument('-d', '--date', help='查询指定日期的成功率 (格式: YYYY-MM-DD)')
    parser.add_argument('-c', '--create-sample', type=int, metavar='N', 
                       help='创建包含N行的示例日志文件')
    parser.add_argument('--chunk-size', type=int, default=10000,
                       help='批处理大小 (默认: 10000)')
    
    args = parser.parse_args()
    
    # 如果指定了创建示例文件
    if args.create_sample:
        sample_file = 'nginx_sample.log'
        create_sample_log_file(sample_file, args.create_sample)
        if not args.log_file:
            args.log_file = sample_file
    
    # 检查是否提供了日志文件
    if not args.log_file:
        print("请提供日志文件路径，或使用 -c 选项创建示例文件")
        print("使用 -h 查看帮助信息")
        return
    
    # 创建分析器并处理日志
    analyzer = NginxLogAnalyzer()
    analyzer.process_log_file(args.log_file, args.chunk_size)
    
    # 打印统计结果
    analyzer.print_statistics()
    
    # 如果指定了特定日期，显示该日期的详细信息
    if args.date:
        print(f"\n特定日期查询结果 ({args.date}):")
        success_rate, success, total = analyzer.get_daily_success_rate(args.date)
        if total > 0:
            print(f"  总请求数: {total:,}")
            print(f"  成功请求数: {success:,}")
            print(f"  成功率: {success_rate:.2f}%")
        else:
            print(f"  在日期 {args.date} 没有找到任何请求记录")


if __name__ == "__main__":
    main()
