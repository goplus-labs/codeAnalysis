"""
AI分析模块
AI Analysis Module
"""

import os
import time
import json
import logging
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

from .models import CodeAnalysis, Complexity, CodeQuality, Effort
from .config import config

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

MAX_DIFF_CHARS = 3000  # 最大diff字符数


class AIAnalyzer:
    """AI代码分析器"""
    
    def __init__(self, cache_dir: str = "cache/ai_analysis"):
        # 支持OpenRouter和OpenAI API key
        self.api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("请设置 OPENROUTER_API_KEY 或 OPENAI_API_KEY 环境变量")
        
        # 检查是否使用OpenRouter
        self.use_openrouter = bool(os.getenv("OPENROUTER_API_KEY"))
        
        if self.use_openrouter:
            # OpenRouter配置
            self.base_url = "https://openrouter.ai/api/v1"
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            # 支持自定义Referer和Title
            self.extra_headers = {}
            referer = os.getenv("OPENROUTER_REFERER")
            title = os.getenv("OPENROUTER_TITLE")
            if referer:
                self.extra_headers["HTTP-Referer"] = referer
            if title:
                self.extra_headers["X-Title"] = title
            # 使用OpenRouter支持的模型
            self.model = os.getenv("OPENROUTER_MODEL") or config.openai_config.model
        else:
            # OpenAI配置
            self.client = OpenAI(api_key=self.api_key)
            self.model = config.openai_config.model
            self.extra_headers = None
        
        self.max_retries = config.openai_config.max_retries
        self.base_delay = config.openai_config.base_delay
        self.request_interval = config.openai_config.request_interval
        
        # 请求间隔控制
        self.last_request_time = 0
        
        # 缓存目录
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        
        logger.info(f"使用 {'OpenRouter' if self.use_openrouter else 'OpenAI'} API，模型: {self.model}")
    
    def _get_cache_key(self, commit_info: Dict[str, Any], diff_content: str) -> str:
        """生成缓存键"""
        # 基于commit信息和diff内容生成唯一键
        content = f"{commit_info.get('hash', '')}_{commit_info.get('message', '')}_{diff_content[:1000]}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> str:
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def _load_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """从缓存加载分析结果"""
        cache_path = self._get_cache_path(cache_key)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                logger.info(f"从缓存加载分析结果: {cache_key}")
                return cached_data
            except Exception as e:
                logger.warning(f"加载缓存失败 {cache_path}: {e}")
        return None
    
    def _save_to_cache(self, cache_key: str, analysis_result: Dict[str, Any]):
        """保存分析结果到缓存"""
        cache_path = self._get_cache_path(cache_key)
        try:
            # 将枚举转换为字符串以便JSON序列化
            serializable_result = {}
            for key, value in analysis_result.items():
                if hasattr(value, 'value'):  # 枚举类型
                    serializable_result[key] = value.value
                elif hasattr(value, 'isoformat'):  # datetime类型
                    serializable_result[key] = value.isoformat()
                else:
                    serializable_result[key] = value
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_result, f, ensure_ascii=False, indent=2)
            logger.info(f"分析结果已缓存: {cache_key}")
        except Exception as e:
            logger.warning(f"保存缓存失败 {cache_path}: {e}")
    
    def analyze_commit(self, commit_info: Dict[str, Any], diff_content: str) -> CodeAnalysis:
        """分析单个提交"""
        try:
            # 生成缓存键
            cache_key = self._get_cache_key(commit_info, diff_content)
            
            # 尝试从缓存加载
            cached_result = self._load_from_cache(cache_key)
            if cached_result:
                # 处理量化分数到枚举的转换
                if 'code_quality_score' in cached_result and 'complexity_score' in cached_result and 'effort_score' in cached_result:
                    # 新格式：从量化分数推导枚举
                    quality_score = cached_result.get('code_quality_score', 60)
                    complexity_score = cached_result.get('complexity_score', 50)
                    effort_score = cached_result.get('effort_score', 50)
                    
                    # 根据分数推导枚举值
                    if quality_score >= 85:
                        cached_result['code_quality'] = CodeQuality.EXCELLENT
                    elif quality_score >= 70:
                        cached_result['code_quality'] = CodeQuality.GOOD
                    elif quality_score >= 50:
                        cached_result['code_quality'] = CodeQuality.MEDIUM
                    else:
                        cached_result['code_quality'] = CodeQuality.POOR
                    
                    if complexity_score >= 80:
                        cached_result['complexity'] = Complexity.HIGH
                    elif complexity_score >= 40:
                        cached_result['complexity'] = Complexity.MEDIUM
                    else:
                        cached_result['complexity'] = Complexity.LOW
                    
                    if effort_score >= 80:
                        cached_result['effort'] = Effort.HARD
                    elif effort_score >= 40:
                        cached_result['effort'] = Effort.MEDIUM
                    else:
                        cached_result['effort'] = Effort.EASY
                else:
                    # 旧格式：将字符串转换为枚举类型
                    if 'complexity' in cached_result:
                        complexity_str = cached_result['complexity']
                        if complexity_str == 'low':
                            cached_result['complexity'] = Complexity.LOW
                        elif complexity_str == 'high':
                            cached_result['complexity'] = Complexity.HIGH
                        else:
                            cached_result['complexity'] = Complexity.MEDIUM
                    
                    if 'code_quality' in cached_result:
                        quality_str = cached_result['code_quality']
                        if quality_str == 'excellent':
                            cached_result['code_quality'] = CodeQuality.EXCELLENT
                        elif quality_str == 'good':
                            cached_result['code_quality'] = CodeQuality.GOOD
                        elif quality_str == 'poor':
                            cached_result['code_quality'] = CodeQuality.POOR
                        else:
                            cached_result['code_quality'] = CodeQuality.MEDIUM
                    
                    if 'effort' in cached_result:
                        effort_str = cached_result['effort']
                        if effort_str == 'easy':
                            cached_result['effort'] = Effort.EASY
                        elif effort_str == 'hard':
                            cached_result['effort'] = Effort.HARD
                        else:
                            cached_result['effort'] = Effort.MEDIUM
                
                # 确保量化分数字段存在
                if 'code_quality_score' not in cached_result:
                    cached_result['code_quality_score'] = None
                if 'complexity_score' not in cached_result:
                    cached_result['complexity_score'] = None
                if 'effort_score' not in cached_result:
                    cached_result['effort_score'] = None
                
                # 确保必需字段存在
                if 'complexity' not in cached_result:
                    cached_result['complexity'] = Complexity.MEDIUM
                if 'code_quality' not in cached_result:
                    cached_result['code_quality'] = CodeQuality.MEDIUM
                if 'effort' not in cached_result:
                    cached_result['effort'] = Effort.MEDIUM
                
                return CodeAnalysis(**cached_result)
            
            # 截断diff内容，防止超长
            if len(diff_content) > MAX_DIFF_CHARS:
                diff_content = diff_content[:MAX_DIFF_CHARS] + '\n...（内容过长已截断）...'
            
            # 构建分析提示
            prompt = self._build_analysis_prompt(commit_info, diff_content)
            
            # 调用OpenAI API
            response = self._call_openai_with_retry(prompt)
            
            # 解析响应
            analysis_result = self._parse_analysis_response(response)
            
            # 计算综合评分
            score = self._calculate_score(analysis_result)
            analysis_result['score'] = score
            analysis_result['commit_hash'] = commit_info.get('hash', 'unknown')  # 补充commit_hash
            
            # 添加量化分数字段
            analysis_result['code_quality_score'] = analysis_result.get('code_quality_score')
            analysis_result['complexity_score'] = analysis_result.get('complexity_score')
            analysis_result['effort_score'] = analysis_result.get('effort_score')
            
            # 保存到缓存
            self._save_to_cache(cache_key, analysis_result)
            
            return CodeAnalysis(**analysis_result)
            
        except Exception as e:
            logger.error(f"分析提交失败 {commit_info.get('hash', 'unknown')}: {e}")
            # 返回默认分析结果
            return self._get_default_analysis(commit_info)
    
    def _build_analysis_prompt(self, commit_info: Dict[str, Any], diff_content: str) -> str:
        """构建分析提示"""
        # 自动识别主技术栈（简单根据文件后缀统计）
        files = commit_info.get('files_changed', [])
        lang_count = {'java': 0, 'js': 0, 'c++': 0, 'go': 0}
        for f in files:
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
            main_lang = 'unknown'

        prompt = f"""
你是一个专业的代码审查专家，擅长分析代码质量和开发效率。
本次提交主要涉及的主技术栈: {main_lang}
请结合该技术栈的行业最佳实践和质量标准，给出如下量化评价：

1. 代码质量分数（code_quality_score，0~100，分数越高质量越好。请务必拉开分布，极高分只给极优秀代码，极低分只给明显有问题的代码。举例：结构混乱/无注释/有bug可给30分以下，规范优秀/高可维护性/有测试可给90分以上。请避免所有分数集中在60~80区间。）
2. 复杂度分数（complexity_score，0~100，分数越高越复杂）
3. 工作量分数（effort_score，0~100，分数越高工作量越大）
4. 详细理由说明

请以如下JSON格式返回：
{{
  "code_quality_score": 85,
  "complexity_score": 40,
  "effort_score": 30,
  "summary": ["..."],
  "analysis": ["..."],
  "advice": ["..."],
  "reasoning": {{
    "code_quality": "...",
    "complexity": "...",
    "effort": "..."
  }}
}}

提交信息：
- 提交哈希: {commit_info.get('hash', 'unknown')}
- 作者: {commit_info.get('author', 'unknown')}
- 提交信息: {commit_info.get('message', 'unknown')}
- 提交时间: {commit_info.get('timestamp', 'unknown')}
- 变更文件数: {len(files)}
- 新增行数: {commit_info.get('lines_added', 0)}
- 删除行数: {commit_info.get('lines_deleted', 0)}

代码diff如下：
{diff_content}
"""
        return prompt
    
    def _call_openai_with_retry(self, prompt: str) -> str:
        """调用OpenAI API，带重试机制"""
        for attempt in range(self.max_retries):
            try:
                # 控制请求间隔
                self._wait_for_rate_limit()
                
                if self.use_openrouter:
                    # OpenRouter官方推荐用法，带extra_headers
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "你是一个专业的代码审查专家，擅长分析代码质量和开发效率。"},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,
                        max_tokens=1024,
                        extra_headers=self.extra_headers if self.extra_headers else None
                    )
                else:
                    # OpenAI官方用法
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "你是一个专业的代码审查专家，擅长分析代码质量和开发效率。"},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,
                        max_tokens=1024
                    )
                
                return response.choices[0].message.content
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"OpenAI API调用失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                
                # 特殊处理429错误（速率限制）
                if "429" in error_msg or "Too Many Requests" in error_msg:
                    wait_time = (2 ** attempt) * 5  # 指数退避，最少5秒
                    logger.info(f"遇到速率限制，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                elif attempt < self.max_retries - 1:
                    # 其他错误使用基础延迟
                    time.sleep(self.base_delay * (2 ** attempt))
                else:
                    raise
        
        # 如果所有重试都失败了，抛出异常
        raise Exception(f"OpenAI API调用失败，已重试 {self.max_retries} 次")
    
    def _wait_for_rate_limit(self):
        """等待速率限制"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        # 增加请求间隔到2秒，避免429错误
        min_interval = max(self.request_interval, 2.0)
        
        if time_since_last_request < min_interval:
            sleep_time = min_interval - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """解析AI响应（量化分数版）"""
        try:
            # 尝试直接解析JSON
            if response.strip().startswith('{'):
                result = json.loads(response)
            else:
                # 尝试提取JSON部分
                start_idx = response.find('{')
                end_idx = response.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = response[start_idx:end_idx]
                    result = json.loads(json_str)
                else:
                    logger.warning(f"无法解析AI响应: {response}")
                    return self._get_default_analysis_data()
            # 兼容旧格式
            code_quality_score = result.get('code_quality_score')
            complexity_score = result.get('complexity_score')
            effort_score = result.get('effort_score')
            # 若AI未返回分数，降级为默认
            if code_quality_score is None or complexity_score is None or effort_score is None:
                logger.warning(f"AI未返回量化分数，降级为默认: {result}")
                return self._get_default_analysis_data()
            # 保证分数在0~100
            code_quality_score = max(0, min(100, float(code_quality_score)))
            complexity_score = max(0, min(100, float(complexity_score)))
            effort_score = max(0, min(100, float(effort_score)))
            result['code_quality_score'] = code_quality_score
            result['complexity_score'] = complexity_score
            result['effort_score'] = effort_score
            
            # 从量化分数推导枚举值
            if code_quality_score >= 85:
                result['code_quality'] = CodeQuality.EXCELLENT
            elif code_quality_score >= 70:
                result['code_quality'] = CodeQuality.GOOD
            elif code_quality_score >= 50:
                result['code_quality'] = CodeQuality.MEDIUM
            else:
                result['code_quality'] = CodeQuality.POOR
            
            if complexity_score >= 80:
                result['complexity'] = Complexity.HIGH
            elif complexity_score >= 40:
                result['complexity'] = Complexity.MEDIUM
            else:
                result['complexity'] = Complexity.LOW
            
            if effort_score >= 80:
                result['effort'] = Effort.HARD
            elif effort_score >= 40:
                result['effort'] = Effort.MEDIUM
            else:
                result['effort'] = Effort.EASY
            
            return result
        except Exception as e:
            logger.error(f"解析AI响应失败: {e}")
            return self._get_default_analysis_data()
    
    def _calculate_score(self, analysis_result: Dict[str, Any]) -> float:
        """综合评分等于三个量化分数的平均值"""
        code_quality_score = analysis_result.get('code_quality_score', 60)
        complexity_score = analysis_result.get('complexity_score', 50)
        effort_score = analysis_result.get('effort_score', 50)
        score = (code_quality_score + complexity_score + effort_score) / 3
        return round(score, 1)
    
    def _get_default_analysis(self, commit_info: Dict[str, Any]) -> CodeAnalysis:
        """获取默认分析结果（量化分数版）"""
        return CodeAnalysis(
            commit_hash=commit_info.get('hash', 'unknown'),
            complexity=Complexity.MEDIUM,
            code_quality=CodeQuality.MEDIUM,
            effort=Effort.MEDIUM,
            summary=["无法完成AI分析，使用默认评估"],
            analysis=["由于技术原因，无法获取详细分析"],
            advice=["建议手动审查代码质量"],
            reasoning={
                "complexity": "默认中等复杂度",
                "code_quality": "默认中等质量",
                "effort": "默认中等工作量"
            },
            score=0.6
        )
    
    def _get_default_analysis_data(self) -> Dict[str, Any]:
        """获取默认分析数据"""
        return {
            "complexity": "medium",
            "code_quality": "medium",
            "effort": "medium",
            "summary": ["使用默认分析结果"],
            "analysis": ["无法获取详细分析"],
            "advice": ["建议手动审查"],
            "reasoning": {
                "complexity": "默认中等复杂度",
                "code_quality": "默认中等质量",
                "effort": "默认中等工作量"
            }
        }
    
    def batch_analyze_commits(self, commits_data: List[Dict[str, Any]]) -> List[CodeAnalysis]:
        """批量分析提交"""
        results = []
        
        for i, commit_data in enumerate(commits_data):
            try:
                commit_hash = commit_data['commit_info'].get('hash', 'unknown')
                logger.info(f"分析提交 {i+1}/{len(commits_data)}: {commit_hash}")
                
                analysis = self.analyze_commit(
                    commit_data['commit_info'],
                    commit_data['diff_content']
                )
                results.append(analysis)
                
            except Exception as e:
                commit_hash = commit_data['commit_info'].get('hash', 'unknown')
                logger.error(f"批量分析失败 {commit_hash}: {e}")
                # 添加默认分析结果
                default_analysis = self._get_default_analysis(commit_data['commit_info'])
                results.append(default_analysis)
        
        return results


class AnalysisManager:
    """分析管理器"""
    
    def __init__(self, cache_dir: str = "cache/ai_analysis"):
        self.ai_analyzer = AIAnalyzer(cache_dir=cache_dir)
    
    def analyze_repository_commits(self, commits_info: List[Dict[str, Any]], 
                                 diffs_content: Dict[str, str]) -> List[CodeAnalysis]:
        """分析仓库提交"""
        commits_data = []
        
        for commit_info in commits_info:
            commit_hash = commit_info.get('hash', 'unknown')
            diff_content = diffs_content.get(commit_hash, '')
            
            commits_data.append({
                'commit_info': commit_info,
                'diff_content': diff_content
            })
        
        return self.ai_analyzer.batch_analyze_commits(commits_data)
    
    def get_analysis_summary(self, analyses: List[CodeAnalysis]) -> Dict[str, Any]:
        """获取分析摘要"""
        if not analyses:
            return {}
        
        # 统计各项指标
        complexity_counts = {}
        quality_counts = {}
        effort_counts = {}
        total_score = 0
        
        for analysis in analyses:
            # 复杂度统计
            complexity = analysis.complexity.value
            complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1
            
            # 质量统计
            quality = analysis.code_quality.value
            quality_counts[quality] = quality_counts.get(quality, 0) + 1
            
            # 工作量统计
            effort = analysis.effort.value
            effort_counts[effort] = effort_counts.get(effort, 0) + 1
            
            # 总分
            total_score += analysis.score
        
        # 计算百分比
        total_count = len(analyses)
        complexity_percentages = {
            k: round((v / total_count) * 100, 2) 
            for k, v in complexity_counts.items()
        }
        quality_percentages = {
            k: round((v / total_count) * 100, 2) 
            for k, v in quality_counts.items()
        }
        effort_percentages = {
            k: round((v / total_count) * 100, 2) 
            for k, v in effort_counts.items()
        }
        
        return {
            'total_commits': total_count,
            'average_score': round(total_score / total_count, 2),
            'complexity_distribution': complexity_percentages,
            'quality_distribution': quality_percentages,
            'effort_distribution': effort_percentages,
            'score_range': {
                'min': min(a.score for a in analyses),
                'max': max(a.score for a in analyses),
                'median': sorted([a.score for a in analyses])[total_count // 2]
            }
        } 