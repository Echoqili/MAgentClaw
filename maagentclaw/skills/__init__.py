"""
Skills - 技能包

所有内置技能的集合
"""

from .hello_world import HelloWorldSkill
from .calculator import CalculatorSkill
from .weather import WeatherSkill
from .file_operator import FileOperatorSkill
from .web_scrape import WebScrapeSkill
from .data_processor import DataProcessorSkill
from .datetime_skill import DateTimeSkill
from .text_extract import TextExtractSkill
from .code_generator import CodeGeneratorSkill
from .http_request import HTTPSkill
from .image_analysis import ImageAnalysisSkill

__all__ = [
    "HelloWorldSkill",
    "CalculatorSkill",
    "WeatherSkill",
    "FileOperatorSkill",
    "WebScrapeSkill",
    "DataProcessorSkill",
    "DateTimeSkill",
    "TextExtractSkill",
    "CodeGeneratorSkill",
    "HTTPSkill",
    "ImageAnalysisSkill"
]
