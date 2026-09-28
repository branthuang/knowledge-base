'use client';

import React, { Suspense, useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import {
  Search as SearchIcon,
  Sparkles,
  BookOpen,
  RefreshCw,
  AlertCircle,
  CornerDownLeft,
  X,
  CheckCircle,
} from 'lucide-react';
import { api } from '@/lib/api';
import {
  AISearchResponse,
  KnowledgeDetail,
  SearchMode,
  SearchResponse,
} from '@/lib/types';
import { ModeSelector } from '@/components/search/ModeSelector';
import { FilterSidebar } from '@/components/search/FilterSidebar';
import { LocalKnowledgeCard } from '@/components/search/LocalKnowledgeCard';
import { SufficiencyBanner } from '@/components/search/SufficiencyBanner';
import { AIAnswerCard } from '@/components/search/AIAnswerCard';
import { InflowDrawer } from '@/components/inflow/InflowDrawer';

function SearchPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  // Search input state
  const initialQuery = searchParams.get('q') || '';
  const initialCategory = searchParams.get('category_id') || undefined;
  const initialTag = searchParams.get('tag') ? [searchParams.get('tag')!] : [];

  const [query, setQuery] = useState(initialQuery);
  const [mode, setMode] = useState<SearchMode>('knowledge_first');
  const [selectedCategoryId, setSelectedCategoryId] = useState<string | undefined>(initialCategory);
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>(initialTag);
  const [favoriteOnly, setFavoriteOnly] = useState(false);

  // Results state
  const [localSearchRes, setLocalSearchRes] = useState<SearchResponse | null>(null);
  const [aiSearchRes, setAiSearchRes] = useState<AISearchResponse | null>(null);
  const [loadingLocal, setLoadingLocal] = useState(false);
  const [loadingAI, setLoadingAI] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Inflow Drawer state
  const [inflowOpen, setInflowOpen] = useState(false);
  const [inflowSuccessMsg, setInflowSuccessMsg] = useState<string | null>(null);
  const [savedSessionIds, setSavedSessionIds] = useState<string[]>([]);

  // Execute Search pipeline based on mode
  const executeSearch = async (targetQuery: string, searchMode = mode) => {
    const trimmed = targetQuery.trim();
    if (!trimmed) return;

    setError(null);
    setLocalSearchRes(null);
    setAiSearchRes(null);

    // 1. If mode is DIRECT_AI
    if (searchMode === 'direct_ai') {
      try {
        setLoadingAI(true);
        const res = await api.aiSearch.ask({
          query: trimmed,
          mode: 'direct_ai',
          category_id: selectedCategoryId,
          tag_ids: selectedTagIds.length ? selectedTagIds : undefined,
        });
        setAiSearchRes(res);
      } catch (err: any) {
        setError(err.message || 'AI 搜索执行异常');
      } finally {
        setLoadingAI(false);
      }
      return;
    }

    // 2. Query Local Knowledge Base
    setLoadingLocal(true);
    let localResult: SearchResponse | null = null;
    try {
      localResult = await api.search.searchKnowledge({
        query: trimmed,
        category_id: selectedCategoryId,
        tag_ids: selectedTagIds.length ? selectedTagIds : undefined,
        favorite: favoriteOnly || undefined,
        minimum_score: 0.60,
      });
      setLocalSearchRes(localResult);
    } catch (err: any) {
      console.error('Local search failed:', err);
      setError(err.message || '本地检索失败');
    } finally {
      setLoadingLocal(false);
    }

    // 3. Handle External / AI Supplement
    if (searchMode === 'external_supplement') {
      // Force AI search regardless of local sufficiency
      triggerAISearch(trimmed, 'external_supplement');
    } else if (searchMode === 'knowledge_first') {
      // If local knowledge is insufficient, automatically trigger AI supplement
      if (localResult && !localResult.is_sufficient) {
        triggerAISearch(trimmed, 'knowledge_first');
      }
    }
  };

  const triggerAISearch = async (targetQuery = query, searchMode = mode) => {
    const trimmed = targetQuery.trim();
    if (!trimmed) return;

    try {
      setLoadingAI(true);
      const res = await api.aiSearch.ask({
        query: trimmed,
        mode: searchMode,
        category_id: selectedCategoryId,
        tag_ids: selectedTagIds.length ? selectedTagIds : undefined,
      });
      setAiSearchRes(res);
    } catch (err: any) {
      console.error('AI search failed:', err);
      setError(err.message || 'AI 增强提问异常');
    } finally {
      setLoadingAI(false);
    }
  };

  useEffect(() => {
    if (initialQuery) {
      executeSearch(initialQuery);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    executeSearch(query, mode);
  };

  const handleModeChange = (newMode: SearchMode) => {
    setMode(newMode);
    if (query.trim()) {
      executeSearch(query, newMode);
    }
  };

  const handleResetFilters = () => {
    setSelectedCategoryId(undefined);
    setSelectedTagIds([]);
    setFavoriteOnly(false);
    if (query.trim()) {
      executeSearch(query);
    }
  };

  const handleInflowSuccess = (saved: KnowledgeDetail) => {
    if (aiSearchRes) {
      setSavedSessionIds((prev) => [...prev, aiSearchRes.session_id]);
    }
    setInflowSuccessMsg(`知识《${saved.title}》已成功入库并生成向量索引！`);
    setTimeout(() => setInflowSuccessMsg(null), 5000);
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
      {/* Search Header and Input */}
      <div className="space-y-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 tracking-tight">
            统一搜索中心
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            融合本地关键词与语义双路召回，支持 AI 综合归纳与溯源入库
          </p>
        </div>

        {/* Search Bar & Mode Selector */}
        <div className="space-y-3">
          <form onSubmit={handleSearchSubmit} className="flex gap-2">
            <div className="relative flex-1 flex items-center bg-white rounded-xl border border-slate-200 shadow-xs focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/10 transition-all">
              <div className="pl-4 pr-2 text-slate-400">
                <SearchIcon className="w-5 h-5" />
              </div>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="输入自然语言问题或关键词搜索知识库..."
                className="w-full py-3 text-sm text-slate-800 bg-transparent outline-none placeholder-slate-400"
              />
              {query && (
                <button
                  type="button"
                  onClick={() => setQuery('')}
                  className="p-1 mr-2 text-slate-400 hover:text-slate-600 rounded-md"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            <button
              type="submit"
              disabled={!query.trim() || loadingLocal || loadingAI}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-200 text-white font-semibold text-sm rounded-xl shadow-xs shadow-blue-500/20 transition-all flex items-center gap-1.5 shrink-0"
            >
              <span>{loadingLocal || loadingAI ? '检索中...' : '搜索'}</span>
              <CornerDownLeft className="w-4 h-4" />
            </button>
          </form>

          {/* Mode Selector */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <ModeSelector currentMode={mode} onModeChange={handleModeChange} />
            <span className="text-[11px] text-slate-400">
              {mode === 'knowledge_first' && '知识优先: 本地库充分时直接展示；不足时自动触发 AI 增强回答'}
              {mode === 'knowledge_only' && '严格仅查本地库: 绝对不发起外部网络或 AI 请求'}
              {mode === 'external_supplement' && '外部补充: 强制同时召回本地知识与公网 AI 组织回答'}
              {mode === 'direct_ai' && '直接 AI: 由 AI 组织回答，侧边展示关联本地参考'}
            </span>
          </div>
        </div>
      </div>

      {/* Inflow Success Alert */}
      {inflowSuccessMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center justify-between animate-in fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-600" />
            <span className="font-semibold">{inflowSuccessMsg}</span>
          </div>
          <button
            onClick={() => setInflowSuccessMsg(null)}
            className="text-emerald-700 hover:text-emerald-900"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Main Layout: Filter Sidebar + Search Results */}
      <div className="flex flex-col lg:flex-row gap-6 items-start">
        {/* Left Filter Sidebar */}
        <FilterSidebar
          selectedCategoryId={selectedCategoryId}
          selectedTagIds={selectedTagIds}
          favoriteOnly={favoriteOnly}
          onCategoryChange={(catId) => {
            setSelectedCategoryId(catId);
            if (query.trim()) executeSearch(query);
          }}
          onTagToggle={(tagId) => {
            const next = selectedTagIds.includes(tagId)
              ? selectedTagIds.filter((id) => id !== tagId)
              : [...selectedTagIds, tagId];
            setSelectedTagIds(next);
            if (query.trim()) executeSearch(query);
          }}
          onFavoriteToggle={(fav) => {
            setFavoriteOnly(fav);
            if (query.trim()) executeSearch(query);
          }}
          onReset={handleResetFilters}
        />

        {/* Right Search Results Area */}
        <div className="flex-1 w-full space-y-6">
          {error && (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* AI Answer Card (if present or loading) */}
          {loadingAI ? (
            <div className="p-8 bg-blue-50/40 border border-blue-200 rounded-2xl flex flex-col items-center justify-center gap-3 text-slate-500">
              <RefreshCw className="w-6 h-6 animate-spin text-blue-600" />
              <span className="text-xs font-medium">
                AI 正在阅读本地知识与公网资讯，组织综合回答中...
              </span>
            </div>
          ) : (
            aiSearchRes && (
              <AIAnswerCard
                response={aiSearchRes}
                onOpenInflow={() => setInflowOpen(true)}
                isSaved={savedSessionIds.includes(aiSearchRes.session_id)}
              />
            )
          )}

          {/* Sufficiency Indicator Banner */}
          {localSearchRes && mode !== 'direct_ai' && (
            <SufficiencyBanner
              isSufficient={localSearchRes.is_sufficient}
              promptText={localSearchRes.ai_search_prompt}
              onTriggerAISearch={() => triggerAISearch(query, 'external_supplement')}
              aiSearchLoading={loadingAI}
              hasAIResult={!!aiSearchRes}
            />
          )}

          {/* Local Knowledge Search Hits */}
          {mode !== 'direct_ai' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-slate-200">
                <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-blue-600" />
                  <span>本地知识库检索结果</span>
                  {localSearchRes && (
                    <span className="text-xs font-mono font-normal text-slate-400">
                      (共 {localSearchRes.total} 条命中)
                    </span>
                  )}
                </h3>
              </div>

              {loadingLocal ? (
                <div className="py-12 text-center text-xs text-slate-400 flex flex-col items-center gap-2">
                  <RefreshCw className="w-5 h-5 animate-spin text-slate-400" />
                  <span>正在执行关键词与向量语义双路融合召回...</span>
                </div>
              ) : localSearchRes && localSearchRes.items.length > 0 ? (
                <div className="space-y-3">
                  {localSearchRes.items.map((item) => (
                    <LocalKnowledgeCard key={item.id} item={item} />
                  ))}
                </div>
              ) : localSearchRes && localSearchRes.items.length === 0 ? (
                <div className="py-12 bg-white rounded-xl border border-slate-200 text-center space-y-2">
                  <p className="text-sm font-medium text-slate-600">
                    本地知识库未检索到相关内容
                  </p>
                  <p className="text-xs text-slate-400">
                    您可以调整关键词、放宽分类/标签筛选，或切换至“外部补充”模式提问 AI
                  </p>
                </div>
              ) : null}
            </div>
          )}
        </div>
      </div>

      {/* Inflow Drawer Component */}
      <InflowDrawer
        isOpen={inflowOpen}
        onClose={() => setInflowOpen(false)}
        aiResponse={aiSearchRes}
        onSuccess={handleInflowSuccess}
      />
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense
      fallback={
        <div className="p-12 text-center text-xs text-slate-400">
          加载搜索中心中...
        </div>
      }
    >
      <SearchPageContent />
    </Suspense>
  );
}
