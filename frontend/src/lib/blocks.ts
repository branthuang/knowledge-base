import { BlockItem, BlockType, BlockProperties } from './types';

/**
 * Generate client-side UUID v4
 */
export function generateUUID(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/**
 * Convert Markdown text to structured BlockItem array
 */
export function markdownToBlocks(markdown: string): BlockItem[] {
  if (!markdown) return [];

  const lines = markdown.split(/\r?\n/);
  const blocks: BlockItem[] = [];

  let inCodeBlock = false;
  let codeLang = '';
  let codeLines: string[] = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // Code block toggle
    if (trimmed.startsWith('```')) {
      if (inCodeBlock) {
        blocks.push({
          id: generateUUID(),
          type: 'code',
          content: codeLines.join('\n'),
          properties: { language: codeLang || 'plaintext' },
        });
        inCodeBlock = false;
        codeLang = '';
        codeLines = [];
      } else {
        inCodeBlock = true;
        codeLang = trimmed.slice(3).trim();
        codeLines = [];
      }
      continue;
    }

    if (inCodeBlock) {
      codeLines.push(line);
      continue;
    }

    if (!trimmed) {
      continue;
    }

    // Horizontal Rule / Divider
    if (trimmed === '---' || trimmed === '***' || trimmed === '___') {
      blocks.push({
        id: generateUUID(),
        type: 'divider',
        content: '',
        properties: {},
      });
      continue;
    }

    // Headings: #, ##, ###, ####
    const headingMatch = trimmed.match(/^(#{1,4})\s+(.+)$/);
    if (headingMatch) {
      const level = headingMatch[1].length;
      blocks.push({
        id: generateUUID(),
        type: 'heading',
        content: headingMatch[2].trim(),
        properties: { level },
      });
      continue;
    }

    // Todo item: - [ ] or - [x]
    const todoMatch = trimmed.match(/^-\s+\[([ xX])\]\s+(.+)$/);
    if (todoMatch) {
      const checked = todoMatch[1].toLowerCase() === 'x';
      blocks.push({
        id: generateUUID(),
        type: 'todo',
        content: todoMatch[2].trim(),
        properties: { checked },
      });
      continue;
    }

    // Bullet list item
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ') || trimmed.startsWith('+ ')) {
      blocks.push({
        id: generateUUID(),
        type: 'list',
        content: trimmed.slice(2).trim(),
        properties: { list_style: 'bullet' },
      });
      continue;
    }

    // Numbered list item
    const numberedMatch = trimmed.match(/^\d+\.\s+(.+)$/);
    if (numberedMatch) {
      blocks.push({
        id: generateUUID(),
        type: 'list',
        content: numberedMatch[1].trim(),
        properties: { list_style: 'ordered' },
      });
      continue;
    }

    // Blockquote
    if (trimmed.startsWith('> ')) {
      blocks.push({
        id: generateUUID(),
        type: 'quote',
        content: trimmed.slice(2).trim(),
        properties: {},
      });
      continue;
    }

    // Regular paragraph
    blocks.push({
      id: generateUUID(),
      type: 'paragraph',
      content: trimmed,
      properties: {},
    });
  }

  // Handle unclosed code block
  if (inCodeBlock && codeLines.length > 0) {
    blocks.push({
      id: generateUUID(),
      type: 'code',
      content: codeLines.join('\n'),
      properties: { language: codeLang || 'plaintext' },
    });
  }

  return blocks;
}

/**
 * Convert structured BlockItem array back to Markdown text
 */
export function blocksToMarkdown(blocks: BlockItem[]): string {
  if (!blocks || !Array.isArray(blocks) || blocks.length === 0) {
    return '';
  }

  const lines: string[] = [];

  for (const block of blocks) {
    const content = typeof block.content === 'string' ? block.content : JSON.stringify(block.content);

    switch (block.type) {
      case 'heading': {
        const level = block.properties?.level || 1;
        const prefix = '#'.repeat(level);
        lines.push(`${prefix} ${content}`);
        break;
      }
      case 'paragraph':
        lines.push(content);
        break;
      case 'quote':
        lines.push(`> ${content}`);
        break;
      case 'callout': {
        const tone = (block.properties?.callout_tone || 'NOTE').toUpperCase();
        lines.push(`> [!${tone}]\n> ${content}`);
        break;
      }
      case 'list': {
        const style = block.properties?.list_style || 'bullet';
        const marker = style === 'ordered' ? '1.' : '-';
        lines.push(`${marker} ${content}`);
        break;
      }
      case 'todo': {
        const marker = block.properties?.checked ? '[x]' : '[ ]';
        lines.push(`- ${marker} ${content}`);
        break;
      }
      case 'code': {
        const lang = block.properties?.language || '';
        lines.push(`\`\`\`${lang}\n${content}\n\`\`\``);
        break;
      }
      case 'divider':
        lines.push('---');
        break;
      case 'table': {
        if (Array.isArray(block.content) && block.content.length > 0) {
          block.content.forEach((row, idx) => {
            if (Array.isArray(row)) {
              lines.push(`| ${row.map((c) => String(c).trim()).join(' | ')} |`);
              if (idx === 0) {
                lines.push(`| ${row.map(() => '---').join(' | ')} |`);
              }
            }
          });
        }
        break;
      }
      default:
        lines.push(content);
        break;
    }
  }

  return lines.join('\n\n');
}
