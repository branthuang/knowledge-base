import React from 'react';
import Link from 'next/link';
import { BookOpen, Star, Calendar, Hash, ArrowUpRight } from 'lucide-react';
import { SearchHitItem } from '@/lib/types';

interface LocalKnowledgeCardProps {
  item: SearchHitItem;
}

export const LocalKnowledgeCard: React.FC<LocalKnowledgeCardProps> = ({ item }) => {
  const percentScore = Math.round(item.score * 100);
  const percentKw = Math.round(item.keyword_score * 100);
  const percentVec = Math.round(item.vector_score * 100);

  // Score badge color
  let scoreBadgeColor = 'bg-slate-100 text-slate-700';
  if (percentScore >= 80) {
    scoreBadgeColor = 'bg-emerald-50 text-emerald-700 border-emerald-200';
  } else if (percentScore >= 60) {
    scoreBadgeColor = 'bg-blue-50 text-blue-700 border-blue-200';
  } else {
    scoreBadgeColor = 'bg-amber-50 text-amber-700 border-amber-200';
  }

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs hover:shadow-md hover:border-blue-300 transition-all group">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap mb-1.5">
            <span className="text-[11px] font-medium bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
              {item.category_name || '未分类'}
            </span>

            {item.favorite && (
              <span className="flex items-center gap-0.5 text-[10px] text-amber-600 font-medium">
                <Star className="w-3 h-3 fill-amber-400 text-amber-400" />
                收藏
              </span>
            )}

            {item.tags.map((tag) => (
              <span
                key={tag.id}
                className="text-[11px] text-slate-500 bg-slate-50 hover:bg-slate-100 px-2 py-0.5 rounded border border-slate-100"
              >
                #{tag.name}
              </span>
            ))}
          </div>

          <Link
            href={`/knowledge/${item.id}`}
            className="text-base font-bold text-slate-800 group-hover:text-blue-600 transition-colors flex items-center gap-1.5"
          >
            <span>{item.title}</span>
            <ArrowUpRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity text-blue-600" />
          </Link>
        </div>

        {/* Fused Match Score Badge */}
        <div className="flex flex-col items-end shrink-0">
          <div
            className={`px-2.5 py-1 rounded-lg text-xs font-bold border ${scoreBadgeColor} flex items-center gap-1`}
            title={`关键词: ${percentKw}% | 向量语义: ${percentVec}%`}
          >
            <span>匹配度</span>
            <span className="font-mono text-sm">{percentScore}%</span>
          </div>
          <div className="flex items-center gap-1.5 mt-1 text-[10px] text-slate-400 font-mono">
            <span>KW: {percentKw}%</span>
            <span>·</span>
            <span>VEC: {percentVec}%</span>
          </div>
        </div>
      </div>

      {/* Best Matched Snippet */}
      {item.best_snippet && (
        <div className="mt-3 p-3 bg-slate-50 border border-slate-100 rounded-lg text-xs text-slate-600 leading-relaxed font-normal">
          <span className="font-semibold text-slate-400 mr-1.5">命中片段:</span>
          {item.best_snippet}
        </div>
      )}

      {/* Card Footer */}
      <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
        <div className="flex items-center gap-1">
          <Calendar className="w-3 h-3" />
          <span>更新于 {new Date(item.updated_at).toLocaleDateString()}</span>
        </div>
        <span className="text-slate-400">
          来源: {item.source_type === 'ai_search' ? 'AI 搜索沉淀' : '人工编写'}
        </span>
      </div>
    </div>
  );
};
