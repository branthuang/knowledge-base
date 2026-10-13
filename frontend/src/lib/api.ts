/**
 * Knowledge Base Typed API Client
 */

import {
  AISearchResponse,
  Category,
  CategoryTreeNode,
  InflowConfirmInput,
  InflowPreviewResponse,
  KnowledgeCreateInput,
  KnowledgeDetail,
  KnowledgeUpdateInput,
  PaginatedKnowledgeResponse,
  SearchMode,
  SearchResponse,
  Tag,
  WorkbenchActivitiesResponse,
  WorkbenchStatsResponse,
} from './types';

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ??
  (typeof window !== 'undefined' ? '' : (process.env.BACKEND_INTERNAL_URL || 'http://127.0.0.1:8000'));

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = `HTTP Error ${response.status} ${response.statusText}`;
    try {
      const errText = await response.text();
      if (errText) {
        try {
          const errJson = JSON.parse(errText);
          if (errJson && errJson.detail) {
            errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
          }
        } catch {
          errorDetail = errText;
        }
      }
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  if (response.status === 204) {
    return {} as T;
  }

  const text = await response.text();
  if (!text || text.trim() === '') {
    return {} as T;
  }

  try {
    return JSON.parse(text) as T;
  } catch {
    return text as unknown as T;
  }
}

export const api = {
  // Workbench API
  workbench: {
    getStats: () => request<WorkbenchStatsResponse>('/api/workbench/stats'),
    getActivities: () => request<WorkbenchActivitiesResponse>('/api/workbench/activities'),
  },

  // Hybrid Search API
  search: {
    searchKnowledge: (params: {
      query: string;
      category_id?: string;
      tag_ids?: string[];
      source_type?: string;
      favorite?: boolean;
      start_date?: string;
      end_date?: string;
      page?: number;
      page_size?: number;
      minimum_score?: number;
    }) =>
      request<SearchResponse>('/api/search', {
        method: 'POST',
        body: JSON.stringify(params),
      }),
  },

  // AI Search & Inflow
  aiSearch: {
    ask: (params: {
      query: string;
      mode?: SearchMode;
      session_id?: string;
      category_id?: string;
      tag_ids?: string[];
      minimum_score?: number;
    }) =>
      request<AISearchResponse>('/api/ai-search', {
        method: 'POST',
        body: JSON.stringify(params),
      }),
    getSessions: (limit: number = 20) =>
      request<any[]>(`/api/ai-search/sessions?limit=${limit}`),
    getSession: (id: string) =>
      request<any>(`/api/ai-search/sessions/${id}`),
  },

  // Knowledge Inflow
  inflow: {
    preview: (payload: {
      session_id?: string;
      query?: string;
      content_markdown?: string;
      citations?: any[];
    }) =>
      request<InflowPreviewResponse>('/api/inflow/preview', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    confirm: (payload: InflowConfirmInput) =>
      request<KnowledgeDetail>('/api/inflow/confirm', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
  },

  // Categories API
  categories: {
    list: () => request<Category[]>('/api/categories'),
    tree: () => request<CategoryTreeNode[]>('/api/categories/tree'),
    create: (data: Partial<Category>) =>
      request<Category>('/api/categories', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    update: (id: string, data: Partial<Category>) =>
      request<Category>(`/api/categories/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    delete: (id: string, reassign_to_id?: string) =>
      request<{ status: string; id: string }>(`/api/categories/${id}`, {
        method: 'DELETE',
        body: JSON.stringify({ reassign_to_id }),
      }),
  },

  // Tags API
  tags: {
    list: () => request<Tag[]>('/api/tags'),
    create: (data: Partial<Tag>) =>
      request<Tag>('/api/tags', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    update: (id: string, data: Partial<Tag>) =>
      request<Tag>(`/api/tags/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    delete: (id: string) =>
      request<void>(`/api/tags/${id}`, {
        method: 'DELETE',
      }),
    merge: (source_tag_id: string, target_tag_id: string) =>
      request<{ status: string; message: string }>('/api/tags/merge', {
        method: 'POST',
        body: JSON.stringify({ source_tag_id, target_tag_id }),
      }),
  },

  // Knowledge CRUD API
  knowledge: {
    list: (params: {
      category_id?: string;
      tag_ids?: string[];
      status?: string;
      favorite?: boolean;
      source_type?: string;
      keyword?: string;
      page?: number;
      page_size?: number;
    } = {}) => {
      const query = new URLSearchParams();
      if (params.category_id) query.set('category_id', params.category_id);
      if (params.tag_ids?.length) {
        params.tag_ids.forEach((tid) => query.append('tag_ids', tid));
      }
      if (params.status) query.set('status', params.status);
      if (params.favorite !== undefined) query.set('favorite', String(params.favorite));
      if (params.source_type) query.set('source_type', params.source_type);
      if (params.keyword) query.set('keyword', params.keyword);
      if (params.page) query.set('page', String(params.page));
      if (params.page_size) query.set('page_size', String(params.page_size));

      const qs = query.toString();
      return request<PaginatedKnowledgeResponse>(`/api/knowledge${qs ? `?${qs}` : ''}`);
    },
    get: (id: string) => request<KnowledgeDetail>(`/api/knowledge/${id}`),
    create: (data: KnowledgeCreateInput) =>
      request<KnowledgeDetail>('/api/knowledge', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    update: (id: string, data: KnowledgeUpdateInput) =>
      request<KnowledgeDetail>(`/api/knowledge/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    delete: (id: string) =>
      request<{ status: string; id: string }>(`/api/knowledge/${id}`, {
        method: 'DELETE',
      }),
    listTrash: (page = 1, page_size = 20) =>
      request<PaginatedKnowledgeResponse>(`/api/knowledge/trash/list?page=${page}&page_size=${page_size}`),
    restoreTrash: (id: string) =>
      request<{ message: string }>(`/api/knowledge/${id}/restore`, {
        method: 'POST',
      }),
    permanentDelete: (id: string) =>
      request<void>(`/api/knowledge/${id}/permanent`, {
        method: 'DELETE',
      }),
  },

  // Backup & Restore & System
  backup: {
    exportUrl: `${API_BASE}/api/backup/export`,
    exportMarkdownUrl: (id: string) => `${API_BASE}/api/backup/export/markdown/${id}`,
    restore: async (fileBlob: Blob) => {
      const response = await fetch(`${API_BASE}/api/backup/restore`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/zip',
        },
        body: fileBlob,
      });
      if (!response.ok) {
        let err = response.statusText;
        try {
          const j = await response.json();
          if (j.detail) err = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail);
        } catch {}
        throw new Error(err);
      }
      return response.json();
    },
  },

  // System Maintenance
  system: {
    health: () => request<{ status: string; database?: string; redis?: string }>('/api/health'),
    reindex: () => request<{ status: string; message: string; indexed_chunks?: number }>('/api/search/reindex', {
      method: 'POST',
    }),
  },
};
