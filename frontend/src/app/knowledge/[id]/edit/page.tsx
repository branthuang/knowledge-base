'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { RefreshCw, AlertCircle, ArrowLeft } from 'lucide-react';
import { api } from '@/lib/api';
import { KnowledgeDetail } from '@/lib/types';
import KnowledgeEditorForm from '@/components/knowledge/KnowledgeEditorForm';

export default function EditKnowledgePage() {
  const params = useParams();
  const id = params?.id as string;

  const [item, setItem] = useState<KnowledgeDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    const fetchKnowledge = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await api.knowledge.get(id);
        setItem(res);
      } catch (err: any) {
        console.error('Failed to load knowledge for editing:', err);
        setError(err?.message || '获取知识点失败');
      } finally {
        setLoading(false);
      }
    };

    fetchKnowledge();
  }, [id]);

  if (loading) {
    return (
      <div className="py-24 text-center text-xs text-slate-400 flex flex-col items-center justify-center gap-3">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-600" />
        <span>正在加载知识点编辑数据...</span>
      </div>
    );
  }

  if (error || !item) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-12 text-center space-y-4">
        <div className="w-12 h-12 bg-rose-50 rounded-xl flex items-center justify-center text-rose-500 mx-auto">
          <AlertCircle className="w-6 h-6" />
        </div>
        <h2 className="text-base font-bold text-slate-800">无法加载知识点</h2>
        <p className="text-xs text-slate-500">{error || '知识点不存在或已被移入回收站'}</p>
        <Link
          href="/knowledge"
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium rounded-lg"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>返回知识库列表</span>
        </Link>
      </div>
    );
  }

  return <KnowledgeEditorForm mode="edit" initialData={item} />;
}
