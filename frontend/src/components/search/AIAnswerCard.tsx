import React from 'react';
import {
  Sparkles,
  ExternalLink,
  Bot,
  BookmarkPlus,
  BookCheck,
  Globe,
  Share2,
} from 'lucide-react';
import { AISearchResponse } from '@/lib/types';

interface AIAnswerCardProps {
  response: AISearchResponse;
  onOpenInflow: (response: AISearchResponse) => void;
  isSaved?: boolean;
}

export const AIAnswerCard: React.FC<AIAnswerCardProps> = ({
  response,
  onOpenInflow,
  isSaved = false,
}) => {
  return (
    <div className="bg-gradient-to-b from-blue-50/50 to-white border border-blue-200 rounded-2xl p-6 shadow-sm space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-blue-100">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center shadow-md shadow-blue-500/20">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-800">
                AI 综合搜索解答
              </h3>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-medium">
                {response.model_used || 'AI Engine'}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              基于本地知识融合与公网多源信息综合归纳
            </p>
          </div>
        </div>

        {/* Action Button: Inflow to Knowledge Base */}
        <div className="shrink-0">
          {isSaved ? (
            <div className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-semibold">
              <BookCheck className="w-4 h-4" />
              <span>已沉淀到知识库</span>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => onOpenInflow(response)}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 active:scale-95 text-white text-xs font-bold shadow-md shadow-blue-500/25 transition-all group"
            >
              <BookmarkPlus className="w-4 h-4 transition-transform group-hover:scale-110" />
              <span>确认沉淀到知识库</span>
            </button>
          )}
        </div>
      </div>

      {/* Main AI Answer Content */}
      <div className="prose prose-slate max-w-none text-sm leading-relaxed text-slate-700 whitespace-pre-wrap font-normal">
        {response.ai_answer}
      </div>

      {/* Local Knowledge References (if any) */}
      {response.local_hits && response.local_hits.length > 0 && (
        <div className="space-y-2 pt-2 border-t border-slate-100">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-700">
            <Bot className="w-3.5 h-3.5 text-blue-600" />
            <span>回答引用的本地知识库 ({response.local_hits.length})</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {response.local_hits.map((hit) => (
              <div
                key={hit.id}
                className="p-2.5 bg-slate-50 border border-slate-200/80 rounded-lg text-xs"
              >
                <div className="font-semibold text-slate-800 line-clamp-1">
                  {hit.title}
                </div>
                <div className="text-[11px] text-slate-500 line-clamp-1 mt-0.5">
                  {hit.snippet}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Public Citations List (可追溯外部公网引用列表) */}
      {response.citations && response.citations.length > 0 && (
        <div className="space-y-3 pt-3 border-t border-slate-100">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-700">
              <Globe className="w-3.5 h-3.5 text-blue-600" />
              <span>公网参考资料与可追溯引用 ({response.citations.length})</span>
            </div>
            <span className="text-[11px] text-slate-400">
              沉淀入库时将自动转为底部参考资料块
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
            {response.citations.map((cite, idx) => (
              <a
                key={idx}
                href={cite.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block p-3 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl transition-all shadow-2xs hover:border-blue-300 group"
              >
                <div className="flex items-center justify-between gap-1 text-[11px] text-slate-400 mb-1">
                  <span className="font-medium text-blue-600 truncate">
                    {cite.source_name || new URL(cite.url).hostname}
                  </span>
                  <ExternalLink className="w-3 h-3 text-slate-400 group-hover:text-blue-600 shrink-0" />
                </div>
                <div className="text-xs font-medium text-slate-800 group-hover:text-blue-600 line-clamp-1">
                  {cite.title}
                </div>
                {cite.snippet && (
                  <p className="text-[11px] text-slate-500 line-clamp-2 mt-1 leading-normal">
                    {cite.snippet}
                  </p>
                )}
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
