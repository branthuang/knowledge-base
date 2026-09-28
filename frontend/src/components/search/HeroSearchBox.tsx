import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Search, Sparkles, ArrowRight, CornerDownLeft } from 'lucide-react';

interface HeroSearchBoxProps {
  initialQuery?: string;
  placeholder?: string;
}

export const HeroSearchBox: React.FC<HeroSearchBoxProps> = ({
  initialQuery = '',
  placeholder = '先查本地知识，再向 AI / 公网提问... 回车立即探索',
}) => {
  const router = useRouter();
  const [query, setQuery] = useState(initialQuery);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;
    router.push(`/search?q=${encodeURIComponent(trimmed)}`);
  };

  const handleQuickSearch = (keyword: string) => {
    setQuery(keyword);
    router.push(`/search?q=${encodeURIComponent(keyword)}`);
  };

  return (
    <div className="w-full max-w-3xl mx-auto">
      <form onSubmit={handleSubmit} className="relative group">
        <div className="relative flex items-center bg-white rounded-2xl border border-slate-200 shadow-md shadow-slate-200/50 group-hover:border-blue-400 group-focus-within:border-blue-500 group-focus-within:ring-4 group-focus-within:ring-blue-500/10 transition-all duration-200">
          <div className="pl-5 pr-3 text-slate-400 group-focus-within:text-blue-600 transition-colors">
            <Search className="w-6 h-6" />
          </div>

          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={placeholder}
            className="w-full py-4 text-base text-slate-800 placeholder-slate-400 bg-transparent outline-none font-normal"
            autoFocus
          />

          <div className="pr-3 flex items-center gap-2">
            <button
              type="submit"
              disabled={!query.trim()}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:bg-slate-200 text-white disabled:text-slate-400 font-medium text-sm transition-all shadow-sm shadow-blue-500/20 disabled:shadow-none"
            >
              <span>搜索</span>
              <CornerDownLeft className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </form>

      {/* Suggested Quick Queries */}
      <div className="mt-3 flex items-center justify-between text-xs text-slate-400 px-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="flex items-center gap-1 text-slate-500 font-medium">
            <Sparkles className="w-3.5 h-3.5 text-blue-500" />
            推荐探索:
          </span>
          {['FastAPI 最佳实践', 'PostgreSQL 向量检索', 'Docker 容器化部署'].map((chip) => (
            <button
              key={chip}
              type="button"
              onClick={() => handleQuickSearch(chip)}
              className="px-2.5 py-1 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-600 transition-colors text-xs"
            >
              {chip}
            </button>
          ))}
        </div>
        <span className="hidden sm:inline-block text-slate-400">
          优先匹配本地库，不足时自动连网 AI 综合沉淀
        </span>
      </div>
    </div>
  );
};
