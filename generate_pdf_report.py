#!/usr/bin/env python3
"""
PDF报告生成器
Generate PDF reports from JSON analysis results
"""

import os
import json
import sys
import platform
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
except ImportError:
    print("❌ 缺少reportlab依赖，请安装：pip install reportlab")
    sys.exit(1)


class PDFReportGenerator:
    """PDF报告生成器"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_chinese_fonts()
        self._setup_styles()
    
    def _setup_chinese_fonts(self):
        """设置中文字体"""
        try:
            # 尝试注册系统中文字体
            system = platform.system()
            
            if system == "Darwin":  # macOS
                # macOS 中文字体路径
                chinese_fonts = [
                    "/System/Library/Fonts/PingFang.ttc",
                    "/System/Library/Fonts/STHeiti Light.ttc",
                    "/System/Library/Fonts/STHeiti Medium.ttc",
                    "/Library/Fonts/Arial Unicode MS.ttf",
                    "/System/Library/Fonts/Helvetica.ttc"
                ]
            elif system == "Windows":
                # Windows 中文字体路径
                chinese_fonts = [
                    "C:/Windows/Fonts/simsun.ttc",
                    "C:/Windows/Fonts/simhei.ttf",
                    "C:/Windows/Fonts/msyh.ttc",
                    "C:/Windows/Fonts/arial.ttf"
                ]
            else:  # Linux
                # Linux 中文字体路径
                chinese_fonts = [
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
                ]
            
            # 尝试注册字体
            font_registered = False
            for font_path in chinese_fonts:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                        font_registered = True
                        print(f"✅ 成功注册中文字体: {font_path}")
                        break
                    except Exception as e:
                        print(f"⚠️ 注册字体失败 {font_path}: {e}")
                        continue
            
            if not font_registered:
                # 使用UnicodeCIDFont作为fallback
                pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
                print("✅ 使用UnicodeCIDFont作为中文字体")
                self.chinese_font = 'STSong-Light'
            else:
                self.chinese_font = 'ChineseFont'
                
        except Exception as e:
            print(f"⚠️ 字体设置失败: {e}")
            # 使用默认字体
            self.chinese_font = 'Helvetica'
    
    def _setup_styles(self):
        """设置样式"""
        # 标题样式
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue,
            fontName=self.chinese_font
        ))
        
        # 副标题样式
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            textColor=colors.darkblue,
            fontName=self.chinese_font
        ))
        
        # 正文样式
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=12,
            alignment=TA_LEFT,
            fontName=self.chinese_font
        ))
        
        # 强调样式
        self.styles.add(ParagraphStyle(
            name='CustomEmphasis',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            textColor=colors.darkred,
            alignment=TA_LEFT,
            fontName=self.chinese_font
        ))
    
    def generate_pdf_report(self, json_report_path: str, output_path: str = None):
        """生成PDF报告"""
        # 读取JSON报告
        with open(json_report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        # 确定输出路径
        if output_path is None:
            base_name = Path(json_report_path).stem
            output_path = f"analysis_results/reports/{base_name}.pdf"
        
        # 创建PDF文档
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # 构建PDF内容
        story = []
        
        # 添加标题页
        story.extend(self._create_title_page(report_data))
        story.append(PageBreak())
        
        # 添加执行摘要
        story.extend(self._create_executive_summary(report_data))
        story.append(PageBreak())
        
        # 添加详细分析
        story.extend(self._create_detailed_analysis(report_data))
        story.append(PageBreak())
        
        # 添加员工绩效详情
        story.extend(self._create_employee_details(report_data))
        story.append(PageBreak())
        
        # 添加改进建议
        story.extend(self._create_recommendations(report_data))
        
        # 生成PDF
        doc.build(story)
        print(f"✅ PDF报告已生成: {output_path}")
        return output_path
    
    def _create_title_page(self, report_data: Dict[str, Any]) -> List:
        """创建标题页"""
        story = []
        
        # 主标题
        title = Paragraph("多仓库代码效率评估报告", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 50))
        
        # 报告信息
        eval_result = report_data['evaluation_result']
        info_data = [
            ['报告ID', eval_result['evaluation_id']],
            ['评估名称', eval_result['evaluation_name']],
            ['评估周期', eval_result['evaluation_period']],
            ['开始时间', eval_result['start_date'][:10]],
            ['结束时间', eval_result['end_date'][:10]],
            ['仓库数量', str(eval_result['total_repositories'])],
            ['员工数量', str(eval_result['total_employees'])],
            ['团队评分', f"{eval_result['overall_team_score']:.2f}/1.0"],
            ['生成时间', report_data['generated_at'][:19]]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 30))
        
        return story
    
    def _create_executive_summary(self, report_data: Dict[str, Any]) -> List:
        """创建执行摘要"""
        story = []
        
        # 标题
        title = Paragraph("执行摘要", self.styles['CustomSubtitle'])
        story.append(title)
        story.append(Spacer(1, 20))
        
        # 摘要内容
        summary = Paragraph(report_data['summary'], self.styles['CustomBody'])
        story.append(summary)
        story.append(Spacer(1, 20))
        
        # 关键发现
        title2 = Paragraph("关键发现", self.styles['CustomSubtitle'])
        story.append(title2)
        story.append(Spacer(1, 10))
        
        for i, finding in enumerate(report_data['key_findings'], 1):
            finding_text = f"{i}. {finding}"
            finding_para = Paragraph(finding_text, self.styles['CustomBody'])
            story.append(finding_para)
        
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_detailed_analysis(self, report_data: Dict[str, Any]) -> List:
        """创建详细分析"""
        story = []
        
        # 标题
        title = Paragraph("详细分析", self.styles['CustomSubtitle'])
        story.append(title)
        story.append(Spacer(1, 20))
        
        eval_result = report_data['evaluation_result']
        
        # 仓库分析
        repo_title = Paragraph("仓库分析", self.styles['CustomSubtitle'])
        story.append(repo_title)
        story.append(Spacer(1, 10))
        
        repo_data = [['仓库名称', '提交数', '贡献者', '代码质量', '活跃度']]
        for repo_name, repo_info in eval_result['repositories'].items():
            repo_data.append([
                repo_name,
                str(repo_info['total_commits']),
                str(repo_info['total_contributors']),
                f"{repo_info['average_code_quality']:.2f}",
                f"{repo_info['commits_per_day']:.2f}/天"
            ])
        
        repo_table = Table(repo_data, colWidths=[1.5*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
        repo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), self.chinese_font),
            ('FONTNAME', (0, 1), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(repo_table)
        story.append(Spacer(1, 20))
        
        # 绩效分布
        perf_title = Paragraph("员工绩效分布", self.styles['CustomSubtitle'])
        story.append(perf_title)
        story.append(Spacer(1, 10))
        
        performance_counts = {}
        for emp in eval_result['employees'].values():
            performance_counts[emp['performance_level']] = performance_counts.get(emp['performance_level'], 0) + 1
        
        perf_data = [['绩效等级', '人数', '占比']]
        level_names = {
            'excellent': '优秀',
            'good': '良好',
            'average': '一般',
            'below_average': '低于平均',
            'poor': '较差'
        }
        
        total_employees = eval_result['total_employees']
        for level in ['excellent', 'good', 'average', 'below_average', 'poor']:
            count = performance_counts.get(level, 0)
            if count > 0:
                percentage = (count / total_employees) * 100
                perf_data.append([
                    level_names.get(level, level),
                    str(count),
                    f"{percentage:.1f}%"
                ])
        
        perf_table = Table(perf_data, colWidths=[1.5*inch, 0.8*inch, 0.8*inch])
        perf_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), self.chinese_font),
            ('FONTNAME', (0, 1), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(perf_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_employee_details(self, report_data: Dict[str, Any]) -> List:
        """创建员工详情"""
        story = []
        
        # 标题
        title = Paragraph("员工绩效详情", self.styles['CustomSubtitle'])
        story.append(title)
        story.append(Spacer(1, 20))
        
        eval_result = report_data['evaluation_result']
        
        # 按评分排序员工
        employees = list(eval_result['employees'].values())
        employees.sort(key=lambda x: x['overall_score'], reverse=True)
        
        # 员工详情表格
        emp_data = [['员工姓名', '总体评分', '代码质量', '生产力', '绩效等级']]
        
        for emp in employees:
            emp_data.append([
                emp['employee_name'],
                f"{emp['overall_score']:.2f}",
                f"{emp['average_code_quality_score']:.2f}",
                f"{emp['commits_per_day']:.2f}/天",
                emp['performance_level']
            ])
        
        emp_table = Table(emp_data, colWidths=[1.2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1.2*inch])
        emp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightyellow),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), self.chinese_font),
            ('FONTNAME', (0, 1), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(emp_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_recommendations(self, report_data: Dict[str, Any]) -> List:
        """创建改进建议"""
        story = []
        
        # 标题
        title = Paragraph("改进建议", self.styles['CustomSubtitle'])
        story.append(title)
        story.append(Spacer(1, 20))
        
        # 建议列表
        for i, recommendation in enumerate(report_data['recommendations'], 1):
            rec_text = f"{i}. {recommendation}"
            rec_para = Paragraph(rec_text, self.styles['CustomBody'])
            story.append(rec_para)
            story.append(Spacer(1, 8))
        
        story.append(Spacer(1, 20))
        
        # 结束语
        conclusion = Paragraph(
            "本报告基于代码提交历史、AI分析结果和团队协作数据生成。"
            "建议定期进行此类评估，持续改进团队开发效率和代码质量。",
            self.styles['CustomEmphasis']
        )
        story.append(conclusion)
        
        return story


def main():
    """主函数"""
    # 查找最新的JSON报告
    reports_dir = "analysis_results/reports"
    json_files = list(Path(reports_dir).glob("efficiency_report_*.json"))
    
    if not json_files:
        print("❌ 未找到JSON报告文件")
        print("请先运行主程序生成分析报告：python main.py")
        return
    
    # 使用最新的报告
    latest_report = max(json_files, key=lambda x: x.stat().st_mtime)
    print(f"📄 使用报告文件: {latest_report}")
    
    # 生成PDF
    generator = PDFReportGenerator()
    pdf_path = generator.generate_pdf_report(str(latest_report))
    
    print(f"\n🎉 PDF报告生成完成！")
    print(f"📁 文件位置: {pdf_path}")
    print(f"📏 文件大小: {os.path.getsize(pdf_path) / 1024:.1f} KB")


if __name__ == "__main__":
    main() 