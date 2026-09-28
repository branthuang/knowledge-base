'use client';

import React, { useEffect, useState } from 'react';
import {
  Settings,
  Download,
  Upload,
  RefreshCw,
  Database,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Server,
  Layers,
} from 'lucide-react';
import { api } from '@/lib/api';

export default function SettingsPage() {
  // Health state
  const [health, setHealth] = useState<{ status: string; database?: string; redis?: string } | null>(null);
  const [loadingHealth, setLoadingHealth] = useState(false);

  // Restore state
  const [restoreFile, setRestoreFile] = useState<File | null>(null);
  const [restoring, setRestoring] = useState(false);
  const [restoreResult, setRestoreResult] = useState<any | null>(null);
  const [restoreError, setRestoreError] = useState<string | null>(null);

  // Reindex state
  const [reindexing, setReindexing] = useState(false);
  const [reindexResult, setReindexResult] = useState<any | null>(null);
  const [reindexError, setReindexError] = useState<string | null>(null);

  const checkHealth = async () => {
    try {
      setLoadingHealth(true);
      const res = await api.system.health();
      setHealth(res);
    } catch {
      setHealth({ status: 'unreachable' });
    } finally {
      setLoadingHealth(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  const handleExportBackup = () => {
    window.open(api.backup.exportUrl, '_blank');
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setRestoreFile(e.target.files[0]);
      setRestoreResult(null);
      setRestoreError(null);
    }
  };

  const handleRestoreBackup = async () => {
    if (!restoreFile) {
      alert('请先选择要恢复的 ZIP 备份文件');
      return;
    }

    if (
      !confirm(
        '【重要提示】恢复备份将执行原子全量覆盖导入，并重新构建所有向量语义索引。是否继续？'
      )
    ) {
      return;
    }

    try {
      setRestoring(true);
      setRestoreError(null);
      setRestoreResult(null);
      const res = await api.backup.restore(restoreFile);
      setRestoreResult(res);
      setRestoreFile(null);
    } catch (err: any) {
      console.error('Restore failed:', err);
      setRestoreError(err?.message || '恢复备份失败，请检查文件格式或数据包完整性');
    } finally {
      setRestoring(false);
    }
  };

  const handleReindex = async () => {
    try {
      setReindexing(true);
      setReindexError(null);
      setReindexResult(null);
      const res = await api.system.reindex();
      setReindexResult(res);
    } catch (err: any) {
      console.error('Reindex failed:', err);
      setReindexError(err?.message || '重建向量索引失败');
    } finally {
      setReindexing(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-6 py-8 space-y-8">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-bold text-slate-800 tracking-tight flex items-center gap-2">
          <Settings className="w-6 h-6 text-slate-700" />
          <span>系统设置与数据安全</span>
        </h1>
        <p className="mt-0.5 text-xs text-slate-500">
          全量知识库备份归档与导入、向量索引重建维护与后端运行状态诊断
        </p>
      </div>

      {/* 1. System Health Status Card */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <Server className="w-4 h-4 text-blue-600" />
            <h2 className="text-sm font-bold text-slate-800">
              后端服务与数据引擎健康状态
            </h2>
          </div>
          <button
            type="button"
            onClick={checkHealth}
            disabled={loadingHealth}
            className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-800"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingHealth ? 'animate-spin' : ''}`} />
            <span>检测健康</span>
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between">
            <span className="text-slate-600 font-medium">FastAPI 核心服务</span>
            <span className="flex items-center gap-1.5 font-semibold text-emerald-600">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              {health?.status === 'healthy' ? '在线运行' : health?.status || '检测中'}
            </span>
          </div>

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between">
            <span className="text-slate-600 font-medium">PostgreSQL 16 + pgvector</span>
            <span className="flex items-center gap-1.5 font-semibold text-emerald-600">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              {health?.database || '连通正常'}
            </span>
          </div>

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between">
            <span className="text-slate-600 font-medium">Redis 7 高性能缓存</span>
            <span className="flex items-center gap-1.5 font-semibold text-emerald-600">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              {health?.redis || '连通正常'}
            </span>
          </div>
        </div>
      </div>

      {/* 2. Full Standard Backup Export */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-600" />
              <h2 className="text-sm font-bold text-slate-800">
                全量知识库标准归档导出 (ZIP)
              </h2>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed max-w-xl">
              导出包含完整知识点、分类树、标签映射、多源溯源引用数据的 <code>data.json</code>，以及由系统计算并附带 SHA-256 签名校验和的 <code>manifest.json</code>，打包为通用可迁移的 ZIP 文件。
            </p>
          </div>

          <button
            type="button"
            onClick={handleExportBackup}
            className="flex items-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-sm shadow-emerald-500/20 transition-all shrink-0"
          >
            <Download className="w-4 h-4" />
            <span>下载全量备份包</span>
          </button>
        </div>
      </div>

      {/* 3. Atomic Full Backup Restore */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Upload className="w-5 h-5 text-blue-600" />
            <h2 className="text-sm font-bold text-slate-800">
              备份还原与防篡改校验 (Restore)
            </h2>
          </div>
          <p className="text-xs text-slate-500 leading-relaxed">
            上传此前导出的标准 ZIP 归档。后端将严格核验 SHA-256 签名校验和（防文件篡改或网络传输损坏），在独立事务中原子全量导入，并自动全量触发文本分块与 pgvector 语义向量索引重建。
          </p>
        </div>

        {/* Restore Upload Box */}
        <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center gap-3">
            <input
              type="file"
              accept=".zip"
              onChange={handleFileChange}
              className="text-xs text-slate-600 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer"
            />

            <button
              type="button"
              onClick={handleRestoreBackup}
              disabled={!restoreFile || restoring}
              className="flex items-center justify-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-2xs transition-all shrink-0"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${restoring ? 'animate-spin' : ''}`} />
              <span>{restoring ? '正在校验签名并导入...' : '开始原子全量恢复'}</span>
            </button>
          </div>

          {restoreError && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{restoreError}</span>
            </div>
          )}

          {restoreResult && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 flex items-center gap-2 animate-in fade-in">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <div>
                <span className="font-bold">全量恢复完成！</span>
                <span className="ml-1 text-slate-600">
                  成功导入 {restoreResult.restored_knowledge_count || 0} 篇知识点，
                  {restoreResult.restored_categories_count || 0} 个分类，并已自动完成索引重建。
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 4. Vector Semantic Index Reindexing */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Layers className="w-5 h-5 text-indigo-600" />
              <h2 className="text-sm font-bold text-slate-800">
                向量语义索引全量重建 (Reindex)
              </h2>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed max-w-xl">
              重新遍历知识库全部有效知识点，执行文本分块切片并调用 Embedding 模型重新生成 pgvector 向量，确保混合双路检索的高召回率与准确性。
            </p>
          </div>

          <button
            type="button"
            onClick={handleReindex}
            disabled={reindexing}
            className="flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-xl text-xs font-bold shadow-sm shadow-indigo-500/20 transition-all shrink-0"
          >
            <RefreshCw className={`w-4 h-4 ${reindexing ? 'animate-spin' : ''}`} />
            <span>{reindexing ? '正在重建索引...' : '一键全量重建索引'}</span>
          </button>
        </div>

        {reindexError && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700">
            {reindexError}
          </div>
        )}

        {reindexResult && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 flex items-center gap-2 animate-in fade-in">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <div>
              <span className="font-bold">索引重建成功！</span>
              <span className="ml-1 text-slate-600">
                {reindexResult.message || `已生成并写入 ${reindexResult.indexed_chunks || 0} 个分块向量。`}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
