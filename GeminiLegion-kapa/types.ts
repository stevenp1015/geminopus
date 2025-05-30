
export interface MinionConfig {
  id: string;
  name: string; // Unique Minion name (e.g., "Alpha", "Bravo")
  provider: 'google'; // Assuming Gemini models via ADK backend
  model_id: string; // Specific model for this Minion
  system_prompt_persona: string; // The Minion's core personality and Fire Code
  params: {
    temperature: number;
    // Potentially other ADK-specific params in future
  };
  opinionScores: Record<string, number>; // Minion's opinion of others { participantName: score }
  // Add other Legion-specific fields as needed, e.g., assigned tools, status
  status?: string; // e.g., "Idle", "Processing Task X"
  currentTask?: string;
}

export enum MessageSender {
  User = 'User',
  AI = 'AI', // Represents a Minion
  System = 'System',
}

export interface ChatMessageData {
  id:string;
  channelId: string; // ID of the channel this message belongs to
  senderType: MessageSender;
  senderName: string; // "Steven" for user, Minion's name for AI
  content: string;
  timestamp: number;
  internalDiary?: string | null; // For Minion messages
  isError?: boolean;
  replyToMessageId?: string; // For threaded replies (future)
}

export interface ModelOption {
  id: string;
  name: string;
}

export interface Channel {
  id: string;
  name: string; // e.g., "#general", "#commander_direct_alpha"
  description?: string;
  type: 'user_minion_group' | 'user_minion_dm' | 'minion_minion_group' | 'system_log';
  members?: string[]; // IDs of Minions/User in this channel
  isPrivate?: boolean;
}

// Environment variable access (still relevant for UI's own potential key)
export interface ProcessEnv {
  API_KEY?: string;
}
