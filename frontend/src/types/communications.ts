export type ThreadType = "internal" | "client" | "agency" | "vendor" | "teaming_partner";
export type ThreadStatus = "active" | "archived" | "resolved";
export type ThreadPriority = "low" | "normal" | "high" | "urgent";

export type MessageType = "text" | "system" | "ai_generated" | "file_share";

export type QuestionStatus = "draft" | "submitted" | "answered" | "withdrawn";
export type QuestionSource = "vendor_submitted" | "government_issued" | "internal";

export interface CommunicationThread {
  id: string;
  subject: string;
  thread_type: ThreadType;
  deal: string | null;
  deal_name?: string;
  status: ThreadStatus;
  priority: ThreadPriority;
  tags: string[];
  participant_count?: number;
  message_count?: number;
  last_message_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  thread: string;
  sender: string;
  sender_name?: string;
  content: string;
  message_type: MessageType;
  attachments: unknown[];
  is_edited: boolean;
  edited_at: string | null;
  parent: string | null;
  created_at: string;
}

export interface ClarificationQuestion {
  id: string;
  deal: string;
  deal_name?: string;
  rfp_section: string;
  question_text: string;
  question_number: number | null;
  submitted_by: string | null;
  submitted_by_name?: string;
  submitted_at: string | null;
  due_date: string | null;
  status: QuestionStatus;
  is_government_question: boolean;
  source: QuestionSource;
  created_at: string;
}
