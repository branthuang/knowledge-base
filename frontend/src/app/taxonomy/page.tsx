'use client';

import React, { useEffect, useState } from 'react';
import {
  FolderTree,
  Tag as TagIcon,
  Plus,
  Edit2,
  Trash2,
  GitMerge,
  ChevronRight,
  ChevronDown,
  AlertTriangle,
  FolderPlus,
  RefreshCw,
  X,
  Check,
} from 'lucide-react';
import { api } from '@/lib/api';
import { Category, CategoryTreeNode, Tag } from '@/lib/types';

export default function TaxonomyPage() {
  const [categoriesTree, setCategoriesTree] = useState<CategoryTreeNode[]>([]);
  const [flatCategories, setFlatCategories] = useState<Category[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Category Modal State
  const [categoryModalOpen, setCategoryModalOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [categoryParentId, setCategoryParentId] = useState<string | null>(null);
  const [categoryName, setCategoryName] = useState('');
  const [categoryDesc, setCategoryDesc] = useState('');
  const [categoryColor, setCategoryColor] = useState('');

  // Category Delete Guard Modal
  const [deleteCategoryModalOpen, setDeleteCategoryModalOpen] = useState(false);
  const [categoryToDelete, setCategoryToDelete] = useState<CategoryTreeNode | null>(null);
  const [reassignOption, setReassignOption] = useState<'unclassified' | 'other'>('unclassified');
  const [reassignTargetId, setReassignTargetId] = useState<string>('');

  // Tag Management State
  const [newTagName, setNewTagName] = useState('');
  const [mergeModalOpen, setMergeModalOpen] = useState(false);
  const [sourceTagId, setSourceTagId] = useState('');
  const [targetTagId, setTargetTagId] = useState('');
  const [merging, setMerging] = useState(false);

  // Tag Rename State
  const [renameModalOpen, setRenameModalOpen] = useState(false);
  const [tagToRename, setTagToRename] = useState<Tag | null>(null);
  const [newTagNameInput, setNewTagNameInput] = useState('');
  const [renameError, setRenameError] = useState<string | null>(null);
  const [renaming, setRenaming] = useState(false);

  // Tag Delete State
  const [deleteTagModalOpen, setDeleteTagModalOpen] = useState(false);
  const [tagToDelete, setTagToDelete] = useState<Tag | null>(null);
  const [deletingTag, setDeletingTag] = useState(false);

  // Tree Expansion State
  const [expandedNodes, setExpandedNodes] = useState<Record<string, boolean>>({});

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [tree, flat, tagList] = await Promise.all([
        api.categories.tree(),
        api.categories.list(),
        api.tags.list(),
      ]);
      setCategoriesTree(tree);
      setFlatCategories(flat);
      setTags(tagList);
    } catch (err: any) {
      console.error('Failed to load taxonomy:', err);
      setError(err?.message || '加载分类标签失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const toggleExpand = (nodeId: string) => {
    setExpandedNodes((prev) => ({ ...prev, [nodeId]: !prev[nodeId] }));
  };

  // Open Create/Edit Category Modal
  const handleOpenCategoryModal = (parent_id: string | null = null, existing?: Category) => {
    if (existing) {
      setEditingCategory(existing);
      setCategoryParentId(existing.parent_id || null);
      setCategoryName(existing.name);
      setCategoryDesc(existing.description || '');
      setCategoryColor(existing.color || '');
    } else {
      setEditingCategory(null);
      setCategoryParentId(parent_id);
      setCategoryName('');
      setCategoryDesc('');
      setCategoryColor('');
    }
    setCategoryModalOpen(true);
  };

  const handleSaveCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!categoryName.trim()) return;

    try {
      if (editingCategory) {
        await api.categories.update(editingCategory.id, {
          name: categoryName.trim(),
          description: categoryDesc.trim() || undefined,
          color: categoryColor.trim() || undefined,
        });
      } else {
        await api.categories.create({
          name: categoryName.trim(),
          parent_id: categoryParentId || undefined,
          description: categoryDesc.trim() || undefined,
          color: categoryColor.trim() || undefined,
        });
      }
      setCategoryModalOpen(false);
      loadData();
    } catch (err: any) {
      alert('保存分类失败: ' + err.message);
    }
  };

  // Safe Category Delete
  const handleInitiateDeleteCategory = (node: CategoryTreeNode) => {
    setCategoryToDelete(node);
    setReassignOption('unclassified');
    setReassignTargetId('');
    setDeleteCategoryModalOpen(true);
  };

  const handleConfirmDeleteCategory = async () => {
    if (!categoryToDelete) return;
    try {
      const reassignId =
        reassignOption === 'other' ? reassignTargetId : 'unclassified';
      await api.categories.delete(categoryToDelete.id, reassignId);
      setDeleteCategoryModalOpen(false);
      loadData();
    } catch (err: any) {
      alert('删除分类失败: ' + err.message);
    }
  };

  // Tag Operations
  const handleCreateTag = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = newTagName.trim();
    if (!trimmed) return;
    try {
      await api.tags.create({ name: trimmed });
      setNewTagName('');
      loadData();
    } catch (err: any) {
      alert('创建标签失败: ' + err.message);
    }
  };

  const handleMergeTags = async () => {
    if (!sourceTagId || !targetTagId) {
      alert('请选择源标签和目标标签');
      return;
    }
    if (sourceTagId === targetTagId) {
      alert('源标签与目标标签不能相同');
      return;
    }

    try {
      setMerging(true);
      await api.tags.merge(sourceTagId, targetTagId);
      setMergeModalOpen(false);
      setSourceTagId('');
      setTargetTagId('');
      loadData();
      alert('标签合并成功，所有关联知识已无缝继承到目标标签！');
    } catch (err: any) {
      alert('合并标签失败: ' + err.message);
    } finally {
      setMerging(false);
    }
  };

  const handleOpenRenameModal = (tag: Tag) => {
    setTagToRename(tag);
    setNewTagNameInput(tag.name);
    setRenameError(null);
    setRenameModalOpen(true);
  };

  const handleSaveRename = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tagToRename) return;
    const trimmed = newTagNameInput.trim();
    if (!trimmed) {
      setRenameError('标签名称不能为空');
      return;
    }
    if (trimmed === tagToRename.name) {
      setRenameModalOpen(false);
      return;
    }

    try {
      setRenaming(true);
      setRenameError(null);
      await api.tags.update(tagToRename.id, { name: trimmed });
      setRenameModalOpen(false);
      setTagToRename(null);
      loadData();
    } catch (err: any) {
      setRenameError(err.message || '修改标签名称失败');
    } finally {
      setRenaming(false);
    }
  };

  const handleInitiateDeleteTag = (tag: Tag) => {
    setTagToDelete(tag);
    setDeleteTagModalOpen(true);
  };

  const handleConfirmDeleteTag = async () => {
    if (!tagToDelete) return;
    try {
      setDeletingTag(true);
      await api.tags.delete(tagToDelete.id);
      setDeleteTagModalOpen(false);
      setTagToDelete(null);
      await loadData();
    } catch (err: any) {
      alert('删除标签失败: ' + (err?.message || '未知错误'));
    } finally {
      setDeletingTag(false);
    }
  };

  // Render Recursive Tree
  const renderTree = (nodes: CategoryTreeNode[], depth = 0) => {
    return (
      <div className="space-y-1">
        {nodes.map((node) => {
          const hasChildren = node.children && node.children.length > 0;
          const isExpanded = expandedNodes[node.id] ?? true;

          return (
            <div key={node.id} className="group">
              <div
                className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-50 border border-transparent hover:border-slate-200 transition-all text-xs"
                style={{ paddingLeft: `${depth * 16 + 8}px` }}
              >
                <div className="flex items-center gap-2 min-w-0">
                  {hasChildren ? (
                    <button
                      type="button"
                      onClick={() => toggleExpand(node.id)}
                      className="p-1 hover:bg-slate-200 rounded text-slate-400 hover:text-slate-600"
                    >
                      {isExpanded ? (
                        <ChevronDown className="w-3.5 h-3.5" />
                      ) : (
                        <ChevronRight className="w-3.5 h-3.5" />
                      )}
                    </button>
                  ) : (
                    <span className="w-5" />
                  )}

                  <span className="font-semibold text-slate-800 truncate">
                    {node.name}
                  </span>

                  <span className="text-[10px] bg-slate-100 text-slate-500 font-mono px-1.5 py-0.2 rounded-full">
                    {node.knowledge_count} 篇
                  </span>
                </div>

                {/* Node Action Buttons */}
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    type="button"
                    onClick={() => handleOpenCategoryModal(node.id)}
                    className="p-1 text-slate-400 hover:text-blue-600 hover:bg-slate-100 rounded"
                    title="添加子分类"
                  >
                    <FolderPlus className="w-3.5 h-3.5" />
                  </button>
                  <button
                    type="button"
                    onClick={() => handleOpenCategoryModal(node.parent_id, node)}
                    className="p-1 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded"
                    title="编辑分类"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>
                  <button
                    type="button"
                    onClick={() => handleInitiateDeleteCategory(node)}
                    className="p-1 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded"
                    title="删除分类"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {hasChildren && isExpanded && renderTree(node.children, depth + 1)}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 tracking-tight flex items-center gap-2">
            <FolderTree className="w-6 h-6 text-blue-600" />
            <span>分类与标签体系治理</span>
          </h1>
          <p className="mt-0.5 text-xs text-slate-500">
            维护无限级结构化分类目录，治理交叉标签资产与原子事务合并
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors border border-slate-200 self-start sm:self-auto"
          title="刷新数据"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700">
          {error}
        </div>
      )}

      {/* Two Column Layout: Left Category Tree, Right Tag System */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        {/* Left Column: Categories Management */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <FolderTree className="w-4 h-4 text-blue-600" />
              <h2 className="text-sm font-bold text-slate-800">
                结构化分类树 ({flatCategories.length})
              </h2>
            </div>

            <button
              type="button"
              onClick={() => handleOpenCategoryModal(null)}
              className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-2xs"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>新建顶级分类</span>
            </button>
          </div>

          {loading ? (
            <div className="py-12 text-center text-xs text-slate-400">
              加载分类中...
            </div>
          ) : categoriesTree.length === 0 ? (
            <div className="py-12 text-center text-xs text-slate-400">
              暂无分类，请点击右上角新建顶级分类
            </div>
          ) : (
            <div className="max-h-[560px] overflow-y-auto pr-1">
              {renderTree(categoriesTree)}
            </div>
          )}
        </div>

        {/* Right Column: Tags Management & Merge */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <TagIcon className="w-4 h-4 text-purple-600" />
              <h2 className="text-sm font-bold text-slate-800">
                知识标签资产 ({tags.length})
              </h2>
            </div>

            <button
              type="button"
              onClick={() => setMergeModalOpen(true)}
              className="flex items-center gap-1 px-3 py-1.5 bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200 rounded-lg text-xs font-semibold"
            >
              <GitMerge className="w-3.5 h-3.5" />
              <span>原子合并标签</span>
            </button>
          </div>

          {/* Quick Create Tag Form */}
          <form onSubmit={handleCreateTag} className="flex gap-2">
            <input
              type="text"
              value={newTagName}
              onChange={(e) => setNewTagName(e.target.value)}
              placeholder="输入新标签名称..."
              className="flex-1 px-3 py-1.5 text-xs rounded-lg border border-slate-200 focus:border-purple-500 outline-none"
            />
            <button
              type="submit"
              disabled={!newTagName.trim()}
              className="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shrink-0"
            >
              添加标签
            </button>
          </form>

          {/* Tags Cloud / List */}
          {loading ? (
            <div className="py-12 text-center text-xs text-slate-400">
              加载标签中...
            </div>
          ) : tags.length === 0 ? (
            <div className="py-12 text-center text-xs text-slate-400">
              暂无标签，请输入名称快速创建
            </div>
          ) : (
            <div className="flex flex-wrap gap-2 max-h-[500px] overflow-y-auto p-1">
              {tags.map((tag) => (
                <div
                  key={tag.id}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-50 hover:bg-purple-50/50 border border-slate-200 hover:border-purple-200 rounded-lg text-xs text-slate-700 transition-colors group"
                >
                  <span className="font-medium text-slate-800">#{tag.name}</span>
                  <span className="font-mono text-[10px] text-slate-400 bg-white px-1.5 py-0.2 rounded-full border border-slate-100">
                    {tag.knowledge_count || 0}
                  </span>
                  {/* Hover Actions */}
                  <div className="hidden group-hover:flex items-center gap-0.5 ml-1 pl-1 border-l border-slate-200">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleOpenRenameModal(tag);
                      }}
                      className="p-0.5 text-slate-400 hover:text-purple-600 hover:bg-white rounded transition-colors"
                      title="重命名标签"
                    >
                      <Edit2 className="w-3 h-3" />
                    </button>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleInitiateDeleteTag(tag);
                      }}
                      className="p-0.5 text-slate-400 hover:text-rose-600 hover:bg-white rounded transition-colors"
                      title="删除标签"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Modal 1: Create / Edit Category */}
      {categoryModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-800">
                {editingCategory ? '编辑分类属性' : '新建分类'}
              </h3>
              <button
                type="button"
                onClick={() => setCategoryModalOpen(false)}
                className="p-1 text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSaveCategory} className="space-y-3 text-xs">
              <div>
                <label className="font-bold text-slate-700 block mb-1">
                  分类名称 <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={categoryName}
                  onChange={(e) => setCategoryName(e.target.value)}
                  placeholder="例如: 后端开发, 云原生, 论文笔记"
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 focus:border-blue-500 outline-none"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">
                  分类说明 (可选)
                </label>
                <textarea
                  rows={2}
                  value={categoryDesc}
                  onChange={(e) => setCategoryDesc(e.target.value)}
                  placeholder="分类说明..."
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 focus:border-blue-500 outline-none resize-none"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setCategoryModalOpen(false)}
                  className="px-3.5 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 font-medium"
                >
                  取消
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold"
                >
                  保存
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal 2: Safe Category Delete & Reassignment */}
      {deleteCategoryModalOpen && categoryToDelete && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div className="flex items-center gap-2.5 text-amber-600">
              <AlertTriangle className="w-5 h-5 shrink-0" />
              <h3 className="text-sm font-bold text-slate-800">
                删除分类安全防孤立保护
              </h3>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              确定要删除分类 <span className="font-bold text-slate-900">“{categoryToDelete.name}”</span> 吗？
              {categoryToDelete.knowledge_count > 0 && (
                <span className="block mt-1 text-amber-800 bg-amber-50 p-2 rounded border border-amber-200">
                  当前分类下关联了 <strong>{categoryToDelete.knowledge_count}</strong> 篇知识点。为防止数据孤立，请选择关联知识的归宿：
                </span>
              )}
            </p>

            {categoryToDelete.knowledge_count > 0 && (
              <div className="space-y-2 text-xs">
                <label className="flex items-center gap-2 cursor-pointer text-slate-700">
                  <input
                    type="radio"
                    name="reassign"
                    checked={reassignOption === 'unclassified'}
                    onChange={() => setReassignOption('unclassified')}
                    className="text-blue-600"
                  />
                  <span>将所有知识点设为“未分类 (Unclassified)”</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer text-slate-700">
                  <input
                    type="radio"
                    name="reassign"
                    checked={reassignOption === 'other'}
                    onChange={() => setReassignOption('other')}
                    className="text-blue-600"
                  />
                  <span>转移到其他分类:</span>
                </label>

                {reassignOption === 'other' && (
                  <select
                    value={reassignTargetId}
                    onChange={(e) => setReassignTargetId(e.target.value)}
                    className="w-full px-3 py-1.5 rounded-lg border border-slate-200 text-xs bg-white outline-none mt-1"
                  >
                    <option value="">请选择目标分类...</option>
                    {flatCategories
                      .filter((c) => c.id !== categoryToDelete.id)
                      .map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.name}
                        </option>
                      ))}
                  </select>
                )}
              </div>
            )}

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100 text-xs">
              <button
                type="button"
                onClick={() => setDeleteCategoryModalOpen(false)}
                className="px-3.5 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 font-medium"
              >
                取消
              </button>
              <button
                type="button"
                onClick={handleConfirmDeleteCategory}
                disabled={reassignOption === 'other' && !reassignTargetId}
                className="px-4 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 disabled:opacity-50 text-white font-semibold"
              >
                确认删除
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal 3: Atomic Tag Merge Transaction */}
      {mergeModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <GitMerge className="w-4 h-4 text-purple-600" />
                <h3 className="text-sm font-bold text-slate-800">
                  标签原子事务合并
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setMergeModalOpen(false)}
                className="p-1 text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-500 leading-relaxed">
              将同义或冗余的源标签合并到目标标签。合并后，源标签关联的所有知识将无缝迁移到目标标签，源标签将被安全销毁。
            </p>

            <div className="space-y-3 text-xs">
              <div>
                <label className="font-bold text-slate-700 block mb-1">
                  源标签 (合并后被删除)
                </label>
                <select
                  value={sourceTagId}
                  onChange={(e) => setSourceTagId(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-slate-800 bg-white outline-none"
                >
                  <option value="">请选择源标签...</option>
                  {tags.map((t) => (
                    <option key={t.id} value={t.id}>
                      #{t.name} ({t.knowledge_count || 0} 篇)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">
                  目标标签 (保留并继承全部知识关联)
                </label>
                <select
                  value={targetTagId}
                  onChange={(e) => setTargetTagId(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-slate-800 bg-white outline-none"
                >
                  <option value="">请选择目标标签...</option>
                  {tags
                    .filter((t) => t.id !== sourceTagId)
                    .map((t) => (
                      <option key={t.id} value={t.id}>
                        #{t.name} ({t.knowledge_count || 0} 篇)
                      </option>
                    ))}
                </select>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100 text-xs">
              <button
                type="button"
                onClick={() => setMergeModalOpen(false)}
                disabled={merging}
                className="px-3.5 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 font-medium"
              >
                取消
              </button>
              <button
                type="button"
                onClick={handleMergeTags}
                disabled={merging || !sourceTagId || !targetTagId}
                className="px-4 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-semibold"
              >
                {merging ? '合并中...' : '确认原子合并'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal 4: Lightweight Tag Rename */}
      {renameModalOpen && tagToRename && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <TagIcon className="w-4 h-4 text-purple-600" />
                <h3 className="text-sm font-bold text-slate-800">
                  重命名标签
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setRenameModalOpen(false)}
                className="p-1 text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSaveRename} className="space-y-3 text-xs">
              <div>
                <label className="font-bold text-slate-700 block mb-1">
                  标签名称 <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-2 text-slate-400 font-medium">#</span>
                  <input
                    type="text"
                    required
                    autoFocus
                    value={newTagNameInput}
                    onChange={(e) => {
                      setNewTagNameInput(e.target.value);
                      if (renameError) setRenameError(null);
                    }}
                    placeholder="输入新标签名称..."
                    className="w-full pl-7 pr-3 py-2 rounded-lg border border-slate-200 focus:border-purple-500 outline-none"
                  />
                </div>
                {renameError && (
                  <p className="mt-1.5 text-[11px] text-rose-500 flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3 shrink-0" />
                    <span>{renameError}</span>
                  </p>
                )}
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setRenameModalOpen(false)}
                  disabled={renaming}
                  className="px-3.5 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 font-medium"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={renaming || !newTagNameInput.trim()}
                  className="px-4 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-semibold"
                >
                  {renaming ? '保存中...' : '保存'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal 5: Safe Tag Unlink & Delete Modal */}
      {deleteTagModalOpen && tagToDelete && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div className="flex items-center gap-2.5 text-rose-600">
              <AlertTriangle className="w-5 h-5 shrink-0" />
              <h3 className="text-sm font-bold text-slate-800">
                删除标签确认
              </h3>
            </div>

            <div className="text-xs text-slate-600 leading-relaxed space-y-2">
              <p>
                确定要删除标签 <span className="font-bold text-slate-900">“#{tagToDelete.name}”</span> 吗？
              </p>
              {Boolean(tagToDelete.knowledge_count && tagToDelete.knowledge_count > 0) ? (
                <div className="text-amber-800 bg-amber-50 p-2.5 rounded-lg border border-amber-200 leading-relaxed">
                  当前标签已关联 <strong>{tagToDelete.knowledge_count}</strong> 篇知识点。确认删除后，系统将自动从所有关联知识点中<strong>解绑该标签</strong>，知识点本身保留且不受影响。
                </div>
              ) : (
                <p className="text-slate-400">
                  当前标签未关联任何知识点，删除后将彻底移除。
                </p>
              )}
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100 text-xs">
              <button
                type="button"
                onClick={() => setDeleteTagModalOpen(false)}
                disabled={deletingTag}
                className="px-3.5 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 font-medium"
              >
                取消
              </button>
              <button
                type="button"
                onClick={handleConfirmDeleteTag}
                disabled={deletingTag}
                className="px-4 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 disabled:opacity-50 text-white font-semibold"
              >
                {deletingTag ? '删除中...' : '确认解绑删除'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
