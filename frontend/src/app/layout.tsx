import type { Metadata } from 'next';
import './globals.css';
import Link from 'next/link';
import {
  LayoutDashboard,
  Search,
  BookOpen,
  FolderTree,
  Trash2,
  Settings,
  Sparkles,
  ExternalLink,
} from 'lucide-react';

export const metadata: Metadata = {
  title: '知识库管理系统 | Knowledge Base',
  description: '先查自己的知识，再向 AI / 公网提问；沉淀为可持续维护的知识资产。',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="flex h-screen overflow-hidden bg-slate-50 text-slate-900 antialiased">
        {/* Left Navigation Sidebar */}
        <aside className="w-64 flex-shrink-0 bg-white border-r border-slate-200 flex flex-col justify-between shadow-sm z-20">
          <div>
            {/* App Brand Header */}
            <div className="h-16 flex items-center px-6 border-b border-slate-100 gap-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <span className="font-bold text-slate-800 text-base leading-tight block">知识库系统</span>
                <span className="text-[11px] text-slate-400 font-medium">Knowledge Hub</span>
              </div>
            </div>

            {/* Navigation Menus */}
            <nav className="p-4 space-y-1.5">
              <Link
                href="/"
                className="flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-100 hover:text-blue-600 transition-colors group"
              >
                <LayoutDashboard className="w-4 h-4 text-slate-400 group-hover:text-blue-600 transition-colors" />
                <span>工作台首页</span>
              </Link>

              <Link
                href="/search"
                className="flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-100 hover:text-blue-600 transition-colors group"
              >
                <Search className="w-4 h-4 text-slate-400 group-hover:text-blue-600 transition-colors" />
                <span>统一搜索中心</span>
              </Link>

              <div className="pt-3 pb-1.5 px-3.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                内容管理
              </div>

              <Link
                href="/knowledge"
                className="flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-100 hover:text-blue-600 transition-colors group"
              >
                <BookOpen className="w-4 h-4 text-slate-400 group-hover:text-blue-600 transition-colors" />
                <span>知识库列表</span>
              </Link>

              <Link
                href="/taxonomy"
                className="flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-100 hover:text-blue-600 transition-colors group"
              >
                <FolderTree className="w-4 h-4 text-slate-400 group-hover:text-blue-600 transition-colors" />
                <span>分类与标签</span>
              </Link>

              <Link
                href="/trash"
                className="flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-100 hover:text-rose-600 transition-colors group"
              >
                <Trash2 className="w-4 h-4 text-slate-400 group-hover:text-rose-600 transition-colors" />
                <span>回收站</span>
              </Link>
            </nav>
          </div>

          {/* Bottom Settings & Status */}
          <div className="p-4 border-t border-slate-100 space-y-2">
            <Link
              href="/settings"
              className="flex items-center justify-between px-3.5 py-2 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors"
            >
              <div className="flex items-center gap-2">
                <Settings className="w-4 h-4 text-slate-400" />
                <span>备份与设置</span>
              </div>
            </Link>

            <div className="px-3.5 py-2 bg-slate-50 rounded-lg text-[11px] text-slate-500 flex items-center justify-between border border-slate-100">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                FastAPI 引擎联通
              </span>
              <a
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noreferrer"
                className="text-blue-500 hover:underline flex items-center gap-0.5"
              >
                API <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto min-w-0 bg-slate-50">
          {children}
        </main>
      </body>
    </html>
  );
}
