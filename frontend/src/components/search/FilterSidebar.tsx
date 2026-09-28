import React, { useEffect, useState } from 'react';
import { FolderTree, Tag as TagIcon, Star, RotateCcw, ChevronRight, ChevronDown } from 'lucide-react';
import { api } from '@/lib/api';
import { CategoryTreeNode, Tag } from '@/lib/types';

interface FilterSidebarProps {
  selectedCategoryId?: string;
  selectedTagIds: string[];
  favoriteOnly: boolean;
  onCategoryChange: (categoryId?: string) => void;
  onTagToggle: (tagId: string) => void;
  onFavoriteToggle: (favorite: boolean) => void;
  onReset: () => void;
}

export const FilterSidebar: React.FC<FilterSidebarProps> = ({
  selectedCategoryId,
  selectedTagIds,
  favoriteOnly,
  onCategoryChange,
  onTagToggle,
  onFavoriteToggle,
  onReset,
}) => {
  const [categories, setCategories] = useState<CategoryTreeNode[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [expandedCats, setExpandedCats] = useState<Record<string, boolean>>({});

  useEffect(() => {
    // Load categories tree and tags list
    api.categories.tree().then(setCategories).catch(console.error);
    api.tags.list().then(setTags).catch(console.error);
  }, []);

  const toggleExpand = (catId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setExpandedCats((prev) => ({ ...prev, [catId]: !prev[catId] }));
  };

  const renderCategoryTree = (nodes: CategoryTreeNode[], depth = 0) => {
    return (
      <div className="space-y-0.5">
        {nodes.map((node) => {
          const isSelected = selectedCategoryId === node.id;
          const hasChildren = node.children && node.children.length > 0;
          const isExpanded = !!expandedCats[node.id];

          return (
            <div key={node.id}>
              <div
                onClick={() => onCategoryChange(isSelected ? undefined : node.id)}
                className={`flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs cursor-pointer transition-colors ${
                  isSelected
                    ? 'bg-blue-50 text-blue-700 font-semibold'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`}
                style={{ paddingLeft: `${depth * 12 + 10}px` }}
              >
                <div className="flex items-center gap-1.5 min-w-0">
                  {hasChildren ? (
                    <button
                      type="button"
                      onClick={(e) => toggleExpand(node.id, e)}
                      className="p-0.5 hover:bg-slate-200 rounded text-slate-400 hover:text-slate-600"
                    >
                      {isExpanded ? (
                        <ChevronDown className="w-3.5 h-3.5" />
                      ) : (
                        <ChevronRight className="w-3.5 h-3.5" />
                      )}
                    </button>
                  ) : (
                    <span className="w-3.5" />
                  )}
                  <span className="truncate">{node.name}</span>
                </div>
                {node.knowledge_count > 0 && (
                  <span className="text-[10px] text-slate-400 font-mono ml-1">
                    {node.knowledge_count}
                  </span>
                )}
              </div>

              {hasChildren && isExpanded && renderCategoryTree(node.children, depth + 1)}
            </div>
          );
        })}
      </div>
    );
  };

  const hasActiveFilters = !!selectedCategoryId || selectedTagIds.length > 0 || favoriteOnly;

  return (
    <aside className="w-full lg:w-64 bg-white border border-slate-200 rounded-xl p-4 space-y-5 shadow-xs">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
          检索与多维筛选
        </h3>
        {hasActiveFilters && (
          <button
            type="button"
            onClick={onReset}
            className="flex items-center gap-1 text-[11px] text-blue-600 hover:text-blue-800 transition-colors"
          >
            <RotateCcw className="w-3 h-3" />
            <span>重置</span>
          </button>
        )}
      </div>

      {/* Favorite Toggle */}
      <div>
        <label className="flex items-center gap-2 cursor-pointer text-xs font-medium text-slate-700 hover:text-slate-900">
          <input
            type="checkbox"
            checked={favoriteOnly}
            onChange={(e) => onFavoriteToggle(e.target.checked)}
            className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 w-4 h-4 cursor-pointer"
          />
          <Star className={`w-3.5 h-3.5 ${favoriteOnly ? 'text-amber-500 fill-amber-500' : 'text-slate-400'}`} />
          <span>仅检索我的收藏</span>
        </label>
      </div>

      {/* Category Cascade Filter */}
      <div className="space-y-2">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-700">
          <FolderTree className="w-3.5 h-3.5 text-slate-400" />
          <span>分类目录</span>
        </div>

        <div className="max-h-56 overflow-y-auto pr-1">
          <div
            onClick={() => onCategoryChange(undefined)}
            className={`px-2.5 py-1.5 rounded-lg text-xs cursor-pointer transition-colors ${
              !selectedCategoryId
                ? 'bg-blue-50 text-blue-700 font-semibold'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            全部分类
          </div>
          {renderCategoryTree(categories)}
        </div>
      </div>

      {/* Tags Multi-select Filter */}
      <div className="space-y-2">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-700">
          <TagIcon className="w-3.5 h-3.5 text-slate-400" />
          <span>标签筛选 ({selectedTagIds.length})</span>
        </div>

        <div className="flex flex-wrap gap-1.5 max-h-48 overflow-y-auto pr-1">
          {tags.map((tag) => {
            const isSelected = selectedTagIds.includes(tag.id);
            return (
              <button
                key={tag.id}
                type="button"
                onClick={() => onTagToggle(tag.id)}
                className={`text-[11px] px-2.5 py-1 rounded-md transition-colors ${
                  isSelected
                    ? 'bg-blue-600 text-white font-medium shadow-xs'
                    : 'bg-slate-100 hover:bg-slate-200 text-slate-600'
                }`}
              >
                #{tag.name}
              </button>
            );
          })}
        </div>
      </div>
    </aside>
  );
};
