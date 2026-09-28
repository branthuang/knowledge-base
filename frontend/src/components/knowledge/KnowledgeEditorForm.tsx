'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  ArrowLeft,
  Save,
  Star,
  Eye,
  Edit3,
  Tag as TagIcon,
  FolderTree,
  FileText,
  AlertCircle,
  Plus,
  RefreshCw,
  Code,
  List,
  Heading2,
  Quote,
  Table as TableIcon,
  Check,
} from 'lucide-react';
import { api } from '@/lib/api';
import { Category, KnowledgeDetail, Tag } from '@/lib/types';
import { blocksToMarkdown, markdownToBlocks } from '@/lib/blocks';

interface KnowledgeEditorFormProps {
  mode: 'create' | 'edit';
  initialData?: KnowledgeDetail;
}

export default function KnowledgeEditorForm({ mode, initialData }: KnowledgeEditorFormProps) {
  const router = useRouter();

  // Form Fields
  const [title, setTitle] = useState(initialData?.title || '');
  const [summary, setSummary] = useState(initialData?.summary || '');
  const [categoryId, setCategoryId] = useState(initialData?.category_id || '');
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>(
    initialData?.tags?.map((t) => t.id) || []
  );
  const [status, setStatus] = useState<'draft' | 'published' | 'archived'>(
    initialData?.status || 'published'
  );
  const [favorite, setFavorite] = useState(initialData?.favorite || false);

  // Markdown content
  const [contentMarkdown, setContentMarkdown] = useState<string>(() => {
    if (initialData?.blocks_json && initialData.blocks_json.length > 0) {
      return blocksToMarkdown(initialData.blocks_json);
    }
    return '';
  });

  // UI state
  const [tab, setTab] = useState<'edit' | 'preview'>('edit');
  const [categories, setCategories] = useState<Category[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [newTagName, setNewTagName] = useState('');
  const [creatingTag, setCreatingTag] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load categories and tags
  useEffect(() => {
    api.categories.list().then(setCategories).catch(console.error);
    api.tags.list().then(setTags).catch(console.error);
  }, []);

  const handleToggleTag = (tagId: string) => {
    setSelectedTagIds((prev) =>
      prev.includes(tagId) ? prev.filter((id) => id !== tagId) : [...prev, tagId]
    );
  };

  const handleCreateNewTag = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = newTagName.trim();
    if (!trimmed) return;
    try {
      setCreatingTag(true);
      const newTag = await api.tags.create({ name: trimmed, color: '#3B82F6' });
      setTags((prev) => [...prev, newTag]);
      setSelectedTagIds((prev) => [...prev, newTag.id]);
      setNewTagName('');
    } catch (err: any) {
      alert('创建标签失败: ' + err.message);
    } finally {
      setCreatingTag(false);
    }
  };

  const handleInsertSnippet = (snippet: string) => {
    setContentMarkdown((prev) => {
      if (!prev) return snippet;
      return `${prev}\n\n${snippet}`;
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError('知识点标题不能为空');
      return;
    }

    try {
      setSaving(true);
      setError(null);

      const parsedBlocks = markdownToBlocks(contentMarkdown.trim());

      if (mode === 'create') {
        const created = await api.knowledge.create({
          title: title.trim(),
          summary: summary.trim() || undefined,
          blocks_json: parsedBlocks,
          category_id: categoryId || undefined,
          tag_ids: selectedTagIds,
          status,
          favorite,
          source_type: 'manual',
          sources: [
            {
              type: 'manual',
              title: '手动录入',
              metadata_json: { created_via: 'web_editor' },
            },
          ],
        });
        router.push(`/knowledge/${created.id}`);
      } else if (mode === 'edit' && initialData) {
        await api.knowledge.update(initialData.id, {
          title: title.trim(),
          summary: summary.trim() || undefined,
          blocks_json: parsedBlocks,
          category_id: categoryId || undefined,
          tag_ids: selectedTagIds,
          status,
          favorite,
        });
        router.push(`/knowledge/${initialData.id}`);
      }
    } catch (err: any) {
      console.error('Failed to save knowledge item:', err);
      setError(err?.message || '保存失败，请检查网络或重试');
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-5xl mx-auto px-6 py-8 space-y-6">
      {/* Top Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => router.back()}
            className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors border border-slate-200"
            title="返回"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-slate-800 tracking-tight flex items-center gap-2">
              <FileText className="w-6 h-6 text-blue-600" />
              <span>{mode === 'create' ? '新建知识点' : '编辑知识点'}</span>
            </h1>
            <p className="mt-0.5 text-xs text-slate-500">
              {mode === 'create'
                ? '录入结构化知识资产，自动构建语义向量索引以供全局精准检索'
                : `正在修改《${initialData?.title || ''}》的元数据与正文内容`}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setFavorite(!favorite)}
            className={`p-2 rounded-lg border transition-all flex items-center gap-1.5 text-xs font-medium ${
              favorite
                ? 'bg-amber-50 border-amber-300 text-amber-600'
                : 'bg-white border-slate-200 text-slate-500 hover:bg-slate-50'
            }`}
            title={favorite ? '已收藏' : '未收藏'}
          >
            <Star className={`w-4 h-4 ${favorite ? 'fill-amber-500 text-amber-500' : ''}`} />
            <span>{favorite ? '已收藏' : '收藏'}</span>
          </button>

          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as any)}
            className="px-3 py-2 rounded-lg border border-slate-200 text-slate-700 bg-white outline-none cursor-pointer text-xs font-medium"
          >
            <option value="published">已发布 (可检索)</option>
            <option value="draft">草稿 (待整理)</option>
            <option value="archived">已归档</option>
          </select>

          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold shadow-xs transition-all disabled:opacity-50"
          >
            {saving ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>正在保存...</span>
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                <span>{mode === 'create' ? '创建并发布' : '保存修改'}</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error alert */}
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
          <span>{error}</span>
        </div>
      )}

      {/* Basic Metadata Section */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-2xs space-y-4">
        {/* Title */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5">
            知识点标题 <span className="text-rose-500">*</span>
          </label>
          <input
            type="text"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="例如：OpenResty 流量网关调度机制与双写升级方案"
            className="w-full px-3.5 py-2.5 rounded-lg border border-slate-200 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none text-sm text-slate-800 placeholder-slate-400 font-medium"
          />
        </div>

        {/* Summary */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5">
            摘要说明 <span className="text-slate-400 font-normal">(可选，用于检索卡片快速导读)</span>
          </label>
          <textarea
            rows={2}
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            placeholder="简要概括该知识点的核心内容、适用场景或技术要点..."
            className="w-full px-3.5 py-2 rounded-lg border border-slate-200 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none text-xs text-slate-800 placeholder-slate-400 leading-relaxed"
          />
        </div>

        {/* Category & Tags Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          {/* Category */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5 flex items-center gap-1.5">
              <FolderTree className="w-3.5 h-3.5 text-blue-600" />
              <span>所属分类</span>
            </label>
            <select
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-white text-xs text-slate-700 outline-none cursor-pointer"
            >
              <option value="">未分类</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          {/* Tags */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5 flex items-center gap-1.5">
              <TagIcon className="w-3.5 h-3.5 text-blue-600" />
              <span>关联标签</span>
            </label>
            <div className="flex flex-wrap items-center gap-1.5 max-h-24 overflow-y-auto p-2 border border-slate-200 rounded-lg bg-slate-50/50">
              {tags.map((t) => {
                const isSelected = selectedTagIds.includes(t.id);
                return (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => handleToggleTag(t.id)}
                    className={`px-2.5 py-1 rounded text-xs transition-all flex items-center gap-1 ${
                      isSelected
                        ? 'bg-blue-600 text-white font-medium shadow-2xs'
                        : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
                    }`}
                  >
                    {isSelected && <Check className="w-3 h-3" />}
                    <span>#{t.name}</span>
                  </button>
                );
              })}
            </div>

            {/* Inline tag creator */}
            <div className="mt-2 flex items-center gap-2">
              <input
                type="text"
                value={newTagName}
                onChange={(e) => setNewTagName(e.target.value)}
                placeholder="新建标签..."
                className="px-2.5 py-1 text-xs border border-slate-200 rounded-md outline-none flex-1"
              />
              <button
                type="button"
                onClick={handleCreateNewTag}
                disabled={creatingTag || !newTagName.trim()}
                className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md text-xs font-medium border border-slate-200 flex items-center gap-1 disabled:opacity-40"
              >
                <Plus className="w-3 h-3" />
                <span>添加</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content Editor Section */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-2xs overflow-hidden">
        {/* Editor Toolbar & Tabs Header */}
        <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 bg-slate-50 border-b border-slate-200 text-xs">
          {/* Tabs */}
          <div className="flex items-center gap-1 bg-slate-200/70 p-0.5 rounded-lg">
            <button
              type="button"
              onClick={() => setTab('edit')}
              className={`px-3 py-1 rounded-md font-medium transition-colors flex items-center gap-1.5 ${
                tab === 'edit'
                  ? 'bg-white text-blue-600 shadow-2xs font-semibold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Edit3 className="w-3.5 h-3.5" />
              <span>编辑 Markdown</span>
            </button>
            <button
              type="button"
              onClick={() => setTab('preview')}
              className={`px-3 py-1 rounded-md font-medium transition-colors flex items-center gap-1.5 ${
                tab === 'preview'
                  ? 'bg-white text-blue-600 shadow-2xs font-semibold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Eye className="w-3.5 h-3.5" />
              <span>实时效果预览</span>
            </button>
          </div>

          {/* Quick Insert Snippet Buttons (Only in edit mode) */}
          {tab === 'edit' && (
            <div className="flex items-center gap-1 text-slate-600">
              <span className="text-[11px] text-slate-400 mr-1 select-none">快捷插入:</span>
              <button
                type="button"
                onClick={() => handleInsertSnippet('## 二级标题\n内容说明...')}
                className="p-1 hover:bg-slate-200 rounded text-slate-600"
                title="插入二级标题"
              >
                <Heading2 className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={() => handleInsertSnippet('- 列表项 1\n- 列表项 2')}
                className="p-1 hover:bg-slate-200 rounded text-slate-600"
                title="插入无序列表"
              >
                <List className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={() => handleInsertSnippet('```bash\n# 示例命令或配置\necho "Hello"\n```')}
                className="p-1 hover:bg-slate-200 rounded text-slate-600"
                title="插入代码块"
              >
                <Code className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={() => handleInsertSnippet('> [!NOTE]\n> 关键注意事项或引用说明')}
                className="p-1 hover:bg-slate-200 rounded text-slate-600"
                title="插入引用提示块"
              >
                <Quote className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={() =>
                  handleInsertSnippet(
                    '| 属性列 | 规格说明 |\n| :--- | :--- |\n| 参数 A | 说明 1 |\n| 参数 B | 说明 2 |'
                  )
                }
                className="p-1 hover:bg-slate-200 rounded text-slate-600"
                title="插入表格"
              >
                <TableIcon className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>

        {/* Tab Body */}
        {tab === 'edit' ? (
          <div className="p-4">
            <textarea
              rows={18}
              value={contentMarkdown}
              onChange={(e) => setContentMarkdown(e.target.value)}
              placeholder={`# 知识点正文\n\n在此输入 Markdown 内容。\n支持标题（#）、列表（- 或 1.）、代码块（\`\`\`）、引用（>）、表格（| a | b |）等，保存时系统将自动拆解为结构化 Block 树并生成向量索引。`}
              className="w-full p-3 font-mono text-xs text-slate-800 bg-transparent outline-none resize-y leading-relaxed border border-slate-100 rounded-lg focus:border-blue-400"
            />
          </div>
        ) : (
          <div className="p-6 prose prose-slate max-w-none text-xs leading-relaxed min-h-[350px]">
            {contentMarkdown ? (
              <div className="space-y-4">
                {markdownToBlocks(contentMarkdown).map((block) => (
                  <div key={block.id}>
                    {block.type === 'heading' && (
                      <h2 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-1 mt-4">
                        {String(block.content)}
                      </h2>
                    )}
                    {block.type === 'paragraph' && (
                      <p className="text-slate-700 leading-relaxed">{String(block.content)}</p>
                    )}
                    {block.type === 'list' && (
                      <div className="pl-4 flex items-start gap-2 text-slate-700">
                        <span className="text-blue-500 font-bold">•</span>
                        <span>{String(block.content)}</span>
                      </div>
                    )}
                    {block.type === 'quote' && (
                      <blockquote className="border-l-4 border-blue-500 pl-3 text-slate-600 italic bg-blue-50/30 py-1 rounded-r">
                        {String(block.content)}
                      </blockquote>
                    )}
                    {block.type === 'code' && (
                      <pre className="bg-slate-900 text-slate-100 p-3 rounded-lg overflow-x-auto text-[11px] font-mono">
                        <code>{String(block.content)}</code>
                      </pre>
                    )}
                    {block.type === 'divider' && <hr className="my-4 border-slate-200" />}
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-16 text-center text-slate-400">
                暂无正文内容，请在“编辑 Markdown”标签中录入内容。
              </div>
            )}
          </div>
        )}
      </div>
    </form>
  );
}
