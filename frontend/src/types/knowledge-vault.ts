export type DocumentCategory =
  | "template"
  | "guide"
  | "best_practice"
  | "case_study"
  | "regulatory_reference"
  | "tool"
  | "lesson_learned"
  | "other";

export type DocumentStatus = "draft" | "review" | "approved" | "archived";

export interface KnowledgeDocument {
  id: string;
  title: string;
  description: string;
  category: DocumentCategory;
  content: string;
  file_url: string;
  file_name: string;
  status: DocumentStatus;
  tags: string[];
  keywords: string[];
  author: string | null;
  author_name?: string;
  reviewer: string | null;
  reviewed_at: string | null;
  version: string;
  is_public: boolean;
  downloads: number;
  views: number;
  created_at: string;
  updated_at: string;
}
