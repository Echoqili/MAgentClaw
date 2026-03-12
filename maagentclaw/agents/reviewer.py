"""
审核员Agent (Reviewer Agent)

负责内容审核、质量评估、合规性检查和准确性验证
参考"三郡六县制"：如同古代的监察制度，审核员Agent是系统的"御史大夫"
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re


class ReviewCategory(Enum):
    """审核类别"""
    QUALITY = "quality"           # 质量评估
    COMPLIANCE = "compliance"    # 合规性检查
    ACCURACY = "accuracy"        # 准确性验证
    SAFETY = "safety"            # 安全性检查
    STYLE = "style"             # 风格检查
    COMPLETENESS = "completeness"  # 完整性检查


class ReviewResult(Enum):
    """审核结果"""
    APPROVED = "approved"         # 通过
    REJECTED = "rejected"        # 拒绝
    NEEDS_REVISION = "needs_revision"  # 需要修改
    CONDITIONAL = "conditional"   # 有条件通过
    PENDING = "pending"          # 待审核


class Severity(Enum):
    """严重程度"""
    CRITICAL = "critical"       # 严重
    HIGH = "high"              # 高
    MEDIUM = "medium"          # 中
    LOW = "low"                # 低
    INFO = "info"              # 信息


@dataclass
class ReviewIssue:
    """审核问题"""
    category: ReviewCategory
    severity: Severity
    description: str
    location: Optional[str] = None  # 问题位置
    suggestion: Optional[str] = None  # 建议
    evidence: Optional[str] = None   # 证据


@dataclass
class ReviewReport:
    """审核报告"""
    content_id: str = ""
    reviewer: str = "Reviewer Agent"
    result: ReviewResult = ReviewResult.PENDING
    score: float = 0.0  # 0-100 分
    
    issues: List[ReviewIssue] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    
    reviewed_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReviewerConfig:
    """审核员配置"""
    name: str = "reviewer"
    role: str = "内容审核员"
    
    # 审核规则
    quality_threshold: float = 70.0    # 质量阈值
    compliance_required: bool = True   # 是否必须合规
    accuracy_check_enabled: bool = True  # 准确性检查
    
    # 敏感词过滤
    sensitive_words: List[str] = field(default_factory=list)
    blocked_patterns: List[str] = field(default_factory=list)
    
    # 检查项
    check_spelling: bool = True
    check_grammar: bool = True
    check_plagiarism: bool = False
    check_factuality: bool = True
    
    # 评分权重
    quality_weight: float = 0.4
    compliance_weight: float = 0.3
    accuracy_weight: float = 0.2
    style_weight: float = 0.1
    
    # 角色定义（增强版）
    goal: str = "确保内容质量、合规性和准确性"
    backstory: str = """你是一位资深内容审核专家，拥有多年内容审核经验。
    你精通各类内容审核标准，熟悉法律法规要求，
    能够准确识别内容中的问题，并提供建设性的改进建议。"""
    responsibilities: List[str] = field(default_factory=lambda: [
        "审核内容质量",
        "检查合规性",
        "验证准确性",
        "识别安全问题",
        "提供改进建议"
    ])


class ReviewerAgent:
    """审核员Agent
    
    如同古代的"御史大夫"，负责监察百官、审核奏章
    审核员Agent负责审核系统中所有Agent生成的内容
    """
    
    def __init__(self, config: Optional[ReviewerConfig] = None):
        self.config = config or ReviewerConfig()
        self.review_history: List[ReviewReport] = []
    
    async def initialize(self) -> bool:
        """初始化审核员"""
        return True
    
    async def review(
        self,
        content: str,
        content_id: str = "",
        context: Optional[Dict[str, Any]] = None
    ) -> ReviewReport:
        """审核内容"""
        report = ReviewReport(
            content_id=content_id,
            reviewer=self.config.name
        )
        
        # 1. 质量评估
        if self.config.quality_weight > 0:
            quality_score = self._assess_quality(content)
            report.issues.extend(self._find_quality_issues(content))
        
        # 2. 合规性检查
        if self.config.compliance_required:
            compliance_issues = self._check_compliance(content)
            report.issues.extend(compliance_issues)
        
        # 3. 准确性验证
        if self.config.accuracy_check_enabled:
            accuracy_issues = self._verify_accuracy(content, context)
            report.issues.extend(accuracy_issues)
        
        # 4. 安全性检查
        safety_issues = self._check_safety(content)
        report.issues.extend(safety_issues)
        
        # 计算总分
        report.score = self._calculate_score(report)
        
        # 确定审核结果
        report.result = self._determine_result(report)
        
        # 提取优点
        report.strengths = self._extract_strengths(content, report)
        
        # 生成建议
        report.suggestions = self._generate_suggestions(report)
        
        # 保存到历史
        self.review_history.append(report)
        
        return report
    
    def _assess_quality(self, content: str) -> float:
        """评估内容质量"""
        score = 100.0
        
        # 检查长度
        if len(content) < 50:
            score -= 20
        elif len(content) < 100:
            score -= 10
        
        # 检查是否包含基本结构
        if not content.strip():
            score -= 50
        
        # 检查重复
        words = content.split()
        if len(words) > 10:
            unique_ratio = len(set(words)) / len(words)
            score -= (1 - unique_ratio) * 20
        
        return max(0, score)
    
    def _find_quality_issues(self, content: str) -> List[ReviewIssue]:
        """查找质量问题"""
        issues = []
        
        if self.config.check_spelling:
            # 简单的拼写检查（示例）
            if "　" in content:  # 全角空格
                issues.append(ReviewIssue(
                    category=ReviewCategory.QUALITY,
                    severity=Severity.LOW,
                    description="检测到全角空格",
                    suggestion="建议使用半角空格"
                ))
        
        if self.config.check_grammar:
            # 简单的语法检查
            if content.endswith("。") and len(content) > 100:
                # 检查是否有句子太长
                sentences = content.split("。")
                for i, sent in enumerate(sentences):
                    if len(sent) > 100:
                        issues.append(ReviewIssue(
                            category=ReviewCategory.QUALITY,
                            severity=Severity.MEDIUM,
                            description=f"第{i+1}个句子过长",
                            suggestion="建议拆分长句"
                        ))
        
        return issues
    
    def _check_compliance(self, content: str) -> List[ReviewIssue]:
        """合规性检查"""
        issues = []
        
        # 敏感词检查
        for word in self.config.sensitive_words:
            if word in content:
                issues.append(ReviewIssue(
                    category=ReviewCategory.COMPLIANCE,
                    severity=Severity.CRITICAL,
                    description=f"检测到敏感词: {word}",
                    suggestion="请移除敏感词"
                ))
        
        # 模式匹配检查
        for pattern in self.config.blocked_patterns:
            if re.search(pattern, content):
                issues.append(ReviewIssue(
                    category=ReviewCategory.COMPLIANCE,
                    severity=Severity.HIGH,
                    description=f"检测到违规模式: {pattern}",
                    suggestion="请修改相关内容"
                ))
        
        return issues
    
    def _verify_accuracy(
        self,
        content: str,
        context: Optional[Dict[str, Any]]
    ) -> List[ReviewIssue]:
        """准确性验证"""
        issues = []
        
        if not context:
            return issues
        
        # 检查与事实的一致性
        facts = context.get("facts", [])
        for fact in facts:
            if "expected" in fact and "actual" in fact:
                if fact["expected"] != fact["actual"]:
                    issues.append(ReviewIssue(
                        category=ReviewCategory.ACCURACY,
                        severity=Severity.HIGH,
                        description=f"内容与预期不符: {fact.get('description', '')}",
                        suggestion=fact.get("correction", "请核实并修正")
                    ))
        
        # 检查数据一致性
        data = context.get("data", {})
        if data:
            # 示例：检查数值是否在合理范围内
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    if "range" in context:
                        range_info = context["range"].get(key, {})
                        if "min" in range_info and value < range_info["min"]:
                            issues.append(ReviewIssue(
                                category=ReviewCategory.ACCURACY,
                                severity=Severity.MEDIUM,
                                description=f"数值 {key}={value} 低于最小值 {range_info['min']}",
                                suggestion=f"请检查并调整数值"
                            ))
        
        return issues
    
    def _check_safety(self, content: str) -> List[ReviewIssue]:
        """安全性检查"""
        issues = []
        
        # 检查潜在的不安全内容
        danger_patterns = [
            (r"<script", "检测到潜在 XSS 攻击向量"),
            (r"javascript:", "检测到 JavaScript 协议"),
            (r"on\w+=", "检测到事件处理器"),
        ]
        
        for pattern, desc in danger_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(ReviewIssue(
                    category=ReviewCategory.SAFETY,
                    severity=Severity.CRITICAL,
                    description=desc,
                    suggestion="请移除不安全的内容"
                ))
        
        return issues
    
    def _calculate_score(self, report: ReviewReport) -> float:
        """计算总分"""
        score = 100.0
        
        # 根据问题扣分
        for issue in report.issues:
            if issue.severity == Severity.CRITICAL:
                score -= 30
            elif issue.severity == Severity.HIGH:
                score -= 20
            elif issue.severity == Severity.MEDIUM:
                score -= 10
            elif issue.severity == Severity.LOW:
                score -= 5
        
        return max(0, min(100, score))
    
    def _determine_result(self, report: ReviewReport) -> ReviewResult:
        """确定审核结果"""
        # 有严重问题
        critical_issues = [i for i in report.issues if i.severity == Severity.CRITICAL]
        if critical_issues:
            return ReviewResult.REJECTED
        
        # 有高优先级问题
        high_issues = [i for i in report.issues if i.severity == Severity.HIGH]
        if high_issues:
            return ReviewResult.NEEDS_REVISION
        
        # 分数低于阈值
        if report.score < self.config.quality_threshold:
            return ReviewResult.NEEDS_REVISION
        
        # 有中优先级问题
        medium_issues = [i for i in report.issues if i.severity == Severity.MEDIUM]
        if medium_issues:
            return ReviewResult.CONDITIONAL
        
        # 通过
        return ReviewResult.APPROVED
    
    def _extract_strengths(
        self,
        content: str,
        report: ReviewReport
    ) -> List[str]:
        """提取优点"""
        strengths = []
        
        if len(content) > 200:
            strengths.append("内容详尽")
        
        if report.score >= 90:
            strengths.append("整体质量优秀")
        
        if "。" in content and "，" in content:
            strengths.append("标点使用规范")
        
        return strengths
    
    def _generate_suggestions(self, report: ReviewReport) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        for issue in report.issues:
            if issue.suggestion:
                suggestions.append(issue.suggestion)
        
        # 添加总体建议
        if report.score < 60:
            suggestions.append("建议全面重写内容")
        elif report.score < 80:
            suggestions.append("建议针对问题进行修改")
        
        return suggestions
    
    async def batch_review(
        self,
        contents: List[Dict[str, str]]
    ) -> List[ReviewReport]:
        """批量审核"""
        reports = []
        
        for item in contents:
            content = item.get("content", "")
            content_id = item.get("id", "")
            context = item.get("context")
            
            report = await self.review(content, content_id, context)
            reports.append(report)
        
        return reports
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取审核统计"""
        if not self.review_history:
            return {"total": 0}
        
        return {
            "total": len(self.review_history),
            "approved": len([r for r in self.review_history if r.result == ReviewResult.APPROVED]),
            "rejected": len([r for r in self.review_history if r.result == ReviewResult.REJECTED]),
            "needs_revision": len([r for r in self.review_history if r.result == ReviewResult.NEEDS_REVISION]),
            "avg_score": sum(r.score for r in self.review_history) / len(self.review_history),
            "issues_by_category": self._count_by_category(),
            "issues_by_severity": self._count_by_severity()
        }
    
    def _count_by_category(self) -> Dict[str, int]:
        """按类别统计问题"""
        counts = {cat.value: 0 for cat in ReviewCategory}
        for report in self.review_history:
            for issue in report.issues:
                counts[issue.category.value] += 1
        return counts
    
    def _count_by_severity(self) -> Dict[str, int]:
        """按严重程度统计问题"""
        counts = {sev.value: 0 for sev in Severity}
        for report in self.review_history:
            for issue in report.issues:
                counts[issue.severity.value] += 1
        return counts
