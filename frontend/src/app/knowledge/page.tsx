'use client';

import React, { Suspense, useEffect, useState } from 'react';
import Link from 'next/link';
import { useSearchParams, useRouter } from 'next/navigation';
import {
  BookOpen,
  Search,
  Filter,
  PlusCircle,
  Star,
  Download,
  Trash2,
  Calendar,
  Tag as TagIcon,
  FolderTree,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Sparkles,
  LayoutList,
  LayoutGrid,
  Edit3,
} from 'lucide-react';
import { api } from '@/lib/api';
import { Category, KnowledgeListItem, PaginatedKnowledgeResponse, Tag } from '@/lib/types';

function KnowledgeListPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Filters state
  const initialStatus = searchParams.get('status') || '';
  const initialCategory = searchParams.get('category_id') || '';
  const initialKeyword = searchParams.get('keyword') || '';

  const [keyword, setKeyword] = useState(initialKeyword);
  const [status, setStatus] = useState<string>(initialStatus);
  const [categoryId, setCategoryId] = useState<string>(initialCategory);
  const [selectedTagId, setSelectedTagId] = useState<string>('');
  const [favoriteOnly, setFavoriteOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');
  const pageSize = 20;

  // Data state
  const [data, setData] = useState<PaginatedKnowledgeResponse | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Load categories and tags for filter dropdowns
  useEffect(() => {
    api.categories.list().then(setCategories).catch(console.error);
    api.tags.list().then(setTags).catch(console.error);
  }, []);

  const fetchKnowledge = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.knowledge.list({
        keyword: keyword.trim() || undefined,
        status: status || undefined,
        category_id: categoryId || undefined,
        tag_ids: selectedTagId ? [selectedTagId] : undefined,
        favorite: favoriteOnly || undefined,
        page,
        page_size: pageSize,
      });
      setData(res);
    } catch (err: any) {
      console.error('Failed to load knowledge list:', err);
      setError(err?.message || '获取知识列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKnowledge();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, categoryId, selectedTagId, favoriteOnly, page]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchKnowledge();
  };

  const handleToggleFavorite = async (item: KnowledgeListItem, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await api.knowledge.update(item.id, { favorite: !item.favorite });
      setData((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          items: prev.items.map((k) =>
            k.id === item.id ? { ...k, favorite: !k.favorite } : k
          ),
        };
      });
    } catch (err: any) {
      alert('更新收藏状态失败: ' + err.message);
    }
  };

  const handleDelete = async (item: KnowledgeListItem, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm(`确定将知识点《${item.title}》移入回收站吗？`)) {
      return;
    }
    try {
      setDeletingId(item.id);
      await api.knowledge.delete(item.id);
      fetchKnowledge();
    } catch (err: any) {
      alert('移入回收站失败: ' + err.message);
    } finally {
      setDeletingId(null);
    }
  };

  const handleExportMarkdown = (item: KnowledgeListItem, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const url = api.backup.exportMarkdownUrl(item.id);
    window.open(url, '_blank');
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
      {/* Header and Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 tracking-tight flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-blue-600" />
            <span>知识库列表</span>
          </h1>
          <p className="mt-0.5 text-xs text-slate-500">
            可持续积累、分类沉淀与结构化检索的个人知识资产库
          </p>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap">
          {/* View Mode Toggle */}
          <div className="flex items-center bg-slate-100 p-0.5 rounded-lg border border-slate-200">
            <button
              type="button"
              onClick={() => setViewMode('list')}
              className={`p-1.5 rounded-md transition-colors ${
                viewMode === 'list'
                  ? 'bg-white text-blue-600 shadow-2xs font-semibold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
              title="切换为列表视图"
            >
              <LayoutList className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded-md transition-colors ${
                viewMode === 'grid'
                  ? 'bg-white text-blue-600 shadow-2xs font-semibold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
              title="切换为卡片网格"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
          </div>

          <button
            onClick={() => fetchKnowledge()}
            disabled={loading}
            className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors border border-slate-200"
            title="刷新"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>

          <Link
            href="/search"
            className="flex items-center gap-1.5 px-3 py-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-medium transition-all shadow-2xs"
          >
            <Sparkles className="w-3.5 h-3.5 text-blue-600" />
            <span>AI 搜索沉淀</span>
          </Link>

          <Link
            href="/knowledge/new"
            className="flex items-center gap-1.5 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-all"
          >
            <PlusCircle className="w-4 h-4" />
            <span>新建知识点</span>
          </Link>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs space-y-3">
        {/* Top: Status Tabs + Search Input */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          {/* Status Tabs */}
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg">
            {[
              { id: '', label: '全部状态' },
              { id: 'published', label: '已发布' },
              { id: 'draft', label: '待整理草稿' },
              { id: 'archived', label: '已归档' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => {
                  setStatus(tab.id);
                  setPage(1);
                }}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  status === tab.id
                    ? 'bg-white text-blue-600 shadow-2xs font-semibold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Search Box */}
          <form onSubmit={handleSearchSubmit} className="flex gap-2 w-full md:w-80">
            <div className="relative flex-1 flex items-center bg-slate-50 border border-slate-200 rounded-lg focus-within:border-blue-500 focus-within:bg-white transition-all">
              <Search className="w-4 h-4 text-slate-400 ml-3 shrink-0" />
              <input
                type="text"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                placeholder="搜索标题或内容..."
                className="w-full py-1.5 px-2.5 text-xs text-slate-800 bg-transparent outline-none placeholder-slate-400"
              />
            </div>
            <button
              type="submit"
              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shrink-0"
            >
              检索
            </button>
          </form>
        </div>

        {/* Bottom: Category, Tag, and Favorite Filter Dropdowns */}
        <div className="flex flex-wrap items-center gap-3 pt-3 border-t border-slate-100 text-xs">
          <div className="flex items-center gap-1.5 text-slate-500 font-medium">
            <Filter className="w-3.5 h-3.5" />
            <span>筛选:</span>
          </div>

          {/* Category Dropdown */}
          <select
            value={categoryId}
            onChange={(e) => {
              setCategoryId(e.target.value);
              setPage(1);
            }}
            className="px-2.5 py-1 rounded-md border border-slate-200 text-slate-700 bg-white outline-none cursor-pointer text-xs"
          >
            <option value="">全部分类</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.knowledge_count})
              </option>
            ))}
          </select>

          {/* Tag Dropdown */}
          <select
            value={selectedTagId}
            onChange={(e) => {
              setSelectedTagId(e.target.value);
              setPage(1);
            }}
            className="px-2.5 py-1 rounded-md border border-slate-200 text-slate-700 bg-white outline-none cursor-pointer text-xs"
          >
            <option value="">全部标签</option>
            {tags.map((t) => (
              <option key={t.id} value={t.id}>
                #{t.name}
              </option>
            ))}
          </select>

          {/* Favorite Toggle */}
          <label className="flex items-center gap-1.5 cursor-pointer text-slate-600 hover:text-slate-900 ml-1">
            <input
              type="checkbox"
              checked={favoriteOnly}
              onChange={(e) => {
                setFavoriteOnly(e.target.checked);
                setPage(1);
              }}
              className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 w-3.5 h-3.5 cursor-pointer"
            />
            <Star className={`w-3 h-3 ${favoriteOnly ? 'text-amber-500 fill-amber-500' : 'text-slate-400'}`} />
            <span>仅看收藏</span>
          </label>

          {(categoryId || selectedTagId || favoriteOnly || keyword || status) && (
            <button
              onClick={() => {
                setCategoryId('');
                setSelectedTagId('');
                setFavoriteOnly(false);
                setKeyword('');
                setStatus('');
                setPage(1);
              }}
              className="text-[11px] text-blue-600 hover:underline ml-auto"
            >
              清除全部筛选
            </button>
          )}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700">
          {error}
        </div>
      )}

      {/* Knowledge Items Presentation */}
      {loading ? (
        <div className="py-20 text-center text-xs text-slate-400 flex flex-col items-center gap-2">
          <RefreshCw className="w-6 h-6 animate-spin text-blue-600" />
          <span>正在加载知识库资产...</span>
        </div>
      ) : data?.items.length === 0 ? (
        <div className="py-20 bg-white border border-slate-200 rounded-2xl text-center space-y-3">
          <div className="w-12 h-12 rounded-xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto">
            <BookOpen className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-semibold text-slate-700">暂无匹配知识</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            尝试放宽筛选条件，或在统一搜索中心中通过 AI 搜索将高价值结论一键沉淀入库。
          </p>
          <div className="flex items-center justify-center gap-3 pt-2">
            <Link
              href="/knowledge/new"
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>新建第一篇知识点</span>
            </Link>
            <Link
              href="/search"
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-lg text-xs font-semibold shadow-2xs"
            >
              <Sparkles className="w-3.5 h-3.5 text-blue-600" />
              <span>去搜索沉淀</span>
            </Link>
          </div>
        </div>
      ) : viewMode === 'list' ? (
        /* List View (Table Mode) */
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-semibold select-none">
                <tr>
                  <th className="py-3 px-3.5 w-10 text-center">收藏</th>
                  <th className="py-3 px-4 min-w-[280px]">标题与摘要</th>
                  <th className="py-3 px-4 w-32">分类</th>
                  <th className="py-3 px-4 min-w-[180px]">关联标签</th>
                  <th className="py-3 px-4 w-24">状态</th>
                  <th className="py-3 px-4 w-28">更新时间</th>
                  <th className="py-3 px-4 w-28 text-right">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data?.items.map((item) => (
                  <tr
                    key={item.id}
                    className="hover:bg-blue-50/30 transition-colors group"
                  >
                    {/* Favorite */}
                    <td className="py-3 px-3.5 text-center">
                      <button
                        type="button"
                        onClick={(e) => handleToggleFavorite(item, e)}
                        className="p-1 rounded-md text-slate-300 hover:text-amber-500 transition-colors"
                        title={item.favorite ? '取消收藏' : '加入收藏'}
                      >
                        <Star
                          className={`w-3.5 h-3.5 ${
                            item.favorite ? 'text-amber-500 fill-amber-500' : ''
                          }`}
                        />
                      </button>
                    </td>

                    {/* Title & Summary */}
                    <td className="py-3 px-4">
                      <Link
                        href={`/knowledge/${item.id}`}
                        className="font-semibold text-slate-800 group-hover:text-blue-600 transition-colors line-clamp-1 block text-sm"
                      >
                        {item.title}
                      </Link>
                      {item.summary && (
                        <p className="mt-0.5 text-[11px] text-slate-400 line-clamp-1 leading-snug">
                          {item.summary}
                        </p>
                      )}
                    </td>

                    {/* Category */}
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700">
                        <FolderTree className="w-3 h-3 text-slate-400" />
                        <span>{item.category_name || '未分类'}</span>
                      </span>
                    </td>

                    {/* Tags */}
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1 flex-wrap">
                        {item.tags?.slice(0, 3).map((tag) => (
                          <span
                            key={tag.id}
                            className="text-[10px] text-slate-600 bg-slate-50 px-1.5 py-0.5 rounded border border-slate-200"
                          >
                            #{tag.name}
                          </span>
                        ))}
                        {item.tags && item.tags.length > 3 && (
                          <span className="text-[10px] text-slate-400 font-medium">
                            +{item.tags.length - 3}
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Status */}
                    <td className="py-3 px-4 whitespace-nowrap">
                      {item.status === 'draft' ? (
                        <span className="inline-block text-[10px] font-semibold bg-amber-50 text-amber-700 px-2 py-0.5 rounded-full border border-amber-200">
                          草稿
                        </span>
                      ) : item.status === 'archived' ? (
                        <span className="inline-block text-[10px] font-semibold bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full border border-slate-200">
                          已归档
                        </span>
                      ) : (
                        <span className="inline-block text-[10px] font-semibold bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full border border-emerald-200">
                          已发布
                        </span>
                      )}
                    </td>

                    {/* Updated At */}
                    <td className="py-3 px-4 whitespace-nowrap text-slate-400 text-[11px]">
                      {new Date(item.updated_at).toLocaleDateString()}
                    </td>

                    {/* Actions */}
                    <td className="py-3 px-4 text-right whitespace-nowrap">
                      <div className="flex items-center justify-end gap-1">
                        <Link
                          href={`/knowledge/${item.id}/edit`}
                          className="p-1 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                          title="编辑知识点"
                        >
                          <Edit3 className="w-3.5 h-3.5" />
                        </Link>
                        <button
                          type="button"
                          onClick={(e) => handleExportMarkdown(item, e)}
                          className="p-1 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                          title="导出 Markdown"
                        >
                          <Download className="w-3.5 h-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={(e) => handleDelete(item, e)}
                          disabled={deletingId === item.id}
                          className="p-1 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded transition-colors"
                          title="移入回收站"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        /* Grid View (Card Mode) */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data?.items.map((item) => (
            <div
              key={item.id}
              className="bg-white border border-slate-200 hover:border-blue-400 rounded-xl p-5 shadow-xs hover:shadow-md transition-all group flex flex-col justify-between"
            >
              <div>
                {/* Card Top: Category, Status, Favorite */}
                <div className="flex items-center justify-between gap-2 mb-2.5">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[11px] font-medium bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
                      {item.category_name || '未分类'}
                    </span>
                    {item.status === 'draft' ? (
                      <span className="text-[10px] font-medium bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded">
                        草稿
                      </span>
                    ) : item.status === 'archived' ? (
                      <span className="text-[10px] font-medium bg-slate-200 text-slate-700 px-1.5 py-0.5 rounded">
                        已归档
                      </span>
                    ) : (
                      <span className="text-[10px] font-medium bg-emerald-50 text-emerald-700 px-1.5 py-0.5 rounded">
                        已发布
                      </span>
                    )}
                  </div>

                  <button
                    type="button"
                    onClick={(e) => handleToggleFavorite(item, e)}
                    className="p-1 rounded-md text-slate-300 hover:text-amber-500 hover:bg-slate-50 transition-colors"
                    title={item.favorite ? '取消收藏' : '加入收藏'}
                  >
                    <Star
                      className={`w-4 h-4 ${
                        item.favorite ? 'text-amber-400 fill-amber-400' : ''
                      }`}
                    />
                  </button>
                </div>

                {/* Title */}
                <Link
                  href={`/knowledge/${item.id}`}
                  className="text-sm font-bold text-slate-800 group-hover:text-blue-600 transition-colors line-clamp-2 leading-snug block"
                >
                  {item.title}
                </Link>

                {/* Summary */}
                {item.summary && (
                  <p className="mt-2 text-xs text-slate-500 line-clamp-2 leading-relaxed font-normal">
                    {item.summary}
                  </p>
                )}

                {/* Tags */}
                {item.tags && item.tags.length > 0 && (
                  <div className="mt-3 flex items-center gap-1.5 flex-wrap">
                    {item.tags.slice(0, 3).map((tag) => (
                      <span
                        key={tag.id}
                        className="text-[10px] text-slate-500 bg-slate-50 px-2 py-0.5 rounded border border-slate-100"
                      >
                        #{tag.name}
                      </span>
                    ))}
                    {item.tags.length > 3 && (
                      <span className="text-[10px] text-slate-400">
                        +{item.tags.length - 3}
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Card Footer: Metadata and Quick Actions */}
              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
                <div className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  <span>{new Date(item.updated_at).toLocaleDateString()}</span>
                </div>

                <div className="flex items-center gap-1 opacity-80 group-hover:opacity-100 transition-opacity">
                  <Link
                    href={`/knowledge/${item.id}/edit`}
                    className="p-1 text-slate-400 hover:text-blue-600 hover:bg-slate-100 rounded"
                    title="编辑知识点"
                  >
                    <Edit3 className="w-3.5 h-3.5" />
                  </Link>
                  <button
                    type="button"
                    onClick={(e) => handleExportMarkdown(item, e)}
                    className="p-1 text-slate-400 hover:text-blue-600 hover:bg-slate-100 rounded"
                    title="导出 Markdown"
                  >
                    <Download className="w-3.5 h-3.5" />
                  </button>
                  <button
                    type="button"
                    onClick={(e) => handleDelete(item, e)}
                    disabled={deletingId === item.id}
                    className="p-1 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded"
                    title="移入回收站"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination Controls */}
      {data && data.pages > 1 && (
        <div className="flex items-center justify-between pt-4 border-t border-slate-200 text-xs text-slate-500">
          <div>
            第 <span className="font-semibold">{data.page}</span> /{' '}
            <span className="font-semibold">{data.pages}</span> 页 (共 {data.total} 篇)
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="p-1.5 rounded border border-slate-200 text-slate-600 hover:bg-slate-100 disabled:opacity-40 disabled:hover:bg-transparent"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
              disabled={page >= data.pages}
              className="p-1.5 rounded border border-slate-200 text-slate-600 hover:bg-slate-100 disabled:opacity-40 disabled:hover:bg-transparent"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function KnowledgeListPage() {
  return (
    <Suspense
      fallback={
        <div className="p-12 text-center text-xs text-slate-400">
          加载知识库列表中...
        </div>
      }
    >
      <KnowledgeListPageContent />
    </Suspense>
  );
}
