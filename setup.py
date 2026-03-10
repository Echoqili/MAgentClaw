"""
MAgentClaw - 多 Agent 管理系统
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="maagentclaw",
    version="1.3.0",
    author="MAgentClaw Team",
    author_email="team@maagentclaw.com",
    description="多 Agent 管理系统 - 灵感来自 OpenClaw",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/MAgentClaw",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "flask>=2.0.0",
        "aiohttp>=3.8.0",
        "openai>=1.0.0",
        "dashscope>=1.0.0",
        "tiktoken>=0.5.0",
        "websockets>=10.0",
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "maagentclaw=maagentclaw.main_enhanced:main",
        ],
    },
    include_package_data=True,
    package_data={
        "maagentclaw": [
            "web/templates/*.html",
            "web/static/*",
        ],
    },
)
