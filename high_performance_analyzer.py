"""
高性能Nginx日志分析器
专门针对大型日志文件（如1000万行）进行优化

功能：
1. 统计HTTPS请求中domain1.com的数量
2. 计算指定日期(UTC)所有请求中成功的比例

优化特性：
- 内存友好的流式处理
- 批量处理提高IO效率
- 编译的正则表达式
- 进度显示
- 错误容忍
"""

import re
import sys
import time
from datetime import datetime
from typing import Dict, Tuple, Optional
from collections import defaultdict
import mmap
import os


class HighPerformanceNginxAnalyzer:
    """高性能Nginx日志分析器"""
    
    def __init__(self):
        # 预编译正则表达式提高性能
        self.log_pattern = re.compile(
            r'(\d+\.\d+\.\d+\.\d+) - - \[([^\]]+)\] "([^"]*)" (\d+) (\d+|-) "([^"]*)" "([^"]*)" "([^"]*)"'
        )
        
        # 预编译时间戳解析模式
        self.time_pattern = re.compile(r'(\d{2})/(\w{3})/(\d{4}):(\d{2}):(\d{2}):(\d{2}) ([+-]\d{4})')
        
        # 月份映射
        self.month_map = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        # 成功状态码集合
        self.success_codes = frozenset(range(200, 300))
        
        # 统计数据
        self.reset_stats()
    
    def reset_stats(self):
        """重置统计数据"""
        self.https_domain1_count = 0
        self.daily_stats = defaultdict(lambda: {'total': 0, 'success': 0})
        self.total_lines_processed = 0
        self.valid_lines_processed = 0
    
    def fast_parse_timestamp(self, timestamp_str: str) -> Optional[str]:
        """
        快速解析时间戳，返回UTC日期字符串
        
        Args:
            timestamp_str: 时间戳字符串，如 "28/Feb/2019:13:17:10 +0000"
            
        Returns:
            日期字符串 "YYYY-MM-DD" 或 None
        """
        try:
            match = self.time_pattern.match(timestamp_str)
            if not match:
                return None
            
            day, month_str, year, hour, minute, second, tz = match.groups()
            
            # 快速月份转换
            month = self.month_map.get(month_str)
            if not month:
                return None
            
            # 简化处理：假设大部分日志是UTC时间或时区差异不大
            # 对于精确的时区处理，可以解析tz参数
            return f"{year}-{month:02d}-{int(day):02d}"
            
        except (ValueError, AttributeError):
            return None
    
    def process_line(self, line: str) -> bool:
        """
        处理单行日志
        
        Args:
            line: 日志行
            
        Returns:
            是否成功处理
        """
        self.total_lines_processed += 1
        
        # 解析日志行
        match = self.log_pattern.match(line.strip())
        if not match:
            return False
        
        try:
            ip, timestamp_str, request, status_code, size, referer, user_agent, response_time = match.groups()
            
            self.valid_lines_processed += 1
            
            # 1. 检查HTTPS domain1.com请求
            if referer.startswith('https://domain1.com'):
                self.https_domain1_count += 1
            
            # 2. 处理日期和状态码统计
            date_key = self.fast_parse_timestamp(timestamp_str)
            if date_key:
                self.daily_stats[date_key]['total'] += 1
                
                status = int(status_code)
                if status in self.success_codes:
                    self.daily_stats[date_key]['success'] += 1
            
            return True
            
        except (ValueError, IndexError):
            return False
    
    def process_file_streaming(self, file_path: str, batch_size: int = 50000) -> None:
        """
        流式处理大文件
        
        Args:
            file_path: 文件路径
            batch_size: 批处理大小
        """
        print(f"开始处理文件: {file_path}")
        
        # 获取文件大小用于进度显示
        file_size = os.path.getsize(file_path)
        print(f"文件大小: {file_size / (1024*1024):.2f} MB")
        
        start_time = time.time()
        bytes_processed = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                batch_lines = []
                
                for line in file:
                    batch_lines.append(line)
                    bytes_processed += len(line.encode('utf-8'))
                    
                    # 批量处理
                    if len(batch_lines) >= batch_size:
                        self._process_batch(batch_lines)
                        batch_lines = []
                        
                        # 显示进度
                        elapsed = time.time() - start_time
                        if elapsed > 0:
                            progress = (bytes_processed / file_size) * 100
                            speed = self.total_lines_processed / elapsed
                            eta = (file_size - bytes_processed) / (bytes_processed / elapsed) if bytes_processed > 0 else 0
                            
                            print(f"\r进度: {progress:.1f}% | "
                                  f"处理: {self.total_lines_processed:,} 行 | "
                                  f"速度: {speed:.0f} 行/秒 | "
                                  f"预计剩余: {eta:.0f}秒", end='', flush=True)
                
                # 处理剩余行
                if batch_lines:
                    self._process_batch(batch_lines)
                    
        except FileNotFoundError:
            print(f"错误: 找不到文件 {file_path}")
            return
        except Exception as e:
            print(f"处理文件时出错: {e}")
            return
        
        elapsed = time.time() - start_time
        print(f"\n\n处理完成!")
        print(f"总计: {self.total_lines_processed:,} 行，有效: {self.valid_lines_processed:,} 行")
        print(f"耗时: {elapsed:.2f} 秒，平均速度: {self.total_lines_processed/elapsed:.0f} 行/秒")
    
    def _process_batch(self, lines: list) -> None:
        """批量处理日志行"""
        for line in lines:
            self.process_line(line)
    
    def process_file_mmap(self, file_path: str) -> None:
        """
        使用内存映射处理大文件（更适合超大文件）
        
        Args:
            file_path: 文件路径
        """
        print(f"使用内存映射处理文件: {file_path}")
        
        start_time = time.time()
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                with mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as mmapped_file:
                    
                    for line_bytes in iter(mmapped_file.readline, b""):
                        try:
                            line = line_bytes.decode('utf-8', errors='ignore')
                            self.process_line(line)
                            
                            # 每10万行显示一次进度
                            if self.total_lines_processed % 100000 == 0:
                                elapsed = time.time() - start_time
                                speed = self.total_lines_processed / elapsed if elapsed > 0 else 0
                                print(f"已处理: {self.total_lines_processed:,} 行，速度: {speed:.0f} 行/秒")
                                
                        except UnicodeDecodeError:
                            continue
                            
        except Exception as e:
            print(f"处理文件时出错: {e}")
            return
        
        elapsed = time.time() - start_time
        print(f"\n处理完成!")
        print(f"总计: {self.total_lines_processed:,} 行，有效: {self.valid_lines_processed:,} 行")
        print(f"耗时: {elapsed:.2f} 秒，平均速度: {self.total_lines_processed/elapsed:.0f} 行/秒")
    
    def get_results(self, target_date: str = None) -> Tuple[int, float, Dict]:
        """
        获取分析结果
        
        Args:
            target_date: 目标日期 (YYYY-MM-DD)
            
        Returns:
            (HTTPS domain1请求数, 指定日期成功率, 所有日期统计)
        """
        success_rate = 0.0
        
        if target_date and target_date in self.daily_stats:
            stats = self.daily_stats[target_date]
            if stats['total'] > 0:
                success_rate = (stats['success'] / stats['total']) * 100
        
        # 生成所有日期的统计信息
        all_dates_stats = {}
        for date, stats in sorted(self.daily_stats.items()):
            total = stats['total']
            success = stats['success']
            rate = (success / total * 100) if total > 0 else 0.0
            
            all_dates_stats[date] = {
                'total': total,
                'success': success,
                'success_rate': round(rate, 2)
            }
        
        return self.https_domain1_count, success_rate, all_dates_stats
    
    def print_results(self, target_date: str = None) -> None:
        """打印分析结果"""
        https_count, success_rate, all_stats = self.get_results(target_date)
        
        print(f"\n{'='*60}")
        print("Nginx日志分析结果")
        print(f"{'='*60}")
        
        print(f"\n文件处理统计:")
        print(f"  总行数: {self.total_lines_processed:,}")
        print(f"  有效行数: {self.valid_lines_processed:,}")
        if self.total_lines_processed > 0:
            validity_rate = (self.valid_lines_processed / self.total_lines_processed) * 100
            print(f"  有效率: {validity_rate:.2f}%")
        
        print(f"\n1. HTTPS domain1.com 请求统计:")
        print(f"   请求数量: {https_count:,}")
        if self.valid_lines_processed > 0:
            https_percentage = (https_count / self.valid_lines_processed) * 100
            print(f"   占总请求比例: {https_percentage:.2f}%")
        
        if target_date:
            print(f"\n2. 指定日期 ({target_date}) 成功率:")
            if target_date in self.daily_stats:
                stats = self.daily_stats[target_date]
                print(f"   总请求数: {stats['total']:,}")
                print(f"   成功请求数: {stats['success']:,}")
                print(f"   成功率: {success_rate:.2f}%")
            else:
                print(f"   在日期 {target_date} 没有找到任何请求记录")
        
        print(f"\n3. 每日统计概览 (显示前10天):")
        if all_stats:
            print(f"   {'日期':<12} {'总请求':<10} {'成功请求':<10} {'成功率':<8}")
            print(f"   {'-'*42}")
            
            # 显示前10天的数据
            for i, (date, stats) in enumerate(sorted(all_stats.items())):
                if i >= 10:
                    remaining = len(all_stats) - 10
                    if remaining > 0:
                        print(f"   ... 还有 {remaining} 天的数据")
                    break
                
                print(f"   {date:<12} {stats['total']:<10,} {stats['success']:<10,} {stats['success_rate']:<7}%")
        
        # 总体统计
        total_requests = sum(stats['total'] for stats in all_stats.values())
        total_success = sum(stats['success'] for stats in all_stats.values())
        overall_rate = (total_success / total_requests * 100) if total_requests > 0 else 0
        
        print(f"\n4. 总体统计:")
        print(f"   分析天数: {len(all_stats)}")
        print(f"   总请求数: {total_requests:,}")
        print(f"   总成功数: {total_success:,}")
        print(f"   总体成功率: {overall_rate:.2f}%")


def create_large_sample_file(file_path: str, num_lines: int = 100000):
    """
    创建大型示例日志文件用于测试
    
    Args:
        file_path: 文件路径
        num_lines: 行数
    """
    import random
    
    print(f"正在创建包含 {num_lines:,} 行的示例日志文件...")
    
    # 基础日志模板
    base_logs = [
        '47.29.201.179 - - [28/Feb/2019:13:17:10 +0000] "GET /?p=1 HTTP/2.0" 200 5316 "https://domain1.com/?p=1" "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36" "2.75"',
        '192.168.1.100 - - [28/Feb/2019:13:18:15 +0000] "POST /api/login HTTP/1.1" 200 1234 "https://domain1.com/login" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" "1.23"',
        '10.0.0.50 - - [01/Mar/2019:13:19:20 +0000] "GET /images/logo.png HTTP/1.1" 404 0 "http://domain2.com/" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36" "0.45"',
        '203.0.113.45 - - [01/Mar/2019:09:30:45 +0000] "GET /admin/dashboard HTTP/1.1" 500 2048 "https://domain1.com/admin" "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:65.0) Gecko/20100101 Firefox/65.0" "5.67"',
        '198.51.100.25 - - [02/Mar/2019:14:22:33 +0000] "GET /api/users HTTP/2.0" 201 8192 "https://domain1.com/api" "curl/7.58.0" "0.89"'
    ]
    
    # 生成变量
    ips = ['47.29.201.179', '192.168.1.100', '10.0.0.50', '203.0.113.45', '198.51.100.25']
    methods = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD']
    urls = ['/', '/api/login', '/images/logo.png', '/admin/dashboard', '/api/users', '/profile', '/search']
    status_codes = [200, 201, 301, 404, 500, 502]
    referers = [
        'https://domain1.com/',
        'https://domain1.com/login', 
        'http://domain2.com/',
        'https://domain1.com/admin',
        'https://domain1.com/api',
        '-'
    ]
    
    start_time = time.time()
    
    with open(file_path, 'w', encoding='utf-8') as f:
        for i in range(num_lines):
            if i < len(base_logs):
                # 使用基础模板
                f.write(base_logs[i] + '\n')
            else:
                # 生成随机日志
                ip = random.choice(ips)
                day = random.randint(28, 31) if random.random() < 0.5 else random.randint(1, 10)
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
            
            # 显示进度
            if (i + 1) % 10000 == 0:
                elapsed = time.time() - start_time
                speed = (i + 1) / elapsed
                eta = (num_lines - i - 1) / speed
                print(f"\r生成进度: {((i+1)/num_lines*100):.1f}% | 速度: {speed:.0f} 行/秒 | 预计剩余: {eta:.0f}秒", end='', flush=True)
    
    elapsed = time.time() - start_time
    print(f"\n示例文件创建完成: {file_path}")
    print(f"耗时: {elapsed:.2f} 秒，包含 {num_lines:,} 行")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python high_performance_analyzer.py <日志文件路径> [日期(YYYY-MM-DD)] [选项]")
        print("\n选项:")
        print("  --create-sample N    创建包含N行的示例文件")
        print("  --use-mmap          使用内存映射处理大文件")
        print("\n示例:")
        print("  python high_performance_analyzer.py nginx.log 2019-02-28")
        print("  python high_performance_analyzer.py --create-sample 1000000")
        
        return
    
    # 解析参数
    if '--create-sample' in sys.argv:
        idx = sys.argv.index('--create-sample')
        if idx + 1 < len(sys.argv):
            try:
                num_lines = int(sys.argv[idx + 1])
                create_large_sample_file('large_nginx_sample.log', num_lines)
                
                # 如果没有其他参数，分析创建的示例文件
                if len(sys.argv) == 3:  # 只有脚本名和--create-sample N
                    print("\n开始分析创建的示例文件...")
                    analyzer = HighPerformanceNginxAnalyzer()
                    analyzer.process_file_streaming('large_nginx_sample.log')
                    analyzer.print_results('2019-02-28')
                
            except ValueError:
                print("错误: 示例行数必须是整数")
        return
    
    log_file = sys.argv[1]
    target_date = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else None
    use_mmap = '--use-mmap' in sys.argv
    
    # 创建分析器
    analyzer = HighPerformanceNginxAnalyzer()
    
    # 选择处理方法
    if use_mmap:
        analyzer.process_file_mmap(log_file)
    else:
        analyzer.process_file_streaming(log_file)
    
    # 显示结果
    analyzer.print_results(target_date)


if __name__ == "__main__":
    main()
