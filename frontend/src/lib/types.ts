/**
 * Knowledge Base Frontend Type Definitions
 * Aligned with FastAPI Backend Schemas
 */

// ========================
// Block & Rich Text Types
// ========================

export type BlockType =
  | 'paragraph'
  | 'heading'
  | 'list'
  | 'todo'
  | 'quote'
  | 'callout'
  | 'code'
  | 'table'
  | 'image'
  | 'attachment'
  | 'divider';

export interface BlockProperties {
  level?: number;
  list_style?: 'bullet' | 'ordered' | string;
  checked?: boolean;
  callout_tone?: 'info' | 'warning' | 'error' | 'success' | string;
  language?: string;
  caption?: string;
  width?: number;
  file_name?: string;
  file_size?: number;
  mime_type?: string;
  extra?: Record<string, unknown>;
}

export interface BlockItem {
  id: string;
  type: BlockType;
  content: string | unknown[] | Record<string, unknown>;
  properties: BlockProperties;
  children?: BlockItem[];
}

// ========================
// Category & Tag Types
// ========================

export interface Category {
  id: string;
  name: string;
  parent_id?: string | null;
  description?: string | null;
  icon?: string | null;
  color?: string | null;
  sort_order: number;
  status: 'active' | 'inactive';
  created_at: string;
  updated_at: string;
  knowledge_count: number;
}

export interface CategoryTreeNode extends Category {
  children: CategoryTreeNode[];
}

export interface Tag {
  id: string;
  name: string;
  parent_id?: string | null;
  description?: string | null;
  color?: string | null;
  created_at: string;
  updated_at: string;
  knowledge_count?: number;
  last_used_at?: string | null;
}

// ========================
// Knowledge Item Types
// ========================

export interface SourceInfo {
  id?: string;
  type: 'manual' | 'ai_search' | 'url' | 'file';
  url?: string | null;
  title?: string | null;
  metadata_json?: Record<string, unknown>;
  created_at?: string;
}

export interface KnowledgeListItem {
  id: string;
  title: string;
  summary?: string | null;
  category_id?: string | null;
  category_name?: string | null;
  tags: Tag[];
  source_type: 'manual' | 'ai_search' | 'import' | 'web_clip';
  status: 'draft' | 'published' | 'archived';
  favorite: boolean;
  index_status: 'indexed' | 'pending' | 'failed';
  created_at: string;
  updated_at: string;
}

export interface KnowledgeDetail extends KnowledgeListItem {
  blocks_json: BlockItem[];
  plain_text: string;
  sources: SourceInfo[];
}

export interface KnowledgeCreateInput {
  title: string;
  summary?: string;
  blocks_json?: BlockItem[];
  category_id?: string;
  tag_ids?: string[];
  source_type?: string;
  status?: 'draft' | 'published' | 'archived';
  favorite?: boolean;
  sources?: SourceInfo[];
}

export interface KnowledgeUpdateInput {
  title?: string;
  summary?: string;
  blocks_json?: BlockItem[];
  category_id?: string;
  tag_ids?: string[];
  status?: string;
  favorite?: boolean;
  sources?: SourceInfo[];
}

export interface PaginatedKnowledgeResponse {
  items: KnowledgeListItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// ========================
// Hybrid Search Types
// ========================

export interface SearchHitItem {
  id: string;
  title: string;
  summary?: string | null;
  category_id?: string | null;
  category_name?: string | null;
  tags: Tag[];
  source_type: string;
  favorite: boolean;
  score: number;
  keyword_score: number;
  vector_score: number;
  best_snippet: string;
  matched_block_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface SearchResponse {
  query: string;
  total: number;
  page: number;
  page_size: number;
  is_sufficient: boolean;
  ai_search_suggested: boolean;
  ai_search_prompt?: string | null;
  items: SearchHitItem[];
}

// ========================
// AI Search & Inflow Types
// ========================

export type SearchMode =
  | 'knowledge_first'
  | 'external_supplement'
  | 'knowledge_only'
  | 'direct_ai';

export interface CitationItem {
  title: string;
  url: string;
  snippet: string;
  source_name?: string | null;
  published_at?: string | null;
}

export interface LocalHitRef {
  id: string;
  title: string;
  snippet: string;
  score: number;
  category_name?: string | null;
}

export interface AISearchResponse {
  session_id: string;
  query: string;
  mode: SearchMode;
  ai_answer: string;
  is_sufficient: boolean;
  local_hits: LocalHitRef[];
  citations: CitationItem[];
  model_used: string;
  created_at: string;
}

export interface SimilarKnowledgeCandidate {
  id: string;
  title: string;
  snippet: string;
  similarity_score: number;
  category_name?: string | null;
  updated_at: string;
}

export interface InflowPreviewResponse {
  session_id?: string | null;
  recommended_title: string;
  recommended_summary: string;
  blocks: BlockItem[];
  recommended_category_id?: string | null;
  recommended_category_name?: string | null;
  recommended_tag_ids: string[];
  recommended_tag_names: string[];
  sources: SourceInfo[];
  has_similar_knowledge: boolean;
  similar_candidates: SimilarKnowledgeCandidate[];
}

export interface InflowConfirmInput {
  session_id?: string | null;
  action: 'create_new' | 'update_existing';
  target_knowledge_id?: string | null;
  title: string;
  summary?: string | null;
  blocks: BlockItem[];
  category_id?: string | null;
  tag_ids?: string[];
  sources?: SourceInfo[];
  status?: string;
}

// ========================
// Workbench Dashboard Types
// ========================

export interface WorkbenchStatsResponse {
  total_knowledge: number;
  total_categories: number;
  total_tags: number;
  monthly_added_count: number;
  ai_inflow_count: number;
}

export interface RecentKnowledgeItem {
  id: string;
  title: string;
  summary?: string | null;
  category_id?: string | null;
  category_name?: string | null;
  status: string;
  updated_at: string;
}

export interface PendingReviewDraftItem {
  id: string;
  title: string;
  summary?: string | null;
  category_name?: string | null;
  source_type: string;
  created_at: string;
}

export interface RecentSearchSessionItem {
  id: string;
  query: string;
  mode: string;
  saved_knowledge_id?: string | null;
  created_at: string;
}

export interface PopularTagItem {
  id: string;
  name: string;
  color?: string | null;
  knowledge_count: number;
}

export interface WorkbenchActivitiesResponse {
  recent_knowledge: RecentKnowledgeItem[];
  pending_drafts: PendingReviewDraftItem[];
  pending_drafts_count: number;
  recent_searches: RecentSearchSessionItem[];
  popular_tags: PopularTagItem[];
}
