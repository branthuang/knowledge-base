import re
from typing import List, Dict, Any, Union
from app.schemas.block import BlockItem, BlockType, BlockProperties


def _normalize_block(block: Union[Dict[str, Any], BlockItem]) -> BlockItem:
    if isinstance(block, BlockItem):
        return block
    return BlockItem.model_validate(block)


def extract_plain_text(blocks: List[Union[Dict[str, Any], BlockItem]]) -> str:
    """
    Recursively extract human-readable, searchable plain text from structured blocks.
    Used for FTS index and embedding derivation.
    """
    text_chunks: List[str] = []

    def _traverse(block_data: Union[Dict[str, Any], BlockItem], depth: int = 0):
        if depth > 10:  # Prevent infinite recursion
            return
        block = _normalize_block(block_data)

        # Extract content based on block type
        if block.type in (BlockType.PARAGRAPH, BlockType.HEADING, BlockType.QUOTE, BlockType.CALLOUT):
            if isinstance(block.content, str) and block.content.strip():
                text_chunks.append(block.content.strip())
        elif block.type in (BlockType.LIST, BlockType.TODO):
            prefix = ""
            if block.type == BlockType.TODO:
                prefix = "[x] " if block.properties.checked else "[ ] "
            content_str = str(block.content).strip() if block.content else ""
            if content_str:
                text_chunks.append(f"{prefix}{content_str}")
        elif block.type == BlockType.CODE:
            code_text = str(block.content).strip() if block.content else ""
            if code_text:
                lang = block.properties.language or ""
                text_chunks.append(f"{lang}\n{code_text}" if lang else code_text)
        elif block.type == BlockType.TABLE:
            # If content is a 2D array of cells
            if isinstance(block.content, list):
                row_texts = []
                for row in block.content:
                    if isinstance(row, list):
                        cells = [str(c).strip() for c in row if str(c).strip()]
                        if cells:
                            row_texts.append(" | ".join(cells))
                if row_texts:
                    text_chunks.append("\n".join(row_texts))
        elif block.type == BlockType.IMAGE:
            if block.properties.caption:
                text_chunks.append(f"[图片: {block.properties.caption}]")
        elif block.type == BlockType.ATTACHMENT:
            if block.properties.file_name:
                text_chunks.append(f"[附件: {block.properties.file_name}]")

        # Recursively process children
        for child in block.children:
            _traverse(child, depth + 1)

    for b in blocks:
        _traverse(b)

    # Join and normalize multiple consecutive empty lines
    combined = "\n\n".join(chunk for chunk in text_chunks if chunk)
    return re.sub(r"\n{3,}", "\n\n", combined).strip()


def blocks_to_markdown(blocks: List[Union[Dict[str, Any], BlockItem]]) -> str:
    """Convert structured blocks into standard GitHub Flavored Markdown."""
    md_lines: List[str] = []

    for block_data in blocks:
        block = _normalize_block(block_data)
        b_type = block.type
        content = block.content

        if b_type == BlockType.HEADING:
            level = block.properties.level or 1
            hashes = "#" * level
            md_lines.append(f"{hashes} {content}")
        elif b_type == BlockType.PARAGRAPH:
            md_lines.append(str(content))
        elif b_type == BlockType.QUOTE:
            md_lines.append(f"> {content}")
        elif b_type == BlockType.CALLOUT:
            tone = (block.properties.callout_tone or "NOTE").upper()
            md_lines.append(f"> [!{tone}]\n> {content}")
        elif b_type == BlockType.LIST:
            style = block.properties.list_style or "bullet"
            marker = "1." if style == "ordered" else "-"
            md_lines.append(f"{marker} {content}")
        elif b_type == BlockType.TODO:
            box = "[x]" if block.properties.checked else "[ ]"
            md_lines.append(f"- {box} {content}")
        elif b_type == BlockType.CODE:
            lang = block.properties.language or ""
            md_lines.append(f"```{lang}\n{content}\n```")
        elif b_type == BlockType.DIVIDER:
            md_lines.append("---")
        elif b_type == BlockType.TABLE:
            if isinstance(content, list) and content:
                for idx, row in enumerate(content):
                    if isinstance(row, list):
                        cells = [str(c) for c in row]
                        md_lines.append("| " + " | ".join(cells) + " |")
                        if idx == 0:
                            # Header divider
                            md_lines.append("| " + " | ".join(["---"] * len(cells)) + " |")
        elif b_type == BlockType.IMAGE:
            caption = block.properties.caption or "Image"
            url = str(content)
            md_lines.append(f"![{caption}]({url})")
        elif b_type == BlockType.ATTACHMENT:
            name = block.properties.file_name or "Attachment"
            url = str(content)
            md_lines.append(f"[{name}]({url})")

    return "\n\n".join(md_lines)


def markdown_to_blocks(md_text: str) -> List[BlockItem]:
    """Basic parser to convert simple Markdown text into structured BlockItems."""
    lines = md_text.splitlines()
    blocks: List[BlockItem] = []
    in_code_block = False
    code_lang = ""
    code_lines: List[str] = []

    for line in lines:
        stripped = line.strip()

        # Code block fence toggle
        if stripped.startswith("```"):
            if in_code_block:
                blocks.append(
                    BlockItem(
                        type=BlockType.CODE,
                        content="\n".join(code_lines),
                        properties=BlockProperties(language=code_lang),
                    )
                )
                in_code_block = False
                code_lang = ""
                code_lines = []
            else:
                in_code_block = True
                code_lang = stripped[3:].strip()
                code_lines = []
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        if not stripped:
            continue

        # Horizontal Rule
        if stripped in ("---", "***", "___"):
            blocks.append(BlockItem(type=BlockType.DIVIDER))
        # Heading
        elif stripped.startswith("#"):
            match = re.match(r"^(#{1,4})\s+(.+)$", stripped)
            if match:
                level = len(match.group(1))
                text = match.group(2)
                blocks.append(
                    BlockItem(
                        type=BlockType.HEADING,
                        content=text,
                        properties=BlockProperties(level=level),
                    )
                )
            else:
                blocks.append(BlockItem(type=BlockType.PARAGRAPH, content=stripped))
        # Todo item
        elif re.match(r"^-\s+\[([ xX])\]\s+(.+)$", stripped):
            match = re.match(r"^-\s+\[([ xX])\]\s+(.+)$", stripped)
            checked = match.group(1).lower() == "x"
            text = match.group(2)
            blocks.append(
                BlockItem(
                    type=BlockType.TODO,
                    content=text,
                    properties=BlockProperties(checked=checked),
                )
            )
        # Bullet list item
        elif stripped.startswith(("- ", "* ", "+ ")):
            text = stripped[2:].strip()
            blocks.append(
                BlockItem(
                    type=BlockType.LIST,
                    content=text,
                    properties=BlockProperties(list_style="bullet"),
                )
            )
        # Numbered list item
        elif re.match(r"^\d+\.\s+(.+)$", stripped):
            match = re.match(r"^\d+\.\s+(.+)$", stripped)
            text = match.group(1)
            blocks.append(
                BlockItem(
                    type=BlockType.LIST,
                    content=text,
                    properties=BlockProperties(list_style="ordered"),
                )
            )
        # Blockquote
        elif stripped.startswith("> "):
            text = stripped[2:].strip()
            blocks.append(BlockItem(type=BlockType.QUOTE, content=text))
        # Paragraph
        else:
            blocks.append(BlockItem(type=BlockType.PARAGRAPH, content=stripped))

    return blocks
