import re
from dataclasses import dataclass
from typing import List, Optional, Union, Dict, Any
from app.schemas.block import BlockItem, BlockType
from app.services.block_parser import _normalize_block


@dataclass
class TextChunk:
    chunk_text: str
    block_id: Optional[str] = None
    token_count: int = 0


class DocumentChunker:
    """
    Structured document chunker supporting:
    1. Block-level semantic boundaries.
    2. Length window aggregation (default 400 chars).
    3. Large block subdivision with sliding overlap window (default 50 chars).
    4. Plain-text fallback for legacy or raw markdown inputs.
    """

    def __init__(
        self,
        max_chunk_size: int = 400,
        min_chunk_size: int = 50,
        overlap_size: int = 50,
    ):
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.overlap_size = overlap_size

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation for mixed Chinese and English text."""
        if not text:
            return 0
        return max(1, len(text) // 2)

    def _extract_block_units(
        self, blocks: List[Union[Dict[str, Any], BlockItem]]
    ) -> List[Dict[str, Any]]:
        """Flatten nested block tree into a list of {block_id, text, type} units."""
        units: List[Dict[str, Any]] = []

        def _traverse(block_data: Union[Dict[str, Any], BlockItem], depth: int = 0):
            if depth > 10:
                return
            block = _normalize_block(block_data)
            b_id = block.id
            b_type = block.type
            content = block.content

            text = ""
            if b_type == BlockType.HEADING:
                level = block.properties.level or 1
                hashes = "#" * level
                text = f"{hashes} {content}".strip()
            elif b_type in (BlockType.PARAGRAPH, BlockType.QUOTE, BlockType.CALLOUT):
                if isinstance(content, str) and content.strip():
                    text = content.strip()
            elif b_type == BlockType.LIST:
                style = block.properties.list_style or "bullet"
                marker = "1." if style == "ordered" else "-"
                text = f"{marker} {content}".strip()
            elif b_type == BlockType.TODO:
                box = "[x]" if block.properties.checked else "[ ]"
                text = f"- {box} {content}".strip()
            elif b_type == BlockType.CODE:
                code_text = str(content).strip() if content else ""
                lang = block.properties.language or ""
                text = f"```{lang}\n{code_text}\n```" if code_text else ""
            elif b_type == BlockType.TABLE:
                if isinstance(content, list) and content:
                    rows = []
                    for row in content:
                        if isinstance(row, list):
                            cells = [str(c).strip() for c in row if str(c).strip()]
                            if cells:
                                rows.append(" | ".join(cells))
                    if rows:
                        text = "\n".join(rows)
            elif b_type == BlockType.IMAGE:
                if block.properties.caption:
                    text = f"[图片: {block.properties.caption}]"
            elif b_type == BlockType.ATTACHMENT:
                if block.properties.file_name:
                    text = f"[附件: {block.properties.file_name}]"

            if text:
                units.append({"block_id": b_id, "text": text, "type": b_type})

            for child in block.children:
                _traverse(child, depth + 1)

        for b in blocks:
            _traverse(b)

        return units

    def split_large_text(
        self,
        text: str,
        block_id: Optional[str] = None,
    ) -> List[TextChunk]:
        """
        Split a single large text string exceeding max_chunk_size into smaller chunks
        with sliding overlap.
        """
        if len(text) <= self.max_chunk_size:
            return [TextChunk(chunk_text=text, block_id=block_id, token_count=self.estimate_tokens(text))]

        chunks: List[TextChunk] = []
        delimiters = r"(\n\n|\n|。|！|？|\. |\? |! )"
        segments = [s for s in re.split(delimiters, text) if s]

        current_piece = ""
        for seg in segments:
            if len(current_piece) + len(seg) <= self.max_chunk_size:
                current_piece += seg
            else:
                if current_piece.strip():
                    chunks.append(
                        TextChunk(
                            chunk_text=current_piece.strip(),
                            block_id=block_id,
                            token_count=self.estimate_tokens(current_piece.strip()),
                        )
                    )
                overlap_tail = current_piece[-self.overlap_size :] if len(current_piece) > self.overlap_size else current_piece
                current_piece = overlap_tail + seg

        if current_piece.strip():
            chunks.append(
                TextChunk(
                    chunk_text=current_piece.strip(),
                    block_id=block_id,
                    token_count=self.estimate_tokens(current_piece.strip()),
                )
            )

        if len(chunks) == 1 and len(chunks[0].chunk_text) > self.max_chunk_size:
            raw_text = chunks[0].chunk_text
            chunks = []
            start = 0
            step = max(1, self.max_chunk_size - self.overlap_size)
            while start < len(raw_text):
                sub = raw_text[start : start + self.max_chunk_size].strip()
                if sub:
                    chunks.append(
                        TextChunk(
                            chunk_text=sub,
                            block_id=block_id,
                            token_count=self.estimate_tokens(sub),
                        )
                    )
                start += step

        return chunks

    def chunk_blocks(
        self,
        blocks: List[Union[Dict[str, Any], BlockItem]],
        title: Optional[str] = None,
    ) -> List[TextChunk]:
        """
        Chunk structured blocks into optimal semantic search units.
        Aggregates small adjacent blocks and splits oversized blocks.
        """
        units = self._extract_block_units(blocks)
        if not units:
            return []

        chunks: List[TextChunk] = []
        current_texts: List[str] = []
        current_len = 0
        current_block_ids: List[str] = []

        for unit in units:
            unit_text = unit["text"]
            unit_id = unit["block_id"]

            if len(unit_text) > self.max_chunk_size:
                if current_texts:
                    combined = "\n\n".join(current_texts).strip()
                    chunks.append(
                        TextChunk(
                            chunk_text=combined,
                            block_id=current_block_ids[0] if current_block_ids else None,
                            token_count=self.estimate_tokens(combined),
                        )
                    )
                    current_texts = []
                    current_len = 0
                    current_block_ids = []

                large_chunks = self.split_large_text(unit_text, block_id=unit_id)
                chunks.extend(large_chunks)
                continue

            added_len = len(unit_text) + (2 if current_texts else 0)
            if current_len + added_len > self.max_chunk_size:
                combined = "\n\n".join(current_texts).strip()
                chunks.append(
                    TextChunk(
                        chunk_text=combined,
                        block_id=current_block_ids[0] if current_block_ids else None,
                        token_count=self.estimate_tokens(combined),
                    )
                )
                current_texts = [unit_text]
                current_len = len(unit_text)
                current_block_ids = [unit_id]
            else:
                current_texts.append(unit_text)
                current_len += added_len
                current_block_ids.append(unit_id)

        if current_texts:
            combined = "\n\n".join(current_texts).strip()
            chunks.append(
                TextChunk(
                    chunk_text=combined,
                    block_id=current_block_ids[0] if current_block_ids else None,
                    token_count=self.estimate_tokens(combined),
                )
            )

        return chunks

    def chunk_plain_text(
        self,
        plain_text: str,
        title: Optional[str] = None,
    ) -> List[TextChunk]:
        """Fallback chunker for plain text or markdown string."""
        if not plain_text or not plain_text.strip():
            return []
        return self.split_large_text(plain_text.strip(), block_id=None)


# Global default chunker instance
default_chunker = DocumentChunker()
