"""
Browser Automation - 浏览器自动化模块

自动操作网页：元素识别、交互、截图等
"""

import asyncio
import base64
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class ElementSelectorType(Enum):
    """元素选择器类型"""
    ID = "id"
    CSS = "css"
    XPATH = "xpath"
    TEXT = "text"
    NAME = "name"


class ActionType(Enum):
    """操作类型"""
    CLICK = "click"
    INPUT = "input"
    SELECT = "select"
    HOVER = "hover"
    SCROLL = "scroll"
    WAIT = "wait"
    NAVIGATE = "navigate"
    Screenshot = "screenshot"


@dataclass
class ElementSelector:
    """元素选择器"""
    type: ElementSelectorType
    value: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.type.value, "value": self.value}


@dataclass
class BrowserAction:
    """浏览器操作"""
    action: ActionType
    selector: Optional[ElementSelector] = None
    value: Optional[str] = None
    timeout: int = 30
    wait_for: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action.value,
            "selector": self.selector.to_dict() if self.selector else None,
            "value": self.value,
            "timeout": self.timeout,
            "wait_for": self.wait_for
        }


@dataclass
class PageElement:
    """页面元素"""
    tag: str
    text: str
    attributes: Dict[str, str]
    selector: ElementSelector
    bounding_box: Optional[Dict[str, int]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tag": self.tag,
            "text": self.text,
            "attributes": self.attributes,
            "selector": self.selector.to_dict(),
            "bounding_box": self.bounding_box
        }


@dataclass
class BrowserResult:
    """浏览器操作结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    screenshot: Optional[str] = None  # base64
    elements: List[PageElement] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "screenshot": self.screenshot,
            "elements": [e.to_dict() for e in self.elements],
            "metadata": self.metadata
        }


class BrowserAutomation:
    """浏览器自动化"""
    
    def __init__(self, 
                 headless: bool = True,
                 timeout: int = 30,
                 screenshot_callback: Optional[Callable] = None):
        self.headless = headless
        self.timeout = timeout
        self.screenshot_callback = screenshot_callback
        
        self.browser = None
        self.page = None
        self.context = None
        self.running = False
    
    async def launch(self) -> bool:
        """启动浏览器"""
        try:
            # 尝试导入 playwright
            try:
                from playwright.async_api import async_playwright
                
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(
                    headless=self.headless
                )
                self.context = await self.browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                self.page = await self.context.new_page()
                self.running = True
                
                print("Browser launched with Playwright")
                return True
                
            except ImportError:
                # 如果没有 playwright，使用模拟模式
                print("Playwright not installed, using mock mode")
                self.running = True
                return True
                
        except Exception as e:
            print(f"Browser launch error: {e}")
            return False
    
    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
        self.running = False
    
    async def navigate(self, url: str) -> BrowserResult:
        """导航到 URL"""
        if not self.running:
            return BrowserResult(success=False, error="Browser not launched")
        
        try:
            if hasattr(self, 'page') and self.page:
                await self.page.goto(url, timeout=self.timeout * 1000)
                title = await self.page.title()
                
                return BrowserResult(
                    success=True,
                    data={"url": url, "title": title},
                    metadata={"timestamp": datetime.now().isoformat()}
                )
            else:
                # 模拟模式
                return BrowserResult(
                    success=True,
                    data={"url": url, "title": "Mock Page"},
                    metadata={"timestamp": datetime.now().isoformat(), "mode": "mock"}
                )
                
        except Exception as e:
            return BrowserResult(success=False, error=str(e))
    
    async def click(self, selector: ElementSelector) -> BrowserResult:
        """点击元素"""
        if not self.running:
            return BrowserResult(success=False, error="Browser not launched")
        
        try:
            if hasattr(self, 'page') and self.page:
                selector_str = self._build_selector(selector)
                await self.page.click(selector_str, timeout=self.timeout * 1000)
                
                return BrowserResult(
                    success=True,
                    data={"action": "click", "selector": selector.to_dict()}
                )
            else:
                return BrowserResult(
                    success=True,
                    data={"action": "click", "selector": selector.to_dict(), "mode": "mock"}
                )
                
        except Exception as e:
            return BrowserResult(success=False, error=str(e))
    
    async def input_text(self, selector: ElementSelector, text: str, clear: bool = True) -> BrowserResult:
        """输入文本"""
        if not self.running:
            return BrowserResult(success=False, error="Browser not launched")
        
        try:
            if hasattr(self, 'page') and self.page:
                selector_str = self._build_selector(selector)
                
                if clear:
                    await self.page.fill(selector_str, "")
                
                await self.page.fill(selector_str, text)
                
                return BrowserResult(
                    success=True,
                    data={"action": "input", "text": text, "selector": selector.to_dict()}
                )
            else:
                return BrowserResult(
                    success=True,
                    data={"action": "input", "text": text, "selector": selector.to_dict(), "mode": "mock"}
                )
                
        except Exception as e:
            return BrowserResult(success=False, error=str(e))
    
    async def select_option(self, selector: ElementSelector, value: str) -> BrowserResult:
        """选择选项"""
        if not self.running:
            return BrowserResult(success=False, error="Browser not launched")
        
        try:
            if hasattr(self, 'page') and self.page:
                selector_str = self._build_selector(selector)
                await self.page.select_option(selector_str, value)
                
                return BrowserResult(
                    success=True,
                    data={"action": "select", "value": value}
                )
            else:
                return BrowserResult(
                    success=True,
                    data={"action": "select", "value": value, "mode": "mock"}
                )
                
        except Exception as e:
            return BrowserResult(success=False, error=str(e))
    
    async def hover(self, selector: ElementSelector) -> BrowserResult:
        """悬停"""
        if not self.running:
            return BrowserResult(success=False, error="Browser not launched")
        
        try:
            if hasattr(self, 'page') and self.page:
                selector_str = self._build_selector(selector)
                await self.page.hover(selector_str)
                
            return BrowserResult(
                success=True,
                data={"action": "hover", "selector": selector.to_dict()}
            )
            
        except Exception as e:
            return BrowserResult(success=False, error=str(e))
    
    async def scroll(self, x: int = 0, y: int = 500) -> BrowserResult:
        """滚动页面"""
        if not self.running:
            return BrowserResult(success=False, error="Browser not launched")
        
        try:
            if hasattr(self, 'page') and self.page:
                await self.page.evaluate(f"window.scrollTo({x}, {y})")
            
            return BrowserResult(
                success=True,
                data={"action": "scroll", "x": x, "y": y}
            )
            
        except Exception as e:
            return BrowserResult(success=False, error=str(e))
    
    async def wait(self, seconds: float) -> BrowserResult:
        """等待"""
        await asyncio.sleep(seconds)
        
        return BrowserResult(
            success=True,
            data={"action": "wait", "seconds": seconds}
        )
    
    async def wait_for_selector(self, selector: ElementSelector, timeout: int = 30) -> BrowserResult:
        """等待元素出现"""
        if not self.running:
            return BrowserResult(success=False, error="Browser not launched")
        
        try:
            if hasattr(self, 'page') and self.page:
                selector_str = self._build_selector(selector)
                await self.page.wait_for_selector(selector_str, timeout=timeout * 1000)
            
            return BrowserResult(
                success=True,
                data={"action": "wait_for_selector", "selector": selector.to_dict()}
            )
            
        except Exception as e:
            return BrowserResult(success=False, error=str(e))
    
    async def screenshot(self, full_page: bool = False) -> BrowserResult:
        """截图"""
        if not self.running:
            return BrowserResult(success=False, error="Browser not launched")
        
        try:
            if hasattr(self, 'page') and self.page:
                screenshot_bytes = await self.page.screenshot(full_page=full_page)
                screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                
                return BrowserResult(
                    success=True,
                    screenshot=screenshot_base64,
                    metadata={"timestamp": datetime.now().isoformat()}
                )
            else:
                return BrowserResult(
                    success=True,
                    screenshot="",
                    metadata={"timestamp": datetime.now().isoformat(), "mode": "mock"}
                )
            
        except Exception as e:
            return BrowserResult(success=False, error=str(e))
    
    async def get_elements(self, selector: Optional[ElementSelector] = None) -> BrowserResult:
        """获取页面元素"""
        if not self.running:
            return BrowserResult(success=False, error="Browser not launched")
        
        try:
            elements = []
            
            if hasattr(self, 'page') and self.page:
                if selector:
                    selector_str = self._build_selector(selector)
                    page_elements = await self.page.query_selector_all(selector_str)
                else:
                    page_elements = await self.page.query_selector_all("*")
                
                for el in page_elements:
                    try:
                        tag = await el.evaluate("el => el.tagName")
                        text = await el.evaluate("el => el.innerText") or ""
                        attributes = await el.evaluate("""
                            el => {
                                const attrs = {};
                                for (const attr of el.attributes) {
                                    attrs[attr.name] = attr.value;
                                }
                                return attrs;
                            }
                        """)
                        
                        element = PageElement(
                            tag=tag.lower(),
                            text=text[:100],
                            attributes=attributes,
                            selector=selector or ElementSelector(ElementSelectorType.ID, "")
                        )
                        elements.append(element)
                        
                    except:
                        pass
            
            return BrowserResult(
                success=True,
                elements=elements,
                data={"count": len(elements)}
            )
            
        except Exception as e:
            return BrowserResult(success=False, error=str(e))
    
    async def execute_script(self, script: str) -> BrowserResult:
        """执行 JavaScript"""
        if not self.running:
            return BrowserResult(success=False, error="Browser not launched")
        
        try:
            if hasattr(self, 'page') and self.page:
                result = await self.page.evaluate(script)
                
                return BrowserResult(
                    success=True,
                    data={"result": result}
                )
            else:
                return BrowserResult(
                    success=True,
                    data={"result": "Mock result", "mode": "mock"}
                )
            
        except Exception as e:
            return BrowserResult(success=False, error=str(e))
    
    async def fill_form(self, fields: Dict[str, str]) -> BrowserResult:
        """填写表单"""
        results = []
        
        for selector_value, value in fields.items():
            # 尝试作为 CSS 选择器
            selector = ElementSelector(ElementSelectorType.CSS, selector_value)
            result = await self.input_text(selector, value, clear=True)
            results.append(result.to_dict())
        
        success = all(r["success"] for r in results)
        
        return BrowserResult(
            success=success,
            data={"fields": fields, "results": results}
        )
    
    def _build_selector(self, selector: ElementSelector) -> str:
        """构建选择器字符串"""
        if selector.type == ElementSelectorType.ID:
            return f"#{selector.value}"
        elif selector.type == ElementSelectorType.CSS:
            return selector.value
        elif selector.type == ElementSelectorType.XPATH:
            return selector.value
        elif selector.type == ElementSelectorType.NAME:
            return f"[name='{selector.value}']"
        elif selector.type == ElementSelectorType.TEXT:
            return f"text={selector.value}"
        return selector.value


class BrowserManager:
    """浏览器管理器"""
    
    def __init__(self):
        self.browsers: Dict[str, BrowserAutomation] = {}
        self.default_timeout = 30
    
    def create_browser(self, 
                      name: str = "default",
                      headless: bool = True) -> BrowserAutomation:
        """创建浏览器实例"""
        browser = BrowserAutomation(
            headless=headless,
            timeout=self.default_timeout
        )
        self.browsers[name] = browser
        return browser
    
    def get_browser(self, name: str = "default") -> Optional[BrowserAutomation]:
        """获取浏览器实例"""
        return self.browsers.get(name)
    
    async def close_all(self):
        """关闭所有浏览器"""
        for browser in self.browsers.values():
            await browser.close()
        self.browsers.clear()
    
    def list_browsers(self) -> List[Dict[str, Any]]:
        """列出所有浏览器"""
        return [
            {"name": name, "running": b.running}
            for name, b in self.browsers.items()
        ]


# 简化导入
__all__ = [
    "ElementSelectorType",
    "ActionType",
    "ElementSelector",
    "BrowserAction",
    "PageElement",
    "BrowserResult",
    "BrowserAutomation",
    "BrowserManager"
]
