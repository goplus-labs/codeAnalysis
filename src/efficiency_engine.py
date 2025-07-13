"""
效率评估引擎
Efficiency Evaluation Engine
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
import uuid

from .models import (
    EmployeeMetrics, RepositoryMetrics, EvaluationResult, 
    EfficiencyReport, get_performance_level
)
from .config import config
from .git_analyzer import MultiRepositoryAnalyzer
from .ai_analyzer import AnalysisManager


logger = logging.getLogger(__name__)


class EfficiencyEngine:
    """效率评估引擎"""
    
    def __init__(self, cache_dir: str = "cache/ai_analysis"):
        self.git_analyzer = MultiRepositoryAnalyzer([
            repo.path for repo in config.repositories
        ])
        self.analysis_manager = AnalysisManager(cache_dir=cache_dir)
        self.employee_mapping = config.employee_mapping
    
    def run_evaluation(self, evaluation_period: str = "monthly", 
                      custom_days: Optional[int] = None) -> EvaluationResult:
        """运行综合评估"""
        logger.info(f"开始运行效率评估，周期: {evaluation_period}")
        
        # 确定评估时间范围
        if custom_days:
            since_days = custom_days
        else:
            period_config = next(
                (p for p in config.evaluation_periods if p.name == evaluation_period),
                config.evaluation_periods[0]
            )
            since_days = period_config.days
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=since_days)
        
        # 生成评估ID
        evaluation_id = str(uuid.uuid4())
        evaluation_name = f"efficiency_evaluation_{evaluation_period}_{end_date.strftime('%Y%m%d')}"
        
        # 分析所有仓库
        logger.info("开始分析Git仓库...")
        commits_by_repo = self.git_analyzer.analyze_all_repositories(since_days)
        
        # 获取仓库统计信息
        repo_stats = self.git_analyzer.get_repository_stats()
        
        # 初始化评估结果
        evaluation_result = EvaluationResult(
            evaluation_id=evaluation_id,
            evaluation_name=evaluation_name,
            evaluation_period=evaluation_period,
            start_date=start_date,
            end_date=end_date,
            total_repositories=len(config.repositories),
            config_used={
                'metrics_weights': {
                    'code_quality': config.metrics_config.code_quality,
                    'productivity': config.metrics_config.productivity,
                    'collaboration': config.metrics_config.collaboration,
                    'innovation': config.metrics_config.innovation,
                    'maintenance': config.metrics_config.maintenance
                },
                'evaluation_period': evaluation_period,
                'since_days': since_days
            }
        )
        
        # 分析每个仓库
        for repo_config in config.repositories:
            repo_name = repo_config.name
            repo_path = repo_config.path
            
            if repo_path not in commits_by_repo:
                logger.warning(f"仓库 {repo_name} 没有找到提交数据")
                continue
            
            commits_info = commits_by_repo[repo_path]  # 分析所有commit
            logger.info(f"分析仓库 {repo_name}: {len(commits_info)} 个提交")
            
            # 获取差异内容
            diffs_content = self._get_diffs_content(repo_path, commits_info)
            
            # AI分析代码质量
            code_analyses = self.analysis_manager.analyze_repository_commits(
                [self._commit_info_to_dict(ci) for ci in commits_info],
                diffs_content
            )
            
            # 计算仓库指标
            repo_metrics = self._calculate_repository_metrics(
                repo_config, commits_info, code_analyses
            )
            
            # 计算员工指标
            employee_metrics = self._calculate_employee_metrics(
                repo_name, commits_info, code_analyses
            )
            
            # 更新仓库指标
            repo_metrics.employee_contributions = employee_metrics
            evaluation_result.repositories[repo_name] = repo_metrics
        
        # 合并所有员工的指标
        evaluation_result.employees = self._merge_employee_metrics(
            [repo.employee_contributions for repo in evaluation_result.repositories.values()]
        )
        
        # 计算总体团队评分
        evaluation_result.total_employees = len(evaluation_result.employees)
        evaluation_result.overall_team_score = self._calculate_team_score(
            evaluation_result.employees
        )
        
        logger.info(f"评估完成，共分析 {evaluation_result.total_repositories} 个仓库，"
                   f"{evaluation_result.total_employees} 个员工")
        
        return evaluation_result
    
    def _get_diffs_content(self, repo_path: str, commits_info: List[Any]) -> Dict[str, str]:
        """获取提交差异内容"""
        diffs_content = {}
        
        try:
            analyzer = self.git_analyzer.analyzers[repo_path]
            
            for commit_info in commits_info:
                try:
                    # 从Git获取对应的Commit对象
                    commit = analyzer.repo.commit(commit_info.full_hash)
                    diff_content = analyzer.get_commit_diff(commit)
                    diffs_content[commit_info.hash] = diff_content
                except Exception as e:
                    logger.warning(f"获取差异失败 {commit_info.hash}: {e}")
                    diffs_content[commit_info.hash] = ""
        except Exception as e:
            logger.error(f"获取差异内容失败 {repo_path}: {e}")
        
        return diffs_content
    
    def _commit_info_to_dict(self, commit_info: Any) -> Dict[str, Any]:
        """将CommitInfo转换为字典"""
        return {
            'hash': commit_info.hash,
            'full_hash': commit_info.full_hash,
            'author': commit_info.author,
            'author_email': commit_info.author_email,
            'message': commit_info.message,
            'timestamp': commit_info.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'files_changed': commit_info.files_changed,
            'lines_added': commit_info.lines_added,
            'lines_deleted': commit_info.lines_deleted,
            'commit_type': commit_info.commit_type.value,
            'repository': commit_info.repository,
            'branch': commit_info.branch,
            'github_link': commit_info.github_link
        }
    
    def _calculate_repository_metrics(self, repo_config: Any, 
                                    commits_info: List[Any], 
                                    code_analyses: List[Any]) -> RepositoryMetrics:
        """计算仓库指标"""
        # 基础统计
        total_commits = len(commits_info)
        total_lines_added = sum(ci.lines_added for ci in commits_info)
        total_lines_deleted = sum(ci.lines_deleted for ci in commits_info)
        
        # 贡献者统计
        contributors = set(ci.author_email for ci in commits_info)
        total_contributors = len(contributors)
        
        # 质量指标
        if code_analyses:
            average_code_quality = sum(analysis.score for analysis in code_analyses) / len(code_analyses)
        else:
            average_code_quality = 0.0
        
        # 活跃度指标
        if commits_info:
            commits_per_day = total_commits / config.git_config.since_days
            last_commit_date = max(ci.timestamp for ci in commits_info)
        else:
            commits_per_day = 0.0
            last_commit_date = None
        
        # 复杂度指标
        if code_analyses:
            complexity_scores = []
            for analysis in code_analyses:
                if analysis.complexity.value == 'low':
                    complexity_scores.append(0.3)
                elif analysis.complexity.value == 'medium':
                    complexity_scores.append(0.6)
                else:  # high
                    complexity_scores.append(1.0)
            average_complexity = sum(complexity_scores) / len(complexity_scores)
        else:
            average_complexity = 0.0
        
        return RepositoryMetrics(
            repository_name=repo_config.name,
            repository_path=repo_config.path,
            weight=repo_config.weight,
            total_commits=total_commits,
            total_contributors=total_contributors,
            total_lines_of_code=total_lines_added - total_lines_deleted,
            average_code_quality=average_code_quality,
            bug_density=0.0,  # 需要额外分析
            technical_debt_ratio=0.0,  # 需要额外分析
            commits_per_day=commits_per_day,
            active_contributors=total_contributors,
            last_commit_date=last_commit_date,
            average_complexity=average_complexity
        )
    
    def _calculate_employee_metrics(self, repo_name: str, 
                                  commits_info: List[Any], 
                                  code_analyses: List[Any]) -> Dict[str, EmployeeMetrics]:
        """计算员工指标"""
        employee_metrics = {}
        
        # 按员工分组
        commits_by_employee = defaultdict(list)
        analyses_by_employee = defaultdict(list)
        
        for i, commit_info in enumerate(commits_info):
            employee_email = commit_info.author_email
            commits_by_employee[employee_email].append(commit_info)
            if i < len(code_analyses):
                analyses_by_employee[employee_email].append(code_analyses[i])
        
        # 计算每个员工的指标
        for employee_email, commits in commits_by_employee.items():
            analyses = analyses_by_employee[employee_email]
            
            # 获取员工姓名
            employee_name = self._get_employee_name(employee_email)
            
            # 基础指标
            total_commits = len(commits)
            total_lines_added = sum(ci.lines_added for ci in commits)
            total_lines_deleted = sum(ci.lines_deleted for ci in commits)
            total_files_changed = sum(len(ci.files_changed) for ci in commits)
            
            # 质量指标
            if analyses:
                # 直接使用AI返回的量化分数（0~100），然后归一化到0~1
                quality_scores = []
                for analysis in analyses:
                    if hasattr(analysis, 'code_quality_score') and analysis.code_quality_score is not None:
                        quality_scores.append(analysis.code_quality_score / 100.0)  # 归一化到0~1
                    else:
                        quality_scores.append(analysis.score)  # 降级使用score
                average_code_quality_score = sum(quality_scores) / len(quality_scores)
                bug_fix_ratio = sum(1 for ci in commits if ci.commit_type.value == 'bugfix') / total_commits
            else:
                average_code_quality_score = 0.0
                bug_fix_ratio = 0.0
            
            # 效率指标 - 使用新的综合生产力计算
            productivity_metrics = self.calculate_comprehensive_productivity(commits, analyses)
            commits_per_day = productivity_metrics['commits_per_day']
            lines_per_commit = total_lines_added / total_commits if total_commits > 0 else 0
            average_commit_size = (total_lines_added + total_lines_deleted) / total_commits if total_commits > 0 else 0
            
            # 创新指标
            new_features_contributed = sum(1 for ci in commits if ci.commit_type.value == 'feature')
            
            # 维护指标
            maintenance_commits = sum(1 for ci in commits if ci.commit_type.value in ['bugfix', 'refactor'])
            
            # 计算综合评分
            overall_score = self._calculate_employee_overall_score(
                average_code_quality_score, 
                productivity_metrics['productivity_score'],  # 使用新的综合生产力分数
                bug_fix_ratio,
                new_features_contributed, 
                maintenance_commits
            )
            
            # 获取绩效等级
            performance_level = get_performance_level(overall_score)
            
            employee_metrics[employee_email] = EmployeeMetrics(
                employee_id=employee_email,
                employee_name=employee_name,
                email=employee_email,
                repositories=[repo_name],
                total_commits=total_commits,
                total_lines_added=total_lines_added,
                total_lines_deleted=total_lines_deleted,
                total_files_changed=total_files_changed,
                average_code_quality_score=average_code_quality_score,
                bug_fix_ratio=bug_fix_ratio,
                test_coverage=0.0,  # 需要额外分析
                commits_per_day=commits_per_day,
                lines_per_commit=lines_per_commit,
                average_commit_size=average_commit_size,
                code_review_participation=0.0,  # 需要额外分析
                merge_conflicts=0,  # 需要额外分析
                collaboration_score=0.0,  # 需要额外分析
                new_features_contributed=new_features_contributed,
                technical_debt_reduced=0.0,  # 需要额外分析
                innovation_score=0.0,  # 需要额外分析
                maintenance_commits=maintenance_commits,
                documentation_quality=0.0,  # 需要额外分析
                maintenance_score=0.0,  # 需要额外分析
                overall_score=overall_score,
                performance_level=performance_level.level,
                analysis_period=f"{config.git_config.since_days}天",
                start_date=datetime.now() - timedelta(days=config.git_config.since_days),
                end_date=datetime.now(),
                # 新增生产力详细指标
                productivity_score=productivity_metrics['productivity_score'],
                code_output_score=productivity_metrics['code_output_score'],
                commit_efficiency=productivity_metrics['commit_efficiency'],
                file_impact_score=productivity_metrics['file_impact_score'],
                complexity_multiplier=productivity_metrics['complexity_multiplier'],
                effort_multiplier=productivity_metrics['effort_multiplier'],
                tech_multiplier=productivity_metrics['tech_multiplier'],
                net_code_output=int(productivity_metrics['net_code_output'])
            )
        
        return employee_metrics
    
    def _get_employee_name(self, email: str) -> str:
        """根据邮箱获取员工姓名"""
        for name, emails in self.employee_mapping.items():
            if email in emails:
                return name
        return email
    
    def _calculate_employee_overall_score(self, quality_score: float, 
                                        productivity_score: float,  # 新的综合生产力分数
                                        bug_fix_ratio: float,
                                        new_features: int,
                                        maintenance_commits: int) -> float:
        """计算员工综合评分"""
        # 质量权重
        quality_weight = config.metrics_config.code_quality
        
        # 生产力权重
        productivity_weight = config.metrics_config.productivity
        
        # 协作权重（基于bug修复比例）
        collaboration_weight = config.metrics_config.collaboration
        
        # 创新权重
        innovation_weight = config.metrics_config.innovation
        
        # 维护权重
        maintenance_weight = config.metrics_config.maintenance
        
        # 标准化各项指标
        normalized_productivity = min(productivity_score, 1.0)  # 生产力分数已经是0~1
        normalized_bug_fix = bug_fix_ratio
        normalized_innovation = min(new_features / 5.0, 1.0)  # 假设5个新功能为满分
        normalized_maintenance = min(maintenance_commits / 10.0, 1.0)  # 假设10个维护提交为满分
        
        # 计算综合评分
        overall_score = (
            quality_score * quality_weight +
            normalized_productivity * productivity_weight +
            normalized_bug_fix * collaboration_weight +
            normalized_innovation * innovation_weight +
            normalized_maintenance * maintenance_weight
        )
        
        return round(overall_score, 2)
    
    def _merge_employee_metrics(self, employee_metrics_list: List[Dict[str, EmployeeMetrics]]) -> Dict[str, EmployeeMetrics]:
        """合并多个仓库的员工指标"""
        merged_metrics = {}
        
        for repo_metrics in employee_metrics_list:
            for email, metrics in repo_metrics.items():
                if email in merged_metrics:
                    # 合并指标
                    existing = merged_metrics[email]
                    existing.total_commits += metrics.total_commits
                    existing.total_lines_added += metrics.total_lines_added
                    existing.total_lines_deleted += metrics.total_lines_deleted
                    existing.total_files_changed += metrics.total_files_changed
                    existing.repositories.extend(metrics.repositories)
                    existing.repositories = list(set(existing.repositories))  # 去重
                    
                    # 重新计算平均指标
                    existing.average_code_quality_score = (
                        (existing.average_code_quality_score + metrics.average_code_quality_score) / 2
                    )
                    existing.commits_per_day += metrics.commits_per_day
                    existing.lines_per_commit = (
                        (existing.lines_per_commit + metrics.lines_per_commit) / 2
                    )
                    existing.average_commit_size = (
                        (existing.average_commit_size + metrics.average_commit_size) / 2
                    )
                    
                    # 重新计算综合评分
                    existing.overall_score = self._calculate_employee_overall_score(
                        existing.average_code_quality_score,
                        existing.commits_per_day,
                        existing.bug_fix_ratio,
                        existing.new_features_contributed,
                        existing.maintenance_commits
                    )
                    
                    # 更新绩效等级
                    performance_level = get_performance_level(existing.overall_score)
                    existing.performance_level = performance_level.level
                else:
                    merged_metrics[email] = metrics
        
        return merged_metrics
    
    def _calculate_team_score(self, employees: Dict[str, EmployeeMetrics]) -> float:
        """计算团队总体评分"""
        if not employees:
            return 0.0
        
        total_score = sum(emp.overall_score for emp in employees.values())
        return round(total_score / len(employees), 2)
    
    def generate_report(self, evaluation_result: EvaluationResult, 
                       report_type: str = "comprehensive") -> EfficiencyReport:
        """生成评估报告"""
        logger.info(f"生成 {report_type} 报告")
        
        report_id = str(uuid.uuid4())
        
        # 生成报告摘要
        summary = self._generate_summary(evaluation_result)
        
        # 生成关键发现
        key_findings = self._generate_key_findings(evaluation_result)
        
        # 生成建议
        recommendations = self._generate_recommendations(evaluation_result)
        
        # 生成图表数据
        charts_data = self._generate_charts_data(evaluation_result)
        
        return EfficiencyReport(
            report_id=report_id,
            report_type=report_type,
            evaluation_result=evaluation_result,
            summary=summary,
            key_findings=key_findings,
            recommendations=recommendations,
            charts_data=charts_data
        )
    
    def _generate_summary(self, evaluation_result: EvaluationResult) -> str:
        """生成报告摘要"""
        total_repos = evaluation_result.total_repositories
        total_employees = evaluation_result.total_employees
        team_score = evaluation_result.overall_team_score
        
        # 统计绩效分布
        performance_distribution = defaultdict(int)
        for emp in evaluation_result.employees.values():
            performance_distribution[emp.performance_level] += 1
        
        summary = f"""
本次评估涵盖了 {total_repos} 个代码仓库，分析了 {total_employees} 位开发人员的工作表现。

团队总体评分：{team_score}/1.0

绩效分布：
- 优秀：{performance_distribution.get('excellent', 0)} 人
- 良好：{performance_distribution.get('good', 0)} 人  
- 一般：{performance_distribution.get('average', 0)} 人
- 低于平均：{performance_distribution.get('below_average', 0)} 人
- 较差：{performance_distribution.get('poor', 0)} 人

评估时间范围：{evaluation_result.start_date.strftime('%Y-%m-%d')} 至 {evaluation_result.end_date.strftime('%Y-%m-%d')}
        """
        
        return summary.strip()
    
    def _generate_key_findings(self, evaluation_result: EvaluationResult) -> List[str]:
        """生成关键发现"""
        findings = []
        
        # 分析团队整体表现
        if evaluation_result.overall_team_score >= 0.8:
            findings.append("团队整体表现优秀，代码质量和开发效率都达到了较高水平")
        elif evaluation_result.overall_team_score >= 0.6:
            findings.append("团队表现良好，但在某些方面还有改进空间")
        else:
            findings.append("团队表现需要关注，建议制定改进计划")
        
        # 分析绩效分布
        performance_counts = defaultdict(int)
        for emp in evaluation_result.employees.values():
            performance_counts[emp.performance_level] += 1
        
        if performance_counts.get('poor', 0) > 0:
            findings.append(f"发现 {performance_counts['poor']} 位员工表现较差，需要重点关注")
        
        if performance_counts.get('excellent', 0) > 0:
            findings.append(f"有 {performance_counts['excellent']} 位员工表现卓越，可以作为团队标杆")
        
        # 分析仓库活跃度
        for repo_name, repo_metrics in evaluation_result.repositories.items():
            if repo_metrics.commits_per_day > 5:
                findings.append(f"仓库 {repo_name} 活跃度很高，开发节奏紧凑")
            elif repo_metrics.commits_per_day < 1:
                findings.append(f"仓库 {repo_name} 活跃度较低，可能需要关注")
        
        return findings
    
    def _generate_recommendations(self, evaluation_result: EvaluationResult) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于团队评分的建议
        if evaluation_result.overall_team_score < 0.6:
            recommendations.append("建议加强代码审查机制，提升代码质量")
            recommendations.append("考虑增加技术培训和知识分享活动")
        
        # 基于员工绩效的建议
        poor_performers = [emp for emp in evaluation_result.employees.values() 
                          if emp.performance_level == 'poor']
        
        if poor_performers:
            recommendations.append(f"为 {len(poor_performers)} 位表现较差的员工制定个性化改进计划")
            recommendations.append("考虑安排导师指导，帮助提升技能")
        
        # 基于仓库活跃度的建议
        low_activity_repos = [repo for repo in evaluation_result.repositories.values() 
                             if repo.commits_per_day < 1]
        
        if low_activity_repos:
            recommendations.append("对于活跃度较低的仓库，建议重新评估项目优先级和资源配置")
        
        # 通用建议
        recommendations.append("建立定期的代码质量回顾机制")
        recommendations.append("鼓励团队成员参与开源项目，提升技术视野")
        recommendations.append("完善技术文档和知识库，促进知识传承")
        
        return recommendations
    
    def _generate_charts_data(self, evaluation_result: EvaluationResult) -> Dict[str, Any]:
        """生成图表数据"""
        charts_data = {
            'performance_distribution': {},
            'repository_activity': {},
            'employee_scores': {},
            'quality_trends': {}
        }
        
        # 绩效分布数据
        performance_counts = defaultdict(int)
        for emp in evaluation_result.employees.values():
            performance_counts[emp.performance_level] += 1
        charts_data['performance_distribution'] = dict(performance_counts)
        
        # 仓库活跃度数据
        repo_activity = {}
        for repo_name, repo_metrics in evaluation_result.repositories.items():
            repo_activity[repo_name] = {
                'commits_per_day': repo_metrics.commits_per_day,
                'total_commits': repo_metrics.total_commits,
                'contributors': repo_metrics.total_contributors
            }
        charts_data['repository_activity'] = repo_activity
        
        # 员工评分数据
        employee_scores = {}
        for emp in evaluation_result.employees.values():
            employee_scores[emp.employee_name] = {
                'overall_score': emp.overall_score,
                'quality_score': emp.average_code_quality_score,
                'productivity': emp.commits_per_day
            }
        charts_data['employee_scores'] = employee_scores
        
        return charts_data 

    def calculate_comprehensive_productivity(self, commits_info: List[Any], code_analyses: List[Any]) -> Dict[str, float]:
        """计算综合生产力指标"""
        
        # 基础指标
        total_commits = len(commits_info)
        total_lines_added = sum(ci.lines_added for ci in commits_info)
        total_lines_deleted = sum(ci.lines_deleted for ci in commits_info)
        total_files_changed = sum(len(ci.files_changed) for ci in commits_info)
        
        # 1. 代码产出量（考虑新增vs删除）
        net_code_output = total_lines_added - total_lines_deleted
        code_output_score = min(max(net_code_output / 1000.0, 0.0), 1.0)  # 1000行为满分
        
        # 2. 工作复杂度（基于AI分析）
        if code_analyses:
            avg_complexity_score = sum(a.complexity_score for a in code_analyses if a.complexity_score is not None) / len(code_analyses)
            avg_effort_score = sum(a.effort_score for a in code_analyses if a.effort_score is not None) / len(code_analyses)
            complexity_multiplier = avg_complexity_score / 100.0  # 复杂度越高，生产力权重越大
            effort_multiplier = avg_effort_score / 100.0
        else:
            complexity_multiplier = 0.5
            effort_multiplier = 0.5
        
        # 3. 提交效率（避免频繁小提交）
        commits_per_day = total_commits / config.git_config.since_days
        commit_efficiency = min(commits_per_day / 3.0, 1.0)  # 每天3次提交为满分
        
        # 4. 文件变更范围（影响面）
        file_impact_score = min(max(total_files_changed / 50.0, 0.0), 1.0)  # 50个文件为满分
        
        # 5. 技术栈调整
        tech_multiplier = self.get_tech_stack_productivity_multiplier(commits_info)
        
        # 6. 综合生产力计算
        productivity_score = (
            code_output_score * 0.3 +           # 代码产出量 30%
            commit_efficiency * 0.2 +           # 提交效率 20%
            file_impact_score * 0.2 +           # 影响范围 20%
            complexity_multiplier * 0.15 +      # 复杂度权重 15%
            effort_multiplier * 0.15            # 工作量权重 15%
        ) * tech_multiplier
        
        return {
            'productivity_score': round(productivity_score, 3),
            'code_output_score': round(code_output_score, 3),
            'commit_efficiency': round(commit_efficiency, 3),
            'file_impact_score': round(file_impact_score, 3),
            'complexity_multiplier': round(complexity_multiplier, 3),
            'effort_multiplier': round(effort_multiplier, 3),
            'tech_multiplier': round(tech_multiplier, 3),
            'net_code_output': net_code_output,
            'total_files_changed': total_files_changed,
            'commits_per_day': round(commits_per_day, 2)
        }
    
    def get_tech_stack_productivity_multiplier(self, commits_info: List[Any]) -> float:
        """根据技术栈调整生产力权重"""
        lang_count = {'java': 0, 'js': 0, 'c++': 0, 'go': 0}
        
        for ci in commits_info:
            for f in ci.files_changed:
                if f.endswith('.java'):
                    lang_count['java'] += 1
                elif f.endswith('.js') or f.endswith('.jsx') or f.endswith('.ts') or f.endswith('.tsx'):
                    lang_count['js'] += 1
                elif f.endswith('.cpp') or f.endswith('.cc') or f.endswith('.hpp') or f.endswith('.cxx'):
                    lang_count['c++'] += 1
                elif f.endswith('.go'):
                    lang_count['go'] += 1
        
        main_lang = max(lang_count, key=lambda k: lang_count[k])
        if lang_count[main_lang] == 0:
            return 1.0  # 默认权重
        
        # 不同技术栈的生产力标准
        multipliers = {
            'java': 1.0,    # 标准
            'js': 0.8,      # 前端开发相对简单
            'c++': 1.3,     # 系统级开发复杂度高
            'go': 1.1       # 现代后端开发
        }
        
        return multipliers.get(main_lang, 1.0) 