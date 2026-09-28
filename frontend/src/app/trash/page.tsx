'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Trash2,
  RotateCcw,
  AlertTriangle,
  RefreshCw,
  ArrowLeft,
  Calendar,
  BookOpen,
  CheckCircle,
} from 'lucide-react';
import { api } from '@/lib/api';
import { KnowledgeListItem, PaginatedKnowledgeResponse } from '@/lib/types';

export default function TrashPage() {
  const [data, setData] = useState<PaginatedKnowledgeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [page, setPage] = useState(1);

  const fetchTrash = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.knowledge.listTrash(page, 20);
      setData(res);
    } catch (err: any) {
      console.error('Failed to load trash:', err);
      setError(err?.message || '获取回收站列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrash();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const handleRestore = async (item: KnowledgeListItem) => {
    try {
      setActionLoadingId(item.id);
      setError(null);
      await api.knowledge.restoreTrash(item.id);
      setSuccessMsg(`知识《${item.title}》已成功恢复到知识库！`);
      setTimeout(() => setSuccessMsg(null), 4000);
      fetchTrash();
    } catch (err: any) {
      alert('恢复失败: ' + err.message);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handlePermanentDelete = async (item: KnowledgeListItem) => {
    if (
      !confirm(
        `【不可撤回】确定要彻底永久删除知识点《${item.title}》吗？该操作将从数据库和向量索引中彻底清除！`
      )
    ) {
      return;
    }

    try {
      setActionLoadingId(item.id);
      setError(null);
      await api.knowledge.permanentDelete(item.id);
      setSuccessMsg(`知识《${item.title}》已被彻底物理删除。`);
      setTimeout(() => setSuccessMsg(null), 4000);
      fetchTrash();
    } catch (err: any) {
      alert('永久删除失败: ' + err.message);
    } finally {
      setActionLoadingId(null);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-6 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link
              href="/knowledge"
              className="text-xs text-slate-500 hover:text-blue-600 flex items-center gap-1"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>返回知识库</span>
            </Link>
          </div>
          <h1 className="text-2xl font-bold text-slate-800 tracking-tight flex items-center gap-2">
            <Trash2 className="w-6 h-6 text-rose-600" />
            <span>安全回收站</span>
          </h1>
          <p className="mt-0.5 text-xs text-slate-500">
            软删除的知识点在此安全保留，可随时一键恢复到知识库，或在此彻底永久清除
          </p>
        </div>

        <button
          onClick={fetchTrash}
          disabled={loading}
          className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors border border-slate-200 self-start sm:self-auto"
          title="刷新"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Success Notification */}
      {successMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center gap-2 animate-in fade-in">
          <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
          <span className="font-semibold">{successMsg}</span>
        </div>
      )}

      {/* Error Notification */}
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700">
          {error}
        </div>
      )}

      {/* Main Trash Content */}
      <div className="bg-white border border-slate-200 rounded-2xl shadow-xs overflow-hidden">
        {loading ? (
          <div className="py-20 text-center text-xs text-slate-400 flex flex-col items-center gap-2">
            <RefreshCw className="w-6 h-6 animate-spin text-rose-600" />
            <span>加载回收站数据中...</span>
          </div>
        ) : data?.items.length === 0 ? (
          <div className="py-20 text-center space-y-3">
            <div className="w-12 h-12 rounded-xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto">
              <Trash2 className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-semibold text-slate-700">
              回收站为空
            </h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              当前没有被软删除的知识点，全部知识资产完好保存在知识库中。
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {data?.items.map((item) => {
              const isBusy = actionLoadingId === item.id;
              return (
                <div
                  key={item.id}
                  className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-50/50 transition-colors"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[11px] font-medium bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
                        {item.category_name || '未分类'}
                      </span>
                      <span className="text-[10px] text-rose-700 bg-rose-50 border border-rose-200 px-1.5 py-0.2 rounded font-medium">
                        已放入回收站
                      </span>
                    </div>

                    <h3 className="text-sm font-bold text-slate-800 line-clamp-1">
                      {item.title}
                    </h3>

                    {item.summary && (
                      <p className="mt-1 text-xs text-slate-500 line-clamp-1">
                        {item.summary}
                      </p>
                    )}

                    <div className="mt-2 flex items-center gap-3 text-[11px] text-slate-400">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        删除时间: {new Date(item.updated_at).toLocaleString()}
                      </span>
                      <span>
                        来源: {item.source_type === 'ai_search' ? 'AI 搜索沉淀' : '人工编写'}
                      </span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      type="button"
                      onClick={() => handleRestore(item)}
                      disabled={isBusy}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-2xs transition-all disabled:opacity-50"
                    >
                      <RotateCcw className="w-3.5 h-3.5 text-blue-600" />
                      <span>{isBusy ? '处理中...' : '还原知识点'}</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => handlePermanentDelete(item)}
                      disabled={isBusy}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-rose-200 bg-rose-50/50 hover:bg-rose-100 text-rose-700 text-xs font-semibold transition-all disabled:opacity-50"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      <span>彻底删除</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
