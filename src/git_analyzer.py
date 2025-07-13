"""
Git分析模块
Git Analysis Module
"""

import os
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from git import Repo, Commit, NULL_TREE
from git.exc import GitCommandError
import logging

from .models import CommitInfo, CommitType
from .config import config


logger = logging.getLogger(__name__)


class GitAnalyzer:
    """Git仓库分析器"""
    
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.repo = Repo(repo_path)
        self.repo_name = os.path.basename(repo_path.rstrip('/'))
        
        # 验证仓库
        if not self.repo.git_dir:
            raise ValueError(f"无效的Git仓库: {repo_path}")
    
    def get_commits(self, since_days: int = None, max_commits: int = None) -> List[Commit]:
        """获取指定时间范围内的提交"""
        if since_days is None:
            since_days = config.git_config.since_days
        if max_commits is None:
            max_commits = config.git_config.max_commits
        
        since = datetime.now() - timedelta(days=since_days)
        logger.info(f"获取 {self.repo_name} 从 {since.strftime('%Y-%m-%d')} 开始的提交")
        
        # 获取所有提交
        all_commits = list(self.repo.iter_commits(max_count=max_commits))
        
        # 过滤时间范围
        commits = [
            c for c in all_commits 
            if datetime.fromtimestamp(c.committed_date) > since
        ]
        
        # 智能过滤合并提交
        if config.git_config.exclude_merge_commits:
            commits = self._filter_merge_commits(commits)
        
        # 过滤空提交
        if config.git_config.exclude_empty_commits:
            commits = self._filter_empty_commits(commits)
        
        logger.info(f"找到 {len(commits)} 个有效提交")
        return commits
    
    def _filter_merge_commits(self, commits: List[Commit]) -> List[Commit]:
        """智能过滤合并提交"""
        filtered_commits = []
        
        for i, commit in enumerate(commits):
            if len(commit.parents) > 1:
                # 检查合并提交是否有实际内容
                if self._has_meaningful_changes(commit):
                    filtered_commits.append(commit)
                    logger.debug(f"保留有意义的合并提交: {commit.hexsha[:7]}")
                else:
                    logger.debug(f"跳过无意义的合并提交: {commit.hexsha[:7]}")
            else:
                filtered_commits.append(commit)
        
        return filtered_commits
    
    def _filter_empty_commits(self, commits: List[Commit]) -> List[Commit]:
        """过滤空提交"""
        filtered_commits = []
        
        for commit in commits:
            if self._has_changes(commit):
                filtered_commits.append(commit)
            else:
                logger.debug(f"跳过空提交: {commit.hexsha[:7]}")
        
        return filtered_commits
    
    def _has_meaningful_changes(self, commit: Commit) -> bool:
        """检查提交是否有有意义的变更"""
        try:
            if len(commit.parents) > 1:
                # 合并提交：检查与第一个父提交的差异
                diff = self.repo.git.diff(f"{commit.parents[0].hexsha}..{commit.hexsha}")
                return bool(diff.strip())
            else:
                # 普通提交：检查与父提交的差异
                diff = self.repo.git.diff(f"{commit.parents[0].hexsha}..{commit.hexsha}")
                return bool(diff.strip())
        except GitCommandError:
            return False
    
    def _has_changes(self, commit: Commit) -> bool:
        """检查提交是否有任何变更"""
        try:
            if commit.parents:
                diff = self.repo.git.diff(f"{commit.parents[0].hexsha}..{commit.hexsha}")
                return bool(diff.strip())
            else:
                # 初始提交
                return True
        except GitCommandError:
            return False
    
    def extract_commit_info(self, commit: Commit, index: int) -> CommitInfo:
        """提取提交信息"""
        try:
            # 获取GitHub链接
            github_link = self._get_github_link(commit)
            
            # 获取文件变更信息
            files_changed, lines_added, lines_deleted = self._get_change_stats(commit)
            
            # 确定提交类型
            commit_type = self._classify_commit_type(commit)
            
            # 获取分支信息
            branch = self._get_branch_name(commit)
            
            return CommitInfo(
                hash=commit.hexsha[:7],
                full_hash=commit.hexsha,
                author=commit.author.name,
                author_email=commit.author.email,
                message=commit.message.strip(),
                timestamp=datetime.fromtimestamp(commit.committed_date),
                files_changed=files_changed,
                lines_added=lines_added,
                lines_deleted=lines_deleted,
                commit_type=commit_type,
                repository=self.repo_name,
                branch=branch,
                github_link=github_link
            )
        except Exception as e:
            logger.error(f"提取提交信息失败 {commit.hexsha}: {e}")
            raise
    
    def _get_github_link(self, commit: Commit) -> Optional[str]:
        """获取GitHub链接"""
        try:
            remote_url = self.repo.remotes.origin.url
            if remote_url.endswith('.git'):
                remote_url = remote_url[:-4]
            
            if remote_url.startswith('git@github.com:'):
                org_repo = remote_url.replace('git@github.com:', '')
            elif remote_url.startswith('https://github.com/'):
                org_repo = remote_url.replace('https://github.com/', '')
            else:
                return None
            
            return f"https://github.com/{org_repo}/commit/{commit.hexsha}"
        except:
            return None
    
    def _get_change_stats(self, commit: Commit) -> Tuple[List[str], int, int]:
        """获取变更统计信息"""
        files_changed = []
        lines_added = 0
        lines_deleted = 0
        
        try:
            if commit.parents:
                # 获取差异统计
                diff_stats = self.repo.git.diff(f"{commit.parents[0].hexsha}..{commit.hexsha}", 
                                              stat=True, numstat=True)
                
                # 解析文件变更
                for line in diff_stats.split('\n'):
                    if line.startswith('diff --git'):
                        # 提取文件路径
                        parts = line.split()
                        if len(parts) >= 4:
                            file_path = parts[3][2:]  # 去掉 b/ 前缀
                            files_changed.append(file_path)
                    elif re.match(r'^\d+\s+\d+\s+', line):
                        # 解析行数统计
                        parts = line.split()
                        if len(parts) >= 3:
                            lines_added += int(parts[0]) if parts[0].isdigit() else 0
                            lines_deleted += int(parts[1]) if parts[1].isdigit() else 0
            else:
                # 初始提交
                for item in commit.tree.traverse():
                    if item.type == 'blob':
                        files_changed.append(item.path)
                        lines_added += len(item.data_stream.read().decode('utf-8', errors='ignore').split('\n'))
        
        except Exception as e:
            logger.warning(f"获取变更统计失败 {commit.hexsha}: {e}")
        
        return files_changed, lines_added, lines_deleted
    
    def _classify_commit_type(self, commit: Commit) -> CommitType:
        """分类提交类型"""
        message = commit.message.lower()
        
        # 关键词匹配
        if any(keyword in message for keyword in ['fix', 'bug', 'issue', 'error']):
            return CommitType.BUGFIX
        elif any(keyword in message for keyword in ['feat', 'feature', 'add', 'implement']):
            return CommitType.FEATURE
        elif any(keyword in message for keyword in ['refactor', 'refactoring']):
            return CommitType.REFACTOR
        elif any(keyword in message for keyword in ['doc', 'documentation', 'readme']):
            return CommitType.DOCUMENTATION
        elif any(keyword in message for keyword in ['test', 'spec', 'specs']):
            return CommitType.TEST
        elif any(keyword in message for keyword in ['merge', 'pull request']):
            return CommitType.MERGE
        else:
            return CommitType.OTHER
    
    def _get_branch_name(self, commit: Commit) -> str:
        """获取分支名称"""
        try:
            # 尝试获取当前分支
            return self.repo.active_branch.name
        except:
            return "unknown"
    
    def get_commit_diff(self, commit: Commit) -> str:
        """获取提交的差异内容"""
        try:
            if commit.parents:
                return self.repo.git.diff(f"{commit.parents[0].hexsha}..{commit.hexsha}")
            else:
                # 初始提交
                return self.repo.git.show(commit.hexsha, format='raw')
        except GitCommandError as e:
            logger.error(f"获取差异失败 {commit.hexsha}: {e}")
            return f"Failed to get diff: {e}"
    
    def get_repository_stats(self) -> Dict[str, any]:
        """获取仓库统计信息"""
        try:
            stats = {
                'name': self.repo_name,
                'path': self.repo_path,
                'total_commits': len(list(self.repo.iter_commits())),
                'branches': [branch.name for branch in self.repo.branches],
                'remotes': [remote.name for remote in self.repo.remotes],
                'last_commit': None,
                'active_branch': None
            }
            
            # 获取最新提交
            if self.repo.head.commit:
                stats['last_commit'] = {
                    'hash': self.repo.head.commit.hexsha[:7],
                    'message': self.repo.head.commit.message.strip(),
                    'author': self.repo.head.commit.author.name,
                    'date': datetime.fromtimestamp(self.repo.head.commit.committed_date)
                }
            
            # 获取当前分支
            try:
                stats['active_branch'] = self.repo.active_branch.name
            except:
                stats['active_branch'] = "detached"
            
            return stats
        except Exception as e:
            logger.error(f"获取仓库统计失败: {e}")
            return {}
    
    def get_contributors(self) -> List[Dict[str, str]]:
        """获取贡献者列表"""
        contributors = []
        seen_emails = set()
        
        for commit in self.repo.iter_commits():
            email = commit.author.email
            if email not in seen_emails:
                contributors.append({
                    'name': commit.author.name,
                    'email': email,
                    'first_commit': datetime.fromtimestamp(commit.committed_date)
                })
                seen_emails.add(email)
        
        return contributors


class MultiRepositoryAnalyzer:
    """多仓库分析器"""
    
    def __init__(self, repositories: List[str]):
        self.repositories = repositories
        self.analyzers = {}
        
        # 初始化每个仓库的分析器
        for repo_path in repositories:
            try:
                self.analyzers[repo_path] = GitAnalyzer(repo_path)
                logger.info(f"成功初始化仓库分析器: {repo_path}")
            except Exception as e:
                logger.error(f"初始化仓库分析器失败 {repo_path}: {e}")
    
    def analyze_all_repositories(self, since_days: int = None) -> Dict[str, List[CommitInfo]]:
        """分析所有仓库"""
        results = {}
        
        for repo_path, analyzer in self.analyzers.items():
            try:
                commits = analyzer.get_commits(since_days=since_days)
                commit_infos = []
                
                for i, commit in enumerate(commits):
                    try:
                        commit_info = analyzer.extract_commit_info(commit, i + 1)
                        commit_infos.append(commit_info)
                    except Exception as e:
                        logger.error(f"处理提交失败 {commit.hexsha}: {e}")
                
                results[repo_path] = commit_infos
                logger.info(f"完成仓库分析 {repo_path}: {len(commit_infos)} 个提交")
                
            except Exception as e:
                logger.error(f"分析仓库失败 {repo_path}: {e}")
                results[repo_path] = []
        
        return results
    
    def get_repository_stats(self) -> Dict[str, Dict[str, any]]:
        """获取所有仓库的统计信息"""
        stats = {}
        
        for repo_path, analyzer in self.analyzers.items():
            try:
                stats[repo_path] = analyzer.get_repository_stats()
            except Exception as e:
                logger.error(f"获取仓库统计失败 {repo_path}: {e}")
                stats[repo_path] = {}
        
        return stats
    
    def get_all_contributors(self) -> Dict[str, List[Dict[str, str]]]:
        """获取所有仓库的贡献者"""
        contributors = {}
        
        for repo_path, analyzer in self.analyzers.items():
            try:
                contributors[repo_path] = analyzer.get_contributors()
            except Exception as e:
                logger.error(f"获取贡献者失败 {repo_path}: {e}")
                contributors[repo_path] = []
        
        return contributors 