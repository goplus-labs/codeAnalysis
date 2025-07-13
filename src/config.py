"""
配置管理模块
Configuration Management Module
"""

import os
import yaml
from typing import Dict, Any, List
from dataclasses import dataclass
from pathlib import Path


@dataclass
class OpenAIConfig:
    """OpenAI配置"""
    model: str
    max_retries: int
    base_delay: float
    request_interval: float


@dataclass
class GitConfig:
    """Git配置"""
    max_commits: int
    since_days: int
    exclude_merge_commits: bool
    exclude_empty_commits: bool


@dataclass
class MetricsConfig:
    """评估指标配置"""
    code_quality: float
    productivity: float
    collaboration: float
    innovation: float
    maintenance: float


@dataclass
class RepositoryConfig:
    """仓库配置"""
    name: str
    path: str
    weight: float
    description: str


@dataclass
class EvaluationPeriod:
    """评估周期配置"""
    name: str
    days: int
    description: str


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config_data = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _validate_config(self):
        """验证配置文件的完整性"""
        required_sections = ['openai', 'git', 'metrics', 'repositories']
        for section in required_sections:
            if section not in self.config_data:
                raise ValueError(f"配置文件缺少必要部分: {section}")
    
    @property
    def openai_config(self) -> OpenAIConfig:
        """获取OpenAI配置"""
        config = self.config_data['openai']
        return OpenAIConfig(
            model=config.get('model', 'gpt-4'),
            max_retries=config.get('max_retries', 6),
            base_delay=config.get('base_delay', 1.0),
            request_interval=config.get('request_interval', 1.0)
        )
    
    @property
    def git_config(self) -> GitConfig:
        """获取Git配置"""
        config = self.config_data['git']
        return GitConfig(
            max_commits=config.get('max_commits', 1000),
            since_days=config.get('since_days', 30),
            exclude_merge_commits=config.get('exclude_merge_commits', True),
            exclude_empty_commits=config.get('exclude_empty_commits', True)
        )
    
    @property
    def metrics_config(self) -> MetricsConfig:
        """获取评估指标配置"""
        config = self.config_data['metrics']
        return MetricsConfig(
            code_quality=config.get('code_quality', 0.3),
            productivity=config.get('productivity', 0.25),
            collaboration=config.get('collaboration', 0.2),
            innovation=config.get('innovation', 0.15),
            maintenance=config.get('maintenance', 0.1)
        )
    
    @property
    def repositories(self) -> List[RepositoryConfig]:
        """获取仓库配置列表"""
        repos = []
        for repo_data in self.config_data['repositories']:
            repos.append(RepositoryConfig(
                name=repo_data['name'],
                path=repo_data['path'],
                weight=repo_data.get('weight', 1.0),
                description=repo_data.get('description', '')
            ))
        return repos
    
    @property
    def employee_mapping(self) -> Dict[str, List[str]]:
        """获取员工邮箱映射"""
        return self.config_data.get('employee_mapping', {})
    
    @property
    def evaluation_periods(self) -> List[EvaluationPeriod]:
        """获取评估周期配置"""
        periods = []
        for period_data in self.config_data.get('evaluation_periods', []):
            periods.append(EvaluationPeriod(
                name=period_data['name'],
                days=period_data['days'],
                description=period_data.get('description', '')
            ))
        return periods
    
    @property
    def output_config(self) -> Dict[str, Any]:
        """获取输出配置"""
        return self.config_data.get('output', {})
    
    @property
    def database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return self.config_data.get('database', {})
    
    @property
    def logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.config_data.get('logging', {})
    
    def get_repository_by_name(self, name: str) -> RepositoryConfig:
        """根据名称获取仓库配置"""
        for repo in self.repositories:
            if repo.name == name:
                return repo
        raise ValueError(f"未找到仓库配置: {name}")
    
    def get_repository_by_path(self, path: str) -> RepositoryConfig:
        """根据路径获取仓库配置"""
        for repo in self.repositories:
            if repo.path == path:
                return repo
        raise ValueError(f"未找到仓库配置: {path}")


# 全局配置实例
config = ConfigManager() 