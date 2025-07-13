"""
数据模型模块
Data Models Module
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class CodeQuality(Enum):
    """代码质量等级"""
    EXCELLENT = "excellent"
    GOOD = "good"
    MEDIUM = "medium"
    POOR = "poor"


class Complexity(Enum):
    """代码复杂度等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Effort(Enum):
    """工作量等级"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class CommitType(Enum):
    """提交类型"""
    FEATURE = "feature"
    BUGFIX = "bugfix"
    REFACTOR = "refactor"
    DOCUMENTATION = "documentation"
    TEST = "test"
    MERGE = "merge"
    OTHER = "other"


@dataclass
class CommitInfo:
    """提交信息"""
    hash: str
    full_hash: str
    author: str
    author_email: str
    message: str
    timestamp: datetime
    files_changed: List[str]
    lines_added: int
    lines_deleted: int
    commit_type: CommitType
    repository: str
    branch: str
    github_link: Optional[str] = None


@dataclass
class CodeAnalysis:
    """代码分析结果"""
    commit_hash: str
    complexity: Complexity
    code_quality: CodeQuality
    effort: Effort
    summary: List[str]
    analysis: List[str]
    advice: List[str]
    reasoning: Dict[str, str]
    score: float = 0.0
    # 新增量化分数字段
    code_quality_score: Optional[float] = None
    complexity_score: Optional[float] = None
    effort_score: Optional[float] = None


@dataclass
class EmployeeMetrics:
    """员工评估指标"""
    employee_id: str
    employee_name: str
    email: str
    repositories: List[str]
    
    # 基础指标
    total_commits: int = 0
    total_lines_added: int = 0
    total_lines_deleted: int = 0
    total_files_changed: int = 0
    
    # 质量指标
    average_code_quality_score: float = 0.0
    bug_fix_ratio: float = 0.0
    test_coverage: float = 0.0
    
    # 效率指标
    commits_per_day: float = 0.0
    lines_per_commit: float = 0.0
    average_commit_size: float = 0.0
    
    # 新增生产力详细指标
    productivity_score: float = 0.0
    code_output_score: float = 0.0
    commit_efficiency: float = 0.0
    file_impact_score: float = 0.0
    complexity_multiplier: float = 0.0
    effort_multiplier: float = 0.0
    tech_multiplier: float = 0.0
    net_code_output: int = 0
    
    # 协作指标
    code_review_participation: float = 0.0
    merge_conflicts: int = 0
    collaboration_score: float = 0.0
    
    # 创新指标
    new_features_contributed: int = 0
    technical_debt_reduced: float = 0.0
    innovation_score: float = 0.0
    
    # 维护指标
    maintenance_commits: int = 0
    documentation_quality: float = 0.0
    maintenance_score: float = 0.0
    
    # 综合评分
    overall_score: float = 0.0
    performance_level: str = "unknown"
    
    # 时间范围
    analysis_period: str = ""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@dataclass
class RepositoryMetrics:
    """仓库评估指标"""
    repository_name: str
    repository_path: str
    weight: float
    
    # 基础统计
    total_commits: int = 0
    total_contributors: int = 0
    total_lines_of_code: int = 0
    
    # 质量指标
    average_code_quality: float = 0.0
    bug_density: float = 0.0
    technical_debt_ratio: float = 0.0
    
    # 活跃度指标
    commits_per_day: float = 0.0
    active_contributors: int = 0
    last_commit_date: Optional[datetime] = None
    
    # 复杂度指标
    average_complexity: float = 0.0
    file_complexity_distribution: Dict[str, int] = field(default_factory=dict)
    
    # 员工贡献
    employee_contributions: Dict[str, EmployeeMetrics] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """评估结果"""
    evaluation_id: str
    evaluation_name: str
    evaluation_period: str
    start_date: datetime
    end_date: datetime
    
    # 仓库评估结果
    repositories: Dict[str, RepositoryMetrics] = field(default_factory=dict)
    
    # 员工评估结果
    employees: Dict[str, EmployeeMetrics] = field(default_factory=dict)
    
    # 综合统计
    total_repositories: int = 0
    total_employees: int = 0
    overall_team_score: float = 0.0
    
    # 评估配置
    config_used: Dict[str, Any] = field(default_factory=dict)
    
    # 生成时间
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class PerformanceLevel:
    """绩效等级"""
    level: str
    min_score: float
    max_score: float
    description: str
    recommendations: List[str] = field(default_factory=list)


@dataclass
class EfficiencyReport:
    """效率报告"""
    report_id: str
    report_type: str  # "individual", "team", "repository", "comprehensive"
    evaluation_result: EvaluationResult
    
    # 报告内容
    summary: str = ""
    key_findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # 可视化数据
    charts_data: Dict[str, Any] = field(default_factory=dict)
    
    # 生成时间
    generated_at: datetime = field(default_factory=datetime.now)
    
    # 报告格式
    formats: List[str] = field(default_factory=lambda: ["json", "html", "pdf"])


# 预定义的绩效等级
PERFORMANCE_LEVELS = [
    PerformanceLevel(
        level="excellent",
        min_score=0.9,
        max_score=1.0,
        description="优秀 - 表现卓越，是团队的核心贡献者",
        recommendations=[
            "继续保持当前的高标准",
            "考虑承担更多技术领导职责",
            "分享最佳实践给团队成员"
        ]
    ),
    PerformanceLevel(
        level="good",
        min_score=0.7,
        max_score=0.89,
        description="良好 - 表现稳定，能够独立完成任务",
        recommendations=[
            "在特定领域深化专业技能",
            "参与更多代码审查",
            "尝试承担更具挑战性的任务"
        ]
    ),
    PerformanceLevel(
        level="average",
        min_score=0.5,
        max_score=0.69,
        description="一般 - 基本满足工作要求，有改进空间",
        recommendations=[
            "加强代码质量意识",
            "提高提交频率和稳定性",
            "参与技术培训和学习"
        ]
    ),
    PerformanceLevel(
        level="below_average",
        min_score=0.3,
        max_score=0.49,
        description="低于平均 - 需要重点关注和改进",
        recommendations=[
            "制定详细的改进计划",
            "寻求导师指导",
            "加强基础技能训练"
        ]
    ),
    PerformanceLevel(
        level="poor",
        min_score=0.0,
        max_score=0.29,
        description="较差 - 需要立即采取行动",
        recommendations=[
            "制定严格的改进计划",
            "考虑岗位调整",
            "提供必要的支持和培训"
        ]
    )
]


def get_performance_level(score: float) -> PerformanceLevel:
    """根据评分获取绩效等级"""
    for level in PERFORMANCE_LEVELS:
        if level.min_score <= score <= level.max_score:
            return level
    return PERFORMANCE_LEVELS[-1]  # 默认返回最差等级 