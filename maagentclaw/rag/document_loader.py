from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Document:
    """文档"""
    content: str
    metadata: Dict[str, Any]
    source: Optional[str] = None


class DocumentLoader(ABC):
    """文档加载器基类"""

    @abstractmethod
    async def load(self, path: Path) -> List[Document]:
        """加载文档"""
        pass


class TextLoader(DocumentLoader):
    """文本文件加载器"""

    async def load(self, path: Path) -> List[Document]:
        """加载文本文件"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            return [Document(
                content=content,
                metadata={"source": str(path), "type": "text"},
                source=str(path)
            )]
        except Exception as e:
            print(f"Error loading text file {path}: {e}")
            return []


class MarkdownLoader(DocumentLoader):
    """Markdown 文件加载器"""

    async def load(self, path: Path) -> List[Document]:
        """加载 Markdown 文件"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            metadata = {
                "source": str(path),
                "type": "markdown",
                "title": path.stem
            }

            return [Document(
                content=content,
                metadata=metadata,
                source=str(path)
            )]
        except Exception as e:
            print(f"Error loading markdown file {path}: {e}")
            return []


class DirectoryLoader(DocumentLoader):
    """目录加载器"""

    def __init__(self, loaders: Optional[Dict[str, DocumentLoader]] = None):
        self.loaders = loaders or {
            ".txt": TextLoader(),
            ".md": MarkdownLoader(),
            ".markdown": MarkdownLoader()
        }

    async def load(self, path: Path) -> List[Document]:
        """加载目录中的所有文档"""
        documents = []

        if not path.exists() or not path.is_dir():
            return documents

        for file_path in path.rglob("*"):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                loader = self.loaders.get(ext)

                if loader:
                    docs = await loader.load(file_path)
                    documents.extend(docs)

        return documents


async def load_document(path: Path) -> List[Document]:
    """便捷函数：自动选择加载器"""
    loaders: Dict[str, DocumentLoader] = {
        ".txt": TextLoader(),
        ".md": MarkdownLoader(),
        ".markdown": MarkdownLoader()
    }

    if path.is_dir():
        return await DirectoryLoader(loaders).load(path)

    ext = path.suffix.lower()
    loader = loaders.get(ext)

    if loader:
        return await loader.load(path)

    return []
