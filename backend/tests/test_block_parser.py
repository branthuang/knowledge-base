import pytest
from app.schemas.block import BlockItem, BlockType, BlockProperties
from app.services.block_parser import extract_plain_text, blocks_to_markdown, markdown_to_blocks


def test_block_schemas_and_validation():
    p = BlockItem(type=BlockType.PARAGRAPH, content="This is a test paragraph")
    assert p.type == BlockType.PARAGRAPH
    assert p.content == "This is a test paragraph"
    assert p.id is not None

    h = BlockItem(type=BlockType.HEADING, content="Title", properties=BlockProperties(level=2))
    assert h.properties.level == 2

    todo = BlockItem(type=BlockType.TODO, content="Task 1", properties=BlockProperties(checked=True))
    assert todo.properties.checked is True

    code = BlockItem(
        type=BlockType.CODE,
        content="print('hello')",
        properties=BlockProperties(language="python"),
    )
    assert code.properties.language == "python"

    table = BlockItem(
        type=BlockType.TABLE,
        content=[
            ["Col1", "Col2"],
            ["Val1", "Val2"],
        ],
    )
    assert len(table.content) == 2


def test_extract_plain_text():
    blocks = [
        {"type": "heading", "content": "知识库架构设计", "properties": {"level": 1}},
        {"type": "paragraph", "content": "本文描述系统核心模块设计与职责划分。"},
        {"type": "todo", "content": "完成块模型设计", "properties": {"checked": True}},
        {"type": "todo", "content": "完成测试验证", "properties": {"checked": False}},
        {"type": "code", "content": "def run():\n    pass", "properties": {"language": "python"}},
        {
            "type": "table",
            "content": [
                ["表头A", "表头B"],
                ["数据1", "数据2"],
            ],
        },
        {"type": "image", "content": "http://example.com/img.png", "properties": {"caption": "架构图"}},
    ]

    plain_text = extract_plain_text(blocks)
    assert "知识库架构设计" in plain_text
    assert "系统核心模块设计" in plain_text
    assert "[x] 完成块模型设计" in plain_text
    assert "[ ] 完成测试验证" in plain_text
    assert "def run():" in plain_text
    assert "表头A | 表头B" in plain_text
    assert "[图片: 架构图]" in plain_text


def test_blocks_to_markdown():
    blocks = [
        BlockItem(type=BlockType.HEADING, content="快速上手", properties=BlockProperties(level=2)),
        BlockItem(type=BlockType.PARAGRAPH, content="执行以下命令启动项目："),
        BlockItem(type=BlockType.CODE, content="uvicorn main:app --reload", properties=BlockProperties(language="bash")),
        BlockItem(type=BlockType.DIVIDER),
    ]

    md = blocks_to_markdown(blocks)
    assert "## 快速上手" in md
    assert "执行以下命令启动项目：" in md
    assert "```bash\nuvicorn main:app --reload\n```" in md
    assert "---" in md


def test_markdown_to_blocks():
    md = """# 主标题
这是正文段落。

## 子标题
- 列表项1
- 列表项2

- [x] 已完成待办
- [ ] 未完成待办

```python
x = 10
```
---
"""
    blocks = markdown_to_blocks(md)
    assert len(blocks) >= 7
    assert blocks[0].type == BlockType.HEADING
    assert blocks[0].content == "主标题"
    assert blocks[0].properties.level == 1

    assert blocks[1].type == BlockType.PARAGRAPH

    assert blocks[2].type == BlockType.HEADING
    assert blocks[2].properties.level == 2

    assert blocks[3].type == BlockType.LIST
    assert blocks[4].type == BlockType.LIST

    assert blocks[5].type == BlockType.TODO
    assert blocks[5].properties.checked is True

    assert blocks[6].type == BlockType.TODO
    assert blocks[6].properties.checked is False

    assert blocks[7].type == BlockType.CODE
    assert blocks[7].properties.language == "python"

    assert blocks[8].type == BlockType.DIVIDER
