from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import re


@dataclass
class TextChunk:
    """文本块"""
    content: str
    metadata: Dict[str, Any]
    index: int


class TextSplitter(ABC):
    """文本分块器基类"""

    @abstractmethod
    def split(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[TextChunk]:
        """分块文本"""
        pass


class RecursiveTextSplitter(TextSplitter):
    """递归文本分块器"""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: Optional[List[str]] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or [
            "\n\n",
            "\n",
            ".",
            "?",
            "!",
            ";",
            ",",
            " ",
            ""
        ]

    def split(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[TextChunk]:
        """递归分块"""
        metadata = metadata or {}

        chunks = []
        self._split_text(text, metadata, chunks, 0)

        return [
            TextChunk(
                content=chunk,
                metadata={**metadata, "index": i},
                index=i
            )
            for i, chunk in enumerate(chunks)
        ]

    def _split_text(
        self,
        text: str,
        metadata: Dict[str, Any],
        chunks: List[str],
        depth: int
    ) -> None:
        """递归拆分文本"""
        if depth >= len(self.separators):
            if text.strip():
                chunks.append(text.strip())
            return

        separator = self.separators[depth]

        if not separator:
            for i in range(0, len(text), self.chunk_size):
                chunk = text[i:i + self.chunk_size]
                if chunk.strip():
                    chunks.append(chunk.strip())
            return

        parts = text.split(separator)

        current_chunk = ""

        for part in parts:
            test_chunk = current_chunk + separator + part if current_chunk else part

            if len(test_chunk) <= self.chunk_size:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())

                    overlap_parts = current_chunk.split(separator)
                    if len(overlap_parts) > 1 and self.chunk_overlap > 0:
                        overlap = separator.join(overlap_parts[-2:])[-self.chunk_overlap:]
                        current_chunk = overlap + separator + part
                    else:
                        current_chunk = part
                else:
                    self._split_text(part, metadata, chunks, depth + 1)

        if current_chunk.strip():
            chunks.append(current_chunk.strip())


class FixedSizeSplitter(TextSplitter):
    """固定大小分块器"""

    def __init__(self, chunk_size: int = 200, overlap: int = 20):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[TextChunk]:
        """固定大小分块"""
        metadata = metadata or {}
        chunks = []

        start = 0
        index = 0

        while start < len(text):
            end = start + self.chunk_size

            if end < len(text):
                newline_pos = text.rfind("\n", start, end)
                if newline_pos > start:
                    end = newline_pos

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(TextChunk(
                    content=chunk,
                    metadata={**metadata, "index": index},
                    index=index
                ))
                index += 1

            start = end - self.overlap
            if start < 0:
                start = 0

        return chunks


def split_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
    method: str = "recursive"
) -> List[str]:
    """便捷文本分块函数"""
    if method == "fixed":
        splitter = FixedSizeSplitter(chunk_size, overlap)
    else:
        splitter = RecursiveTextSplitter(chunk_size, overlap)

    chunks = splitter.split(text)
    return [chunk.content for chunk in chunks]
