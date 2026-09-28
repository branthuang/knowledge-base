import React from 'react';
import { CheckCircle2, AlertTriangle, Sparkles, ArrowRight } from 'lucide-react';

interface SufficiencyBannerProps {
  isSufficient: boolean;
  promptText?: string | null;
  onTriggerAISearch?: () => void;
  aiSearchLoading?: boolean;
  hasAIResult?: boolean;
}

export const SufficiencyBanner: React.FC<SufficiencyBannerProps> = ({
  isSufficient,
  promptText,
  onTriggerAISearch,
  aiSearchLoading = false,
  hasAIResult = false,
}) => {
  if (isSufficient) {
    return (
      <div className="p-4 bg-emerald-50/80 border border-emerald-200 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
          <div>
            <span className="text-xs font-bold text-emerald-900 block">
              本地知识库解答充分
            </span>
            <span className="text-xs text-emerald-700/90">
              Top-1 知识点综合匹配度已达到充分阈值 (≥ 60%)，优先查阅本地沉淀。
            </span>
          </div>
        </div>

        {!hasAIResult && onTriggerAISearch && (
          <button
            type="button"
            onClick={onTriggerAISearch}
            disabled={aiSearchLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-emerald-300 text-emerald-800 hover:bg-emerald-100 text-xs font-medium transition-colors shrink-0"
          >
            <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
            <span>{aiSearchLoading ? 'AI 检索中...' : '向公网/AI 扩展补充'}</span>
          </button>
        )}
      </div>
    );
  }

  // Insufficient banner
  return (
    <div className="p-4 bg-amber-50/90 border border-amber-200 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <div className="flex items-center gap-2.5">
        <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
        <div>
          <span className="text-xs font-bold text-amber-900 block">
            本地知识储备不足
          </span>
          <span className="text-xs text-amber-800/90">
            {promptText || '未检索到高匹配度知识，推荐向 AI / 公网提问以沉淀新知识。'}
          </span>
        </div>
      </div>

      {!hasAIResult && onTriggerAISearch && (
        <button
          type="button"
          onClick={onTriggerAISearch}
          disabled={aiSearchLoading}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs shadow-blue-500/20 transition-all shrink-0"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>{aiSearchLoading ? 'AI 正在分析思考...' : '立即向 AI / 公网提问'}</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
};
