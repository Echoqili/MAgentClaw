from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from ..memory.vector_store import InMemoryVectorStore
from .document_loader import Document, load_document
from .text_splitter import RecursiveTextSplitter


class RAGPipeline:
    """RAG 管道 - 文档问答"""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        top_k: int = 3
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k

        self.vector_store = InMemoryVectorStore()
        self.text_splitter = RecursiveTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        self.documents: List[Document] = []
        self.is_indexed = False

    async def load_and_index(
        self,
        source: Path,
        loader_func: Optional[Callable] = None
    ) -> int:
        """加载并索引文档"""
        if loader_func:
            self.documents = await loader_func(source)
        else:
            self.documents = await load_document(source)

        total_chunks = 0

        for doc in self.documents:
            chunks = self.text_splitter.split(
                doc.content,
                doc.metadata
            )

            for chunk in chunks:
                chunk_item = _ChunkItem(
                    id=f"doc_{self.documents.index(doc)}_chunk_{chunk.index}",
                    content=chunk.content,
                    metadata={
                        **chunk.metadata,
                        "source": doc.source,
                        "doc_index": self.documents.index(doc)
                    }
                )
                await self.vector_store.add(chunk_item)
                total_chunks += 1

        self.is_indexed = True
        return total_chunks

    async def search(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """检索相关文档"""
        if not self.is_indexed:
            return []

        k = top_k or self.top_k
        results = await self.vector_store.search(query, k)

        formatted_results = []
        for item in results:
            formatted_results.append({
                "content": item.content,
                "metadata": item.metadata,
                "score": getattr(item, "score", None)
            })

        return formatted_results

    async def query(
        self,
        query: str,
        llm_callback: Optional[Callable] = None,
        system_prompt: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> Dict[str, Any]:
        """查询 RAG"""
        context_docs = await self.search(query, top_k)

        if not context_docs:
            return {
                "answer": "没有找到相关文档",
                "sources": [],
                "query": query
            }

        context = "\n\n".join(
            f"[{i+1}] {doc['content']}"
            for i, doc in enumerate(context_docs)
        )

        if llm_callback:
            user_prompt = f"""基于以下参考文档回答问题。

参考文档:
{context}

问题: {query}

请根据参考文档回答，如果文档中没有相关信息，请说明"根据提供的信息无法回答"。"""

            answer = await llm_callback(
                user_prompt,
                system=system_prompt or "你是一个有帮助的问答助手。"
            )
        else:
            best_doc = context_docs[0]
            answer = f"根据文档: {best_doc['content'][:200]}..."

        return {
            "answer": answer,
            "sources": context_docs,
            "query": query
        }

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "document_count": len(self.documents),
            "chunk_count": self.vector_store.count(),
            "is_indexed": self.is_indexed,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap
        }

    async def clear(self) -> None:
        """清空索引"""
        self.vector_store.clear()
        self.documents.clear()
        self.is_indexed = False


class _ChunkItem:
    """内部使用的块项目"""

    def __init__(self, id: str, content: str, metadata: Dict[str, Any]):
        self.id = id
        self.content = content
        self.metadata = metadata
