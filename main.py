#!/usr/bin/env python3
"""
多仓库代码效率评估系统
Multi-Repository Code Efficiency Analysis System

主程序入口
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.efficiency_engine import EfficiencyEngine
from src.config import config
from src.models import get_performance_level


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """设置日志配置"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 配置根日志记录器
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # 如果指定了日志文件，添加文件处理器
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)
    
    # 设置第三方库的日志级别
    logging.getLogger('git').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)


def create_output_directories():
    """创建输出目录"""
    output_config = config.output_config
    base_dir = output_config.get('base_dir', 'analysis_results')
    
    directories = [
        base_dir,
        os.path.join(base_dir, 'reports'),
        os.path.join(base_dir, 'data'),
        os.path.join(base_dir, 'charts'),
        os.path.join(base_dir, 'logs')
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    return base_dir


def save_evaluation_result(evaluation_result, output_dir: str):
    """保存评估结果"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存JSON格式的评估结果
    result_file = os.path.join(output_dir, 'data', f'evaluation_result_{timestamp}.json')
    
    # 转换dataclass为字典
    def dataclass_to_dict(obj):
        if hasattr(obj, '__dict__'):
            result = {}
            for key, value in obj.__dict__.items():
                if hasattr(value, '__dict__'):
                    result[key] = dataclass_to_dict(value)
                elif isinstance(value, list):
                    result[key] = [dataclass_to_dict(item) if hasattr(item, '__dict__') else item for item in value]
                elif isinstance(value, dict):
                    result[key] = {k: dataclass_to_dict(v) if hasattr(v, '__dict__') else v for k, v in value.items()}
                elif isinstance(value, datetime):
                    result[key] = value.isoformat()
                else:
                    result[key] = value
            return result
        return obj
    
    result_dict = dataclass_to_dict(evaluation_result)
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result_dict, f, ensure_ascii=False, indent=2)
    
    print(f"评估结果已保存到: {result_file}")
    return result_file


def save_efficiency_report(report, output_dir: str):
    """保存效率报告"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存JSON格式的报告
    report_file = os.path.join(output_dir, 'reports', f'efficiency_report_{timestamp}.json')
    
    def dataclass_to_dict(obj):
        if hasattr(obj, '__dict__'):
            result = {}
            for key, value in obj.__dict__.items():
                if hasattr(value, '__dict__'):
                    result[key] = dataclass_to_dict(value)
                elif isinstance(value, list):
                    result[key] = [dataclass_to_dict(item) if hasattr(item, '__dict__') else item for item in value]
                elif isinstance(value, dict):
                    result[key] = {k: dataclass_to_dict(v) if hasattr(v, '__dict__') else v for k, v in value.items()}
                elif isinstance(value, datetime):
                    result[key] = value.isoformat()
                else:
                    result[key] = value
            return result
        return obj
    
    report_dict = dataclass_to_dict(report)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_dict, f, ensure_ascii=False, indent=2)
    
    print(f"效率报告已保存到: {report_file}")
    return report_file


def print_summary(evaluation_result, report):
    """打印评估摘要"""
    print("\n" + "="*80)
    print("多仓库代码效率评估系统 - 评估摘要")
    print("="*80)
    
    print(f"\n评估信息:")
    print(f"  评估ID: {evaluation_result.evaluation_id}")
    print(f"  评估名称: {evaluation_result.evaluation_name}")
    print(f"  评估周期: {evaluation_result.evaluation_period}")
    print(f"  时间范围: {evaluation_result.start_date.strftime('%Y-%m-%d')} 至 {evaluation_result.end_date.strftime('%Y-%m-%d')}")
    
    print(f"\n仓库统计:")
    print(f"  总仓库数: {evaluation_result.total_repositories}")
    for repo_name, repo_metrics in evaluation_result.repositories.items():
        print(f"  - {repo_name}: {repo_metrics.total_commits} 提交, {repo_metrics.total_contributors} 贡献者")
    
    print(f"\n员工统计:")
    print(f"  总员工数: {evaluation_result.total_employees}")
    print(f"  团队总体评分: {evaluation_result.overall_team_score}/1.0")
    
    # 绩效分布
    performance_counts = {}
    for emp in evaluation_result.employees.values():
        performance_counts[emp.performance_level] = performance_counts.get(emp.performance_level, 0) + 1
    
    print(f"\n绩效分布:")
    for level in ['excellent', 'good', 'average', 'below_average', 'poor']:
        count = performance_counts.get(level, 0)
        if count > 0:
            level_name = {
                'excellent': '优秀',
                'good': '良好', 
                'average': '一般',
                'below_average': '低于平均',
                'poor': '较差'
            }.get(level, level)
            print(f"  - {level_name}: {count} 人")
    
    print(f"\n关键发现:")
    for i, finding in enumerate(report.key_findings, 1):
        print(f"  {i}. {finding}")
    
    print(f"\n改进建议:")
    for i, recommendation in enumerate(report.recommendations, 1):
        print(f"  {i}. {recommendation}")
    
    print("\n" + "="*80)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="多仓库代码效率评估系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py --period monthly                    # 月度评估
  python main.py --period weekly --output-dir results # 周度评估，指定输出目录
  python main.py --custom-days 7 --log-level DEBUG   # 自定义7天评估，调试模式
        """
    )
    
    parser.add_argument(
        '--period',
        choices=['weekly', 'monthly', 'quarterly'],
        default='monthly',
        help='评估周期 (默认: monthly)'
    )
    
    parser.add_argument(
        '--custom-days',
        type=int,
        help='自定义评估天数（覆盖period设置）'
    )
    
    parser.add_argument(
        '--output-dir',
        help='输出目录 (默认: analysis_results)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='日志级别 (默认: INFO)'
    )
    
    parser.add_argument(
        '--log-file',
        help='日志文件路径'
    )
    
    parser.add_argument(
        '--config',
        help='配置文件路径 (默认: config.yaml)'
    )
    
    parser.add_argument(
        '--list-repos',
        action='store_true',
        help='列出配置的仓库信息'
    )
    
    parser.add_argument(
        '--list-employees',
        action='store_true',
        help='列出配置的员工信息'
    )
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.log_level, args.log_file)
    logger = logging.getLogger(__name__)
    
    try:
        # 显示配置信息
        if args.list_repos:
            print("配置的仓库:")
            for repo in config.repositories:
                print(f"  - {repo.name}: {repo.path} (权重: {repo.weight})")
            return
        
        if args.list_employees:
            print("配置的员工:")
            for name, emails in config.employee_mapping.items():
                print(f"  - {name}: {emails}")
            return
        
        # 创建输出目录
        output_dir = args.output_dir or create_output_directories()
        
        logger.info("开始多仓库代码效率评估")
        logger.info(f"评估周期: {args.period}")
        if args.custom_days:
            logger.info(f"自定义天数: {args.custom_days}")
        
        # 初始化评估引擎
        cache_dir = os.path.join(output_dir, 'cache', 'ai_analysis')
        engine = EfficiencyEngine(cache_dir=cache_dir)
        
        # 运行评估
        evaluation_result = engine.run_evaluation(
            evaluation_period=args.period,
            custom_days=args.custom_days
        )
        
        # 生成报告
        report = engine.generate_report(evaluation_result)
        
        # 保存结果
        save_evaluation_result(evaluation_result, output_dir)
        save_efficiency_report(report, output_dir)
        
        # 打印摘要
        print_summary(evaluation_result, report)
        
        logger.info("评估完成")
        
    except KeyboardInterrupt:
        logger.info("用户中断评估")
        sys.exit(1)
    except Exception as e:
        logger.error(f"评估失败: {e}")
        if args.log_level == 'DEBUG':
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 