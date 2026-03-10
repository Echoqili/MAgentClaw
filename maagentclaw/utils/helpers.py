"""
工具函数模块
提供通用工具函数和辅助功能
"""

import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
import functools
import traceback


def setup_logger(name: str, log_dir: str = "logs", level: str = "INFO") -> logging.Logger:
    """设置日志记录器"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # 文件处理器
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_handler = logging.FileHandler(
        log_path / f"{name}_{timestamp}.log",
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 格式化器
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def async_retry(max_retries: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """异步重试装饰器"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


def sync_retry(max_retries: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """同步重试装饰器"""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


def async_timeout(timeout_seconds: float = 30.0):
    """异步超时装饰器"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                raise TimeoutError(f"Function {func.__name__} timed out after {timeout_seconds}s")
        return wrapper
    return decorator


def measure_time(func: Callable):
    """测量执行时间的装饰器"""
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        import time
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            end = time.time()
            print(f"{func.__name__} executed in {end - start:.4f}s")
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        import time
        start = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end = time.time()
            print(f"{func.__name__} executed in {end - start:.4f}s")
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


def safe_execute(default: Any = None, on_error: Optional[Callable] = None):
    """安全执行装饰器，捕获所有异常"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if on_error:
                    on_error(e)
                return default
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if on_error:
                    on_error(e)
                return default
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


def format_exception(e: Exception) -> str:
    """格式化异常信息"""
    return f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"


def ensure_dir(path: str) -> Path:
    """确保目录存在"""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """截断文本"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def parse_json_safe(text: str) -> Optional[Dict]:
    """安全解析 JSON"""
    import json
    try:
        return json.loads(text)
    except:
        return None


def merge_dicts(base: Dict, updates: Dict) -> Dict:
    """深度合并字典"""
    result = base.copy()
    for key, value in updates.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def generate_id(prefix: str = "") -> str:
    """生成唯一 ID"""
    import uuid
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}{timestamp}_{unique_id}" if prefix else f"{timestamp}_{unique_id}"
