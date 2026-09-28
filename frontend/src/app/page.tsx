'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  BookOpen,
  FolderTree,
  Tag as TagIcon,
  TrendingUp,
  Sparkles,
  Clock,
  History,
  ArrowRight,
  ExternalLink,
  RefreshCw,
  PlusCircle,
} from 'lucide-react';
import { api } from '@/lib/api';
import {
  WorkbenchStatsResponse,
  WorkbenchActivitiesResponse,
} from '@/lib/types';
import { StatCard } from '@/components/workbench/StatCard';
import { PendingDraftsCard } from '@/components/workbench/PendingDraftsCard';
import { HeroSearchBox } from '@/components/search/HeroSearchBox';

export default function WorkbenchPage() {
  const router = useRouter();
  const [stats, setStats] = useState<WorkbenchStatsResponse | null>(null);
  const [activities, setActivities] = useState<WorkbenchActivitiesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [statsRes, actRes] = await Promise.all([
        api.workbench.getStats(),
        api.workbench.getActivities(),
      ]);
      setStats(statsRes);
      setActivities(actRes);
    } catch (err: any) {
      console.error('Failed to load dashboard data:', err);
      setError(err?.message || '连接后端服务失败，请检查 FastAPI 服务状态');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  return (
    <div className="max-w-6xl mx-auto px-6 py-8 space-y-8">
      {/* Top Banner & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 tracking-tight flex items-center gap-2">
            <span>个人知识工作台</span>
            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
              V1.2 MVP
            </span>
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            先查自己的知识，再向 AI / 公网提问；沉淀为可持续维护的知识资产。
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={fetchDashboardData}
            disabled={loading}
            className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors border border-slate-200"
            title="刷新数据"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <Link
            href="/knowledge/new"
            className="flex items-center gap-1.5 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium shadow-sm transition-all"
          >
            <PlusCircle className="w-4 h-4" />
            <span>新建知识点</span>
          </Link>
        </div>
      </div>

      {/* Central Hero Search */}
      <div className="py-4">
        <HeroSearchBox />
      </div>

      {/* Error Notice */}
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-sm text-rose-700 flex items-center justify-between">
          <span>{error}</span>
          <button
            onClick={fetchDashboardData}
            className="underline font-medium hover:text-rose-900 ml-4 shrink-0"
          >
            重试
          </button>
        </div>
      )}

      {/* 5 Macro Stat Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <StatCard
          title="知识库总量"
          value={stats?.total_knowledge ?? (loading ? '...' : 0)}
          description="有效知识点 (排除回收站)"
          icon={BookOpen}
          colorVariant="blue"
        />
        <StatCard
          title="启用分类"
          value={stats?.total_categories ?? (loading ? '...' : 0)}
          description="支持级联无限层级"
          icon={FolderTree}
          colorVariant="indigo"
        />
        <StatCard
          title="标签总数"
          value={stats?.total_tags ?? (loading ? '...' : 0)}
          description="灵活交叉聚合标签"
          icon={TagIcon}
          colorVariant="purple"
        />
        <StatCard
          title="本月新增"
          value={stats?.monthly_added_count ?? (loading ? '...' : 0)}
          description="持续沉淀知识积累"
          icon={TrendingUp}
          colorVariant="emerald"
        />
        <StatCard
          title="AI 搜索沉淀"
          value={stats?.ai_inflow_count ?? (loading ? '...' : 0)}
          description="由 AI 搜索确认入库"
          icon={Sparkles}
          colorVariant="amber"
        />
      </div>

      {/* Pending Drafts Alert Card */}
      {activities && activities.pending_drafts_count > 0 && (
        <PendingDraftsCard
          drafts={activities.pending_drafts}
          totalCount={activities.pending_drafts_count}
        />
      )}

      {/* Two-Column Activity Dashboard */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Recent Knowledge (2 cols) */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h2 className="text-sm font-bold text-slate-800 flex items-center gap-2">
              <Clock className="w-4 h-4 text-slate-400" />
              <span>最近更新知识</span>
            </h2>
            <Link
              href="/knowledge"
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1 group"
            >
              <span>查看全部</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </Link>
          </div>

          <div className="divide-y divide-slate-100 mt-2">
            {loading && !activities ? (
              <div className="py-8 text-center text-xs text-slate-400">加载中...</div>
            ) : activities?.recent_knowledge.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-400">
                暂无知识点，点击右上角“新建知识点”开启知识沉淀
              </div>
            ) : (
              activities?.recent_knowledge.map((item) => (
                <Link
                  key={item.id}
                  href={`/knowledge/${item.id}`}
                  className="py-3 px-2 flex items-center justify-between hover:bg-slate-50 rounded-lg transition-colors group block"
                >
                  <div className="min-w-0 pr-4">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-slate-800 group-hover:text-blue-600 truncate">
                        {item.title}
                      </span>
                      {item.status === 'draft' ? (
                        <span className="px-1.5 py-0.5 text-[10px] bg-amber-100 text-amber-800 rounded font-medium shrink-0">
                          草稿
                        </span>
                      ) : (
                        <span className="px-1.5 py-0.5 text-[10px] bg-emerald-50 text-emerald-700 rounded font-medium shrink-0">
                          已发布
                        </span>
                      )}
                    </div>
                    {item.summary && (
                      <p className="mt-1 text-xs text-slate-500 line-clamp-1">
                        {item.summary}
                      </p>
                    )}
                  </div>

                  <div className="text-right shrink-0">
                    <span className="text-[11px] text-slate-400 block">
                      {item.category_name || '未分类'}
                    </span>
                    <span className="text-[10px] text-slate-400 block mt-0.5">
                      {new Date(item.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>

        {/* Right Column: Searches & Popular Tags (1 col) */}
        <div className="space-y-6">
          {/* Recent Searches */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h2 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                <History className="w-4 h-4 text-slate-400" />
                <span>近期搜索与提问</span>
              </h2>
            </div>

            <div className="mt-3 space-y-2">
              {activities?.recent_searches.length === 0 ? (
                <div className="py-4 text-center text-xs text-slate-400">
                  暂无搜索历史
                </div>
              ) : (
                activities?.recent_searches.slice(0, 5).map((search) => (
                  <button
                    key={search.id}
                    onClick={() => router.push(`/search?q=${encodeURIComponent(search.query)}`)}
                    className="w-full text-left p-2.5 rounded-lg hover:bg-slate-50 transition-colors flex items-center justify-between group border border-transparent hover:border-slate-200"
                  >
                    <div className="min-w-0 pr-2">
                      <span className="text-xs font-medium text-slate-700 group-hover:text-blue-600 truncate block">
                        {search.query}
                      </span>
                      <span className="text-[10px] text-slate-400">
                        {new Date(search.created_at).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                    </div>
                    {search.saved_knowledge_id && (
                      <span className="shrink-0 text-[10px] bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded font-medium">
                        已沉淀
                      </span>
                    )}
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Popular Tags */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h2 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                <TagIcon className="w-4 h-4 text-slate-400" />
                <span>高频热门标签</span>
              </h2>
              <Link
                href="/taxonomy"
                className="text-xs text-blue-600 hover:text-blue-700 font-semibold"
              >
                管理
              </Link>
            </div>

            <div className="mt-3 flex flex-wrap gap-2">
              {activities?.popular_tags.length === 0 ? (
                <div className="py-4 text-center text-xs text-slate-400 w-full">
                  暂无标签数据
                </div>
              ) : (
                activities?.popular_tags.map((tag) => (
                  <button
                    key={tag.id}
                    onClick={() => router.push(`/search?tag=${encodeURIComponent(tag.id)}`)}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 hover:bg-blue-50 hover:text-blue-700 text-slate-700 transition-colors"
                  >
                    <span>#{tag.name}</span>
                    <span className="text-[10px] bg-white px-1.5 py-0.2 rounded-full text-slate-500 font-mono">
                      {tag.knowledge_count}
                    </span>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
