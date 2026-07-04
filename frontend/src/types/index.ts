export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export interface RecommendationItem {
  name: string;
  url: string;
  test_type?: string;
  description?: string;
  duration?: string;
  adaptive?: boolean;
  remote?: boolean;
  languages?: string[];
  job_levels?: string[];
}

export interface ChatResponse {
  reply: string;
  recommendations: RecommendationItem[];
  end_of_conversation: boolean;
}

export interface HiringConstraints {
  role: string | null;
  skills: string[];
  programming_languages: string[];
  job_level: string | null;
  experience: string | null;
  duration: number | null;
  language: string | null;
  adaptive: string | null;
  remote: string | null;
  assessment_keys: string[];
}
