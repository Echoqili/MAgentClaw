"""
输入过滤器 - 防止Prompt注入攻击

参考OpenClaw安全设计的第一层防护
"""

from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import re
import html


class FilterLevel(Enum):
    """过滤级别"""
    ALLOW = "allow"       # 允许
    WARN = "warn"        # 警告但允许
    BLOCK = "block"      # 阻止


@dataclass
class FilterResult:
    """过滤结果"""
    allowed: bool
    level: FilterLevel
    matched_patterns: List[str] = field(default_factory=list)
    sanitized_input: str = ""
    warnings: List[str] = field(default_factory=list)
    
    def __str__(self):
        if self.allowed:
            return f"Allowed (level: {self.level.value})"
        return f"Blocked - patterns: {self.matched_patterns}"


class InputFilter:
    """输入过滤器
    
    检测并阻止Prompt注入攻击
    """
    
    INJECTION_PATTERNS = [
        r"(?i)(ignore\s+(all\s+)?(previous|prior|above)\s+instructions)",
        r"(?i)(disregard\s+(all\s+)?(previous|prior|above)\s+rules)",
        r"(?i)(forget\s+(all\s+)?(your|everything\s+you\s+know))",
        r"(?i)(you\s+are\s+(now|no\s+longer|just|only)\s+a\s+(AI|model|assistant))",
        r"(?i)(system\s*:\s*|system\s*>)",
        r"(?i)(human\s*:\s*|human\s*>)",
        r"(?i)(assistant\s*:\s*|assistant\s*>)",
        r"(?i)(\\{.*\\}|\\[.*\\])",
        r"(?i)(\<.*\>.*\<\/.*\>)",
        r"(?i)(new\s+instruction(s)?|override|overwrite)",
        r"(?i)(role\s*=\s*|act\s+as\s+|pretend\s+(to\s+be|you\s+are))",
        r"(?i)(\`\`\`.*\`\`\`)",
        r"(?i)(jailbreak|hack|exploit|malicious)",
    ]
    
    DANGEROUS_COMMANDS = [
        r"rm\s+-rf",
        r"del\s+/[fq]",
        r"format\s+[a-z]:",
        r"shutdown",
        r"reboot",
        r"kill\s+-9",
        r"curl.*\|.*sh",
        r"wget.*\|.*sh",
    ]
    
    SENSITIVE_PATTERNS = [
        r"(?i)(password|passwd|pwd)\s*[:=]",
        r"(?i)(api[_-]?key|secret|token)\s*[:=]",
        r"(?i)(ssh[_-]?key|private[_-]?key)",
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    ]
    
    def __init__(
        self,
        block_on_injection: bool = True,
        block_on_dangerous: bool = True,
        warn_on_sensitive: bool = True,
        custom_patterns: Optional[List[str]] = None
    ):
        self.block_on_injection = block_on_injection
        self.block_on_dangerous = block_on_dangerous
        self.warn_on_sensitive = warn_on_sensitive
        
        self._injection_patterns = [
            re.compile(p, re.IGNORECASE) 
            for p in self.INJECTION_PATTERNS
        ]
        self._dangerous_patterns = [
            re.compile(p, re.IGNORECASE) 
            for p in self.DANGEROUS_COMMANDS
        ]
        self._sensitive_patterns = [
            re.compile(p, re.IGNORECASE) 
            for p in self.SENSITIVE_PATTERNS
        ]
        
        if custom_patterns:
            self._custom_patterns = [
                re.compile(p, re.IGNORECASE) 
                for p in custom_patterns
            ]
        else:
            self._custom_patterns = []
    
    def filter(self, input_text: str) -> FilterResult:
        """过滤输入"""
        matched_patterns: List[str] = []
        warnings: List[str] = []
        
        sanitized = self._sanitize(input_text)
        
        for i, pattern in enumerate(self._injection_patterns):
            if pattern.search(input_text):
                matched_patterns.append(f"injection_{i}")
                if self.block_on_injection:
                    return FilterResult(
                        allowed=False,
                        level=FilterLevel.BLOCK,
                        matched_patterns=matched_patterns,
                        sanitized_input=sanitized,
                        warnings=["Potential prompt injection detected"]
                    )
                warnings.append("Potential prompt injection detected")
        
        for i, pattern in enumerate(self._dangerous_patterns):
            if pattern.search(input_text):
                matched_patterns.append(f"dangerous_{i}")
                if self.block_on_dangerous:
                    return FilterResult(
                        allowed=False,
                        level=FilterLevel.BLOCK,
                        matched_patterns=matched_patterns,
                        sanitized_input=sanitized,
                        warnings=["Dangerous command detected"]
                    )
                warnings.append("Dangerous command detected")
        
        sensitive_found = []
        for i, pattern in enumerate(self._sensitive_patterns):
            matches = pattern.findall(input_text)
            if matches:
                sensitive_found.append(f"sensitive_{i}")
        
        if sensitive_found:
            if self.warn_on_sensitive:
                warnings.append("Sensitive data pattern detected")
            matched_patterns.extend(sensitive_found)
        
        for i, pattern in enumerate(self._custom_patterns):
            if pattern.search(input_text):
                matched_patterns.append(f"custom_{i}")
        
        if matched_patterns and warnings:
            return FilterResult(
                allowed=True,
                level=FilterLevel.WARN,
                matched_patterns=matched_patterns,
                sanitized_input=sanitized,
                warnings=warnings
            )
        
        return FilterResult(
            allowed=True,
            level=FilterLevel.ALLOW,
            sanitized_input=sanitized
        )
    
    def _sanitize(self, input_text: str) -> str:
        """清理输入"""
        sanitized = input_text
        sanitized = html.escape(sanitized)
        sanitized = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', sanitized)
        return sanitized
    
    def add_pattern(self, pattern: str, pattern_type: str = "custom"):
        """添加自定义模式"""
        compiled = re.compile(pattern, re.IGNORECASE)
        if pattern_type == "injection":
            self._injection_patterns.append(compiled)
        elif pattern_type == "dangerous":
            self._dangerous_patterns.append(compiled)
        elif pattern_type == "sensitive":
            self._sensitive_patterns.append(compiled)
        else:
            self._custom_patterns.append(compiled)
    
    def get_statistics(self) -> Dict:
        return {
            "injection_patterns": len(self._injection_patterns),
            "dangerous_patterns": len(self._dangerous_patterns),
            "sensitive_patterns": len(self._sensitive_patterns),
            "custom_patterns": len(self._custom_patterns),
            "block_on_injection": self.block_on_injection,
            "block_on_dangerous": self.block_on_dangerous,
        }
