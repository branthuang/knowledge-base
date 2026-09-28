'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import {
  ArrowLeft,
  Calendar,
  Download,
  Trash2,
  Star,
  ExternalLink,
  Sparkles,
  BookOpen,
  FolderTree,
  Tag as TagIcon,
  RefreshCw,
  Copy,
  Check,
  FileText,
  AlertCircle,
  Info,
  CheckCircle2,
} from 'lucide-react';
import { api } from '@/lib/api';
import { BlockItem, KnowledgeDetail } from '@/lib/types';

export default function KnowledgeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [item, setItem] = useState<KnowledgeDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copiedCodeId, setCopiedCodeId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const fetchDetail = async () => {
    if (!id) return;
    try {
      setLoading(true);
      setError(null);
      const res = await api.knowledge.get(id);
      setItem(res);
    } catch (err: any) {
      console.error('Failed to load knowledge detail:', err);
      setError(err?.message || '获取知识点详情失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const handleToggleFavorite = async () => {
    if (!item) return;
    try {
      const updated = await api.knowledge.update(item.id, { favorite: !item.favorite });
      setItem((prev) => (prev ? { ...prev, favorite: updated.favorite } : prev));
    } catch (err: any) {
      alert('更新收藏状态失败: ' + err.message);
    }
  };

  const handleDelete = async () => {
    if (!item) return;
    if (!confirm(`确定将知识点《${item.title}》移入回收站吗？`)) return;
    try {
      setDeleting(true);
      await api.knowledge.delete(item.id);
      router.push('/knowledge');
    } catch (err: any) {
      alert('移入回收站失败: ' + err.message);
      setDeleting(false);
    }
  };

  const handleExportMarkdown = () => {
    if (!item) return;
    window.open(api.backup.exportMarkdownUrl(item.id), '_blank');
  };

  const handleCopyCode = (blockId: string, code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCodeId(blockId);
    setTimeout(() => setCopiedCodeId(null), 2000);
  };

  // Render individual BlockItem
  const renderBlock = (block: BlockItem) => {
    const contentText = typeof block.content === 'string' ? block.content : JSON.stringify(block.content);

    switch (block.type) {
      case 'heading': {
        const level = block.properties?.level || 2;
        if (level === 1) {
          return (
            <h1 key={block.id} className="text-2xl font-bold text-slate-900 mt-6 mb-3 tracking-tight">
              {contentText}
            </h1>
          );
        }
        if (level === 2) {
          return (
            <h2 key={block.id} className="text-xl font-bold text-slate-800 mt-5 mb-2.5 tracking-tight border-b border-slate-100 pb-1.5">
              {contentText}
            </h2>
          );
        }
        if (level === 3) {
          return (
            <h3 key={block.id} className="text-base font-bold text-slate-800 mt-4 mb-2">
              {contentText}
            </h3>
          );
        }
        return (
          <h4 key={block.id} className="text-sm font-bold text-slate-700 mt-3 mb-1.5">
            {contentText}
          </h4>
        );
      }

      case 'list': {
        const isOrdered = block.properties?.list_style === 'ordered';
        return (
          <div key={block.id} className="my-1.5 pl-5 flex items-start gap-2 text-sm text-slate-700 leading-relaxed">
            <span className="text-blue-500 font-bold select-none">•</span>
            <span>{contentText}</span>
          </div>
        );
      }

      case 'code': {
        const lang = block.properties?.language || 'plaintext';
        const isCopied = copiedCodeId === block.id;
        return (
          <div key={block.id} className="my-4 rounded-xl overflow-hidden bg-slate-900 text-slate-100 shadow-md">
            <div className="flex items-center justify-between px-4 py-2 bg-slate-800/80 border-b border-slate-700/60 text-xs">
              <span className="font-mono text-slate-300 font-medium">{lang}</span>
              <button
                type="button"
                onClick={() => handleCopyCode(block.id, contentText)}
                className="flex items-center gap-1 text-slate-400 hover:text-white transition-colors"
              >
                {isCopied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span className="text-[11px]">{isCopied ? '已复制' : '复制'}</span>
              </button>
            </div>
            <pre className="p-4 font-mono text-xs overflow-x-auto leading-relaxed text-slate-200">
              <code>{contentText}</code>
            </pre>
          </div>
        );
      }

      case 'quote':
        return (
          <blockquote
            key={block.id}
            className="my-3 pl-4 border-l-4 border-blue-500 bg-blue-50/40 py-2 pr-3 rounded-r-lg text-sm text-slate-700 italic"
          >
            {contentText}
          </blockquote>
        );

      case 'callout': {
        const tone = block.properties?.callout_tone || 'info';
        const isWarning = tone === 'warning';
        return (
          <div
            key={block.id}
            className={`my-3 p-3.5 rounded-xl border flex items-start gap-2.5 text-xs leading-relaxed ${
              isWarning
                ? 'bg-amber-50 border-amber-200 text-amber-900'
                : 'bg-blue-50 border-blue-200 text-blue-900'
            }`}
          >
            {isWarning ? (
              <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            ) : (
              <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
            )}
            <div>{contentText}</div>
          </div>
        );
      }

      case 'divider':
        return <hr key={block.id} className="my-6 border-slate-200" />;

      case 'paragraph':
      default:
        return (
          <p key={block.id} className="my-2.5 text-sm text-slate-700 leading-relaxed font-normal">
            {contentText}
          </p>
        );
    }
  };

  if (loading) {
    return (
      <div className="py-24 text-center text-slate-400 flex flex-col items-center gap-2">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-600" />
        <span className="text-xs">加载知识点详情中...</span>
      </div>
    );
  }

  if (error || !item) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-12 space-y-4">
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700">
          {error || '未找到该知识点'}
        </div>
        <Link
          href="/knowledge"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:underline"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>返回知识库列表</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8 space-y-6">
      {/* Top Navigation & Action Bar */}
      <div className="flex items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <Link
          href="/knowledge"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-blue-600 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>返回知识库列表</span>
        </Link>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleToggleFavorite}
            className={`flex items-center gap-1 px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors ${
              item.favorite
                ? 'border-amber-300 bg-amber-50 text-amber-800'
                : 'border-slate-200 text-slate-600 hover:bg-slate-100'
            }`}
          >
            <Star className={`w-3.5 h-3.5 ${item.favorite ? 'text-amber-500 fill-amber-500' : ''}`} />
            <span>{item.favorite ? '已收藏' : '收藏'}</span>
          </button>

          <button
            type="button"
            onClick={handleExportMarkdown}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-100 text-xs font-medium transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>导出 Markdown</span>
          </button>

          <button
            type="button"
            onClick={handleDelete}
            disabled={deleting}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-rose-200 text-rose-600 hover:bg-rose-50 text-xs font-medium transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>移入回收站</span>
          </button>
        </div>
      </div>

      {/* Title & Metadata Header */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 flex-wrap text-xs">
          <span className="font-semibold bg-slate-100 text-slate-700 px-2.5 py-0.5 rounded-md">
            {item.category_name || '未分类'}
          </span>

          {item.status === 'draft' ? (
            <span className="bg-amber-100 text-amber-800 px-2 py-0.5 rounded-md font-medium">
              草稿
            </span>
          ) : (
            <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-md font-medium">
              已发布
            </span>
          )}

          <span className="text-slate-400">
            来源: {item.source_type === 'ai_search' ? 'AI 搜索沉淀' : '人工编写'}
          </span>

          <span className="text-slate-400">
            索引: {item.index_status === 'indexed' ? '向量就绪' : item.index_status}
          </span>
        </div>

        <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight leading-tight">
          {item.title}
        </h1>

        {/* Tags List */}
        {item.tags && item.tags.length > 0 && (
          <div className="flex items-center gap-1.5 flex-wrap pt-1">
            {item.tags.map((tag) => (
              <span
                key={tag.id}
                className="text-xs text-slate-600 bg-slate-100 hover:bg-slate-200 px-2.5 py-0.5 rounded-md transition-colors"
              >
                #{tag.name}
              </span>
            ))}
          </div>
        )}

        <div className="text-xs text-slate-400 flex items-center gap-4 pt-1">
          <span>创建时间: {new Date(item.created_at).toLocaleString()}</span>
          <span>更新时间: {new Date(item.updated_at).toLocaleString()}</span>
        </div>
      </div>

      {/* Summary Banner (if exists) */}
      {item.summary && (
        <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 leading-relaxed">
          <span className="font-bold text-slate-800 mr-1.5">摘要:</span>
          {item.summary}
        </div>
      )}

      {/* Main Body Content Blocks */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-xs">
        {item.blocks_json && item.blocks_json.length > 0 ? (
          item.blocks_json.map((block) => renderBlock(block))
        ) : (
          <div className="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">
            {item.plain_text || '暂无正文内容'}
          </div>
        )}
      </div>

      {/* Bottom Sources & Citations Section */}
      {item.sources && item.sources.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
            <ExternalLink className="w-3.5 h-3.5 text-blue-600" />
            <span>参考来源与引用 ({item.sources.length})</span>
          </h3>

          <div className="space-y-2">
            {item.sources.map((src, idx) => (
              <div
                key={src.id || idx}
                className="p-3 bg-slate-50 border border-slate-100 rounded-lg text-xs flex items-center justify-between"
              >
                <div className="min-w-0 pr-3">
                  <span className="font-medium text-slate-800 block truncate">
                    {src.title || src.url || '参考来源'}
                  </span>
                  {src.url && (
                    <a
                      href={src.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[11px] text-blue-600 hover:underline flex items-center gap-1 mt-0.5 truncate"
                    >
                      <span className="truncate">{src.url}</span>
                      <ExternalLink className="w-3 h-3 shrink-0" />
                    </a>
                  )}
                </div>
                <span className="text-[10px] font-mono text-slate-400 bg-slate-200/60 px-2 py-0.5 rounded shrink-0">
                  {src.type}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
