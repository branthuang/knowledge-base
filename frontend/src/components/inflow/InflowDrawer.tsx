'use client';

import React, { useEffect, useState } from 'react';
import {
  X,
  Sparkles,
  AlertTriangle,
  FolderTree,
  Tag as TagIcon,
  Layers,
  FileCheck2,
  RefreshCw,
  BookOpen,
} from 'lucide-react';
import { api } from '@/lib/api';
import {
  AISearchResponse,
  Category,
  InflowPreviewResponse,
  KnowledgeDetail,
  Tag,
} from '@/lib/types';

interface InflowDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  aiResponse: AISearchResponse | null;
  onSuccess: (savedKnowledge: KnowledgeDetail) => void;
}

export const InflowDrawer: React.FC<InflowDrawerProps> = ({
  isOpen,
  onClose,
  aiResponse,
  onSuccess,
}) => {
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [preview, setPreview] = useState<InflowPreviewResponse | null>(null);

  // Form states
  const [title, setTitle] = useState('');
  const [summary, setSummary] = useState('');
  const [categoryId, setCategoryId] = useState<string>('');
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>([]);
  const [action, setAction] = useState<'create_new' | 'update_existing'>('create_new');
  const [targetKnowledgeId, setTargetKnowledgeId] = useState<string>('');
  const [status, setStatus] = useState<'published' | 'draft'>('published');
  const [error, setError] = useState<string | null>(null);

  // Metadata categories and tags
  const [categories, setCategories] = useState<Category[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);

  useEffect(() => {
    if (!isOpen || !aiResponse) return;

    // Load categories and tags
    api.categories.list().then(setCategories).catch(console.error);
    api.tags.list().then(setTags).catch(console.error);

    // Fetch inflow preview
    setLoading(true);
    setError(null);
    api.inflow
      .preview({
        session_id: aiResponse.session_id,
        query: aiResponse.query,
        content_markdown: aiResponse.ai_answer,
        citations: aiResponse.citations,
      })
      .then((res) => {
        setPreview(res);
        setTitle(res.recommended_title || aiResponse.query);
        setSummary(res.recommended_summary || '');
        setCategoryId(res.recommended_category_id || '');
        setSelectedTagIds(res.recommended_tag_ids || []);

        if (res.has_similar_knowledge && res.similar_candidates.length > 0) {
          setTargetKnowledgeId(res.similar_candidates[0].id);
        }
      })
      .catch((err) => {
        console.error('Failed to load inflow preview:', err);
        setError(err.message || '加载入库预览失败');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [isOpen, aiResponse]);

  if (!isOpen) return null;

  const handleTagToggle = (tagId: string) => {
    setSelectedTagIds((prev) =>
      prev.includes(tagId) ? prev.filter((id) => id !== tagId) : [...prev, tagId]
    );
  };

  const handleConfirm = async () => {
    if (!title.trim()) {
      setError('请输入知识点标题');
      return;
    }
    if (!preview) return;

    try {
      setSubmitting(true);
      setError(null);

      const saved = await api.inflow.confirm({
        session_id: preview.session_id || aiResponse?.session_id,
        action,
        target_knowledge_id: action === 'update_existing' ? targetKnowledgeId : undefined,
        title: title.trim(),
        summary: summary.trim(),
        blocks: preview.blocks,
        category_id: categoryId || undefined,
        tag_ids: selectedTagIds,
        sources: preview.sources,
        status,
      });

      onSuccess(saved);
      onClose();
    } catch (err: any) {
      console.error('Inflow confirm failed:', err);
      setError(err?.message || '确认入库失败');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/40 backdrop-blur-xs flex justify-end">
      {/* Drawer Container */}
      <div className="w-full max-w-2xl bg-white h-full shadow-2xl flex flex-col justify-between border-l border-slate-200 animate-in slide-in-from-right duration-300">
        {/* Drawer Header */}
        <div className="h-16 px-6 border-b border-slate-200 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center shadow-xs">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-800">
                知识沉淀入库确认
              </h2>
              <p className="text-xs text-slate-400">
                结构化解析、元数据推荐与防重核验
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Drawer Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading ? (
            <div className="py-20 flex flex-col items-center justify-center gap-3 text-slate-400">
              <RefreshCw className="w-6 h-6 animate-spin text-blue-600" />
              <span className="text-sm font-medium">正在解析内容块并推荐分类与标签...</span>
            </div>
          ) : error && !preview ? (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-sm">
              {error}
            </div>
          ) : (
            <>
              {/* High-Similarity Duplicate Alert */}
              {preview?.has_similar_knowledge && (
                <div className="p-4 bg-amber-50 border border-amber-300 rounded-xl space-y-3">
                  <div className="flex items-center gap-2 text-amber-900 font-bold text-xs">
                    <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                    <span>检测到库内已存在高度相似知识点 (相似度 ≥ 75%)</span>
                  </div>

                  <div className="text-xs text-amber-800">
                    为避免知识库冗余分散，您可以选择覆盖更新已有知识，或坚持作为新知识入库：
                  </div>

                  {preview.similar_candidates.map((cand) => (
                    <div
                      key={cand.id}
                      className="p-2.5 bg-white/80 border border-amber-200 rounded-lg text-xs flex items-center justify-between"
                    >
                      <div className="min-w-0 pr-2">
                        <span className="font-semibold text-slate-800 block truncate">
                          {cand.title}
                        </span>
                        <span className="text-[11px] text-slate-500 line-clamp-1">
                          {cand.snippet}
                        </span>
                      </div>
                      <span className="shrink-0 font-mono font-bold text-amber-700 bg-amber-100 px-2 py-0.5 rounded text-[11px]">
                        相似度 {Math.round(cand.similarity_score * 100)}%
                      </span>
                    </div>
                  ))}

                  {/* Action Radios */}
                  <div className="flex items-center gap-4 pt-1">
                    <label className="flex items-center gap-1.5 text-xs text-slate-700 cursor-pointer">
                      <input
                        type="radio"
                        name="inflow_action"
                        value="create_new"
                        checked={action === 'create_new'}
                        onChange={() => setAction('create_new')}
                        className="text-blue-600"
                      />
                      <span>创建为新知识点</span>
                    </label>

                    <label className="flex items-center gap-1.5 text-xs text-slate-700 cursor-pointer">
                      <input
                        type="radio"
                        name="inflow_action"
                        value="update_existing"
                        checked={action === 'update_existing'}
                        onChange={() => setAction('update_existing')}
                        className="text-blue-600"
                      />
                      <span>覆盖更新已有知识点</span>
                    </label>
                  </div>
                </div>
              )}

              {/* Title Input */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700">
                  知识点标题 <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="请输入标题..."
                  className="w-full px-3.5 py-2.5 rounded-lg border border-slate-200 text-sm font-semibold text-slate-800 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/10 outline-none"
                />
              </div>

              {/* Summary Textarea */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700">
                  知识摘要 (可留空或自行润色)
                </label>
                <textarea
                  rows={2}
                  value={summary}
                  onChange={(e) => setSummary(e.target.value)}
                  placeholder="推荐摘要..."
                  className="w-full px-3.5 py-2 rounded-lg border border-slate-200 text-xs text-slate-700 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/10 outline-none resize-none"
                />
              </div>

              {/* Category Selector */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700 flex items-center gap-1">
                  <FolderTree className="w-3.5 h-3.5 text-slate-400" />
                  <span>归属分类</span>
                </label>
                <select
                  value={categoryId}
                  onChange={(e) => setCategoryId(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-lg border border-slate-200 text-xs text-slate-700 focus:border-blue-500 outline-none bg-white cursor-pointer"
                >
                  <option value="">未分类 (Unclassified)</option>
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Tag Selector */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700 flex items-center gap-1">
                  <TagIcon className="w-3.5 h-3.5 text-slate-400" />
                  <span>关联标签</span>
                </label>
                <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto p-1 border border-slate-100 rounded-lg">
                  {tags.map((tag) => {
                    const isSelected = selectedTagIds.includes(tag.id);
                    return (
                      <button
                        key={tag.id}
                        type="button"
                        onClick={() => handleTagToggle(tag.id)}
                        className={`text-xs px-2.5 py-1 rounded-md transition-all ${
                          isSelected
                            ? 'bg-blue-600 text-white font-medium shadow-xs'
                            : 'bg-slate-100 hover:bg-slate-200 text-slate-600'
                        }`}
                      >
                        #{tag.name}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Blocks Structure Preview */}
              <div className="space-y-2 pt-2 border-t border-slate-100">
                <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
                  <span className="flex items-center gap-1">
                    <Layers className="w-3.5 h-3.5 text-blue-600" />
                    <span>结构化内容块预览 ({preview?.blocks.length || 0} Blocks)</span>
                  </span>
                  <span className="text-[11px] text-slate-400 font-normal">
                    包含标题、正文与底部引用资料块
                  </span>
                </div>

                <div className="max-h-48 overflow-y-auto space-y-1.5 p-2 bg-slate-50 border border-slate-200 rounded-lg">
                  {preview?.blocks.map((block, idx) => (
                    <div
                      key={block.id || idx}
                      className="px-2.5 py-1.5 bg-white rounded border border-slate-100 text-xs flex items-center justify-between"
                    >
                      <span className="text-slate-700 line-clamp-1">
                        {typeof block.content === 'string'
                          ? block.content
                          : JSON.stringify(block.content)}
                      </span>
                      <span className="font-mono text-[10px] text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded ml-2 shrink-0">
                        {block.type}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Status Selector */}
              <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
                <span className="text-xs font-bold text-slate-700">入库发布状态</span>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setStatus('published')}
                    className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                      status === 'published'
                        ? 'bg-emerald-600 text-white shadow-xs'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    直接发布
                  </button>
                  <button
                    type="button"
                    onClick={() => setStatus('draft')}
                    className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                      status === 'draft'
                        ? 'bg-amber-500 text-white shadow-xs'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    存为待整理草稿
                  </button>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Drawer Footer Actions */}
        <div className="h-16 px-6 border-t border-slate-200 flex items-center justify-between bg-slate-50/50">
          <button
            type="button"
            onClick={onClose}
            disabled={submitting}
            className="px-4 py-2 rounded-lg border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
          >
            取消
          </button>

          <button
            type="button"
            onClick={handleConfirm}
            disabled={submitting || loading || !preview}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-md shadow-blue-500/25 transition-all disabled:opacity-50"
          >
            <FileCheck2 className="w-4 h-4" />
            <span>{submitting ? '正在确认入库并建立索引...' : '确认沉淀入库'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
