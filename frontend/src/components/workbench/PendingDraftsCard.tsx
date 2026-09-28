import React from 'react';
import Link from 'next/link';
import { AlertCircle, ArrowRight, Clock, FileText } from 'lucide-react';
import { PendingReviewDraftItem } from '@/lib/types';

interface PendingDraftsCardProps {
  drafts: PendingReviewDraftItem[];
  totalCount: number;
}

export const PendingDraftsCard: React.FC<PendingDraftsCardProps> = ({ drafts, totalCount }) => {
  if (totalCount === 0) return null;

  return (
    <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between pb-3 border-b border-amber-200/60">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-amber-500 text-white flex items-center justify-center shadow-sm">
            <AlertCircle className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-amber-900">
              待整理入库草稿 ({totalCount})
            </h3>
            <p className="text-xs text-amber-700/80">
              由 AI 搜索暂存或自动导入，需用户确认发布或归档
            </p>
          </div>
        </div>

        <Link
          href="/knowledge?status=draft"
          className="text-xs font-semibold text-amber-800 hover:text-amber-950 flex items-center gap-1 group bg-white/70 hover:bg-white px-3 py-1.5 rounded-lg border border-amber-200 transition-all"
        >
          <span>查看全部草稿</span>
          <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
        </Link>
      </div>

      <div className="mt-3 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {drafts.slice(0, 3).map((draft) => (
          <Link
            key={draft.id}
            href={`/knowledge/${draft.id}`}
            className="block p-3.5 bg-white/90 hover:bg-white rounded-lg border border-amber-200/80 hover:border-amber-300 shadow-xs hover:shadow transition-all group"
          >
            <div className="flex items-start justify-between gap-2">
              <span className="text-xs font-semibold text-slate-800 group-hover:text-blue-600 line-clamp-1">
                {draft.title}
              </span>
              <span className="text-[10px] bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded font-medium shrink-0">
                草稿
              </span>
            </div>

            {draft.summary && (
              <p className="mt-1 text-xs text-slate-500 line-clamp-2 leading-relaxed">
                {draft.summary}
              </p>
            )}

            <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400">
              <span className="flex items-center gap-1">
                <FileText className="w-3 h-3" />
                {draft.category_name || '未分类'}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {new Date(draft.created_at).toLocaleDateString()}
              </span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};
