
import { MinionConfig, ChatMessageData, MessageSender, Channel, ModelOption } from '../types';
import { 
    LEGION_COMMANDER_NAME, 
    MINION_CONFIGS_STORAGE_KEY, 
    CHAT_HISTORY_STORAGE_KEY,
    EMOTIONAL_ENGINE_SYSTEM_PROMPT_TEMPLATE,
    META_PROMPT_TASK_INSTRUCTIONS_TEMPLATE,
    formatChatHistoryForLLM,
    GEMINI_MODELS_OPTIONS
} from '../constants';
import { callGeminiAPIStream, extractDiaryAndContent } from './geminiService'; // To simulate Minion responses

// Helper to get data from localStorage or return default
const getStoredData = <T>(key: string, defaultValue: T): T => {
  const saved = localStorage.getItem(key);
  try {
    return saved ? JSON.parse(saved) : defaultValue;
  } catch (error) {
    console.error(`Error parsing stored data for key ${key}:`, error);
    return defaultValue;
  }
};

// Helper to set data to localStorage
const setStoredData = <T>(key: string, data: T): void => {
  localStorage.setItem(key, JSON.stringify(data));
};


export interface HandleUserMessageParams {
  channelId: string;
  message: ChatMessageData;
  allMinions: MinionConfig[];
  currentMessages: ChatMessageData[]; // Messages in the current channel for context
  onMinionResponse: (message: ChatMessageData) => void; // Callback for full response
  onMinionResponseChunk?: (minionId: string, tempMessageId: string, chunk: string, isFinal: boolean) => void; // For streaming
  onMinionProcessingUpdate?: (minionId: string, isProcessing: boolean) => void;
  onSystemMessage?: (message: ChatMessageData) => void; // For system messages like [SILENT]
}

class LegionApiService {
  private minionConfigs: MinionConfig[];
  private channels: Channel[];
  private messages: Record<string, ChatMessageData[]>; // channelId -> messages[]

  constructor() {
    this.minionConfigs = getStoredData<MinionConfig[]>(MINION_CONFIGS_STORAGE_KEY, []);
    this.channels = getStoredData<Channel[]>('gemini_legion_channels_v1', [
        { id: 'general', name: '#general', description: 'General discussion with all Minions.', type: 'user_minion_group', members: [LEGION_COMMANDER_NAME] },
        { id: 'random', name: '#random_bullshit', description: 'Off-topic banter and delightful chaos.', type: 'user_minion_group', members: [LEGION_COMMANDER_NAME] },
        { id: 'legion_ops_log', name: '#legion_ops_log', description: 'Automated Legion operational logs.', type: 'system_log', members: [] },
    ]);
    this.messages = getStoredData<Record<string, ChatMessageData[]>>(CHAT_HISTORY_STORAGE_KEY, {
        'general': [],
        'random': [],
        'legion_ops_log': [
            { id: `sys-init-${Date.now()}`, channelId: 'legion_ops_log', senderType: MessageSender.System, senderName: 'LegionOS', content: 'Legion Command Interface Initialized.', timestamp: Date.now() }
        ]
    });
  }

  // --- Minion Management ---
  async getMinions(): Promise<MinionConfig[]> {
    return Promise.resolve([...this.minionConfigs]);
  }

  async addMinion(config: MinionConfig): Promise<MinionConfig> {
    const newMinion: MinionConfig = { 
        ...config, 
        id: config.id || `minion-${Date.now()}`,
        opinionScores: { [LEGION_COMMANDER_NAME]: 50, ...config.opinionScores }, // Ensure commander is scored
        status: config.status || 'Idle'
    };
    this.minionConfigs.push(newMinion);
    // Add this Minion to members of default channels if applicable
    this.channels = this.channels.map(ch => {
        if (ch.type === 'user_minion_group') {
            return {...ch, members: Array.from(new Set([...(ch.members || []), newMinion.name]))};
        }
        return ch;
    });
    setStoredData(MINION_CONFIGS_STORAGE_KEY, this.minionConfigs);
    setStoredData('gemini_legion_channels_v1', this.channels);
    return Promise.resolve(newMinion);
  }

  async updateMinion(updatedConfig: MinionConfig): Promise<MinionConfig> {
    const index = this.minionConfigs.findIndex(m => m.id === updatedConfig.id);
    if (index === -1) throw new Error("Minion not found for update.");
    this.minionConfigs[index] = updatedConfig;
    setStoredData(MINION_CONFIGS_STORAGE_KEY, this.minionConfigs);
    return Promise.resolve(updatedConfig);
  }

  async deleteMinion(id: string): Promise<void> {
    this.minionConfigs = this.minionConfigs.filter(m => m.id !== id);
    setStoredData(MINION_CONFIGS_STORAGE_KEY, this.minionConfigs);
    return Promise.resolve();
  }

  async getMinionModels(): Promise<ModelOption[]> {
    // In a real app, this would fetch from the Legion backend, which might get them from Google or a config.
    return Promise.resolve(GEMINI_MODELS_OPTIONS);
  }

  // --- Channel Management ---
  async getChannels(): Promise<Channel[]> {
    return Promise.resolve([...this.channels]);
  }

  async addChannel(channelData: Omit<Channel, 'id'> & { id?: string }): Promise<Channel> {
    const newChannel: Channel = { 
        ...channelData, 
        id: channelData.id || `channel-${Date.now()}`,
        members: Array.from(new Set([...(channelData.members || []), LEGION_COMMANDER_NAME])), // Commander always a member
    };
    this.channels.push(newChannel);
    if (!this.messages[newChannel.id]) {
        this.messages[newChannel.id] = [];
    }
    setStoredData('gemini_legion_channels_v1', this.channels);
    setStoredData(CHAT_HISTORY_STORAGE_KEY, this.messages);
    return Promise.resolve(newChannel);
  }

  // --- Message Management ---
  async getMessages(channelId: string): Promise<ChatMessageData[]> {
    return Promise.resolve([...(this.messages[channelId] || [])]);
  }
  
  // This method simulates how the backend would orchestrate Minion responses
  async handleUserMessage(params: HandleUserMessageParams): Promise<void> {
    const { 
        channelId, message: userMessage, allMinions, currentMessages, 
        onMinionResponse, onMinionResponseChunk, onMinionProcessingUpdate, onSystemMessage 
    } = params;

    // Add user message to local store (actual backend would persist this)
    this.messages[channelId] = [...(this.messages[channelId] || []), userMessage];
    setStoredData(CHAT_HISTORY_STORAGE_KEY, this.messages);
    
    const activeChannel = this.channels.find(c => c.id === channelId);
    if (!activeChannel) {
        console.error(`Channel ${channelId} not found for message handling.`);
        return;
    }

    // Determine which minions should respond based on channel members or if it's a general channel
    // This is a simplified logic; backend would have more complex routing.
    const minionsInChannel = allMinions.filter(minion => 
        activeChannel.type === 'user_minion_group' || (activeChannel.members || []).includes(minion.name)
    );


    const chatHistoryForPrompt = formatChatHistoryForLLM([...currentMessages, userMessage], channelId);

    for (const minion of minionsInChannel) {
      if (onMinionProcessingUpdate) onMinionProcessingUpdate(minion.id, true);

      const tempMessageId = `ai-${minion.id}-${Date.now()}`;
      let accumulatedContent = "";
      
      // Create a placeholder streaming message
      const tempStreamingMessage: ChatMessageData = {
        id: tempMessageId, channelId, senderType: MessageSender.AI,
        senderName: minion.name, content: "", timestamp: Date.now(),
      };
      if (onMinionResponseChunk) { // Immediately add placeholder so UI can update it
          onMinionResponse(tempStreamingMessage);
      }


      // Simulate fetching last diary (in a real backend, this comes from DB)
      let lastDiary: string | null = null;
      const minionMessagesInChannel = (this.messages[channelId] || []).filter(m => m.senderName === minion.name && m.internalDiary);
      if (minionMessagesInChannel.length > 0) {
        lastDiary = minionMessagesInChannel[minionMessagesInChannel.length - 1].internalDiary ?? null;

      }
      
      const systemPromptForMinion = EMOTIONAL_ENGINE_SYSTEM_PROMPT_TEMPLATE(minion.name, minion.system_prompt_persona, lastDiary);
      const lastSenderName = userMessage.senderName; // User is always the last sender for this trigger
      const currentOpinionOfLastSender = minion.opinionScores[lastSenderName] ?? 50;
      const fullPrompt = META_PROMPT_TASK_INSTRUCTIONS_TEMPLATE(minion.name, currentOpinionOfLastSender, lastSenderName, chatHistoryForPrompt, activeChannel.name);

      await callGeminiAPIStream(
        fullPrompt, minion.model_id, minion.params.temperature,
        (chunk, isFinal) => { // onStreamChunk from geminiService
          if (!isFinal) {
            accumulatedContent += chunk;
            if(onMinionResponseChunk) onMinionResponseChunk(minion.id, tempMessageId, chunk, false);
          } else { // Stream ended from geminiService
            if (accumulatedContent.trim() === '[SILENT]') {
                if (onMinionResponseChunk) { // Signal to remove placeholder
                     // Update message to be empty but final, then it can be filtered out by App.tsx if needed
                    onMinionResponseChunk(minion.id, tempMessageId, '[SILENT_MARKER]', true);
                }
                if (onSystemMessage) {
                    onSystemMessage({
                        id: `sys-silent-${minion.id}-${Date.now()}`, channelId, senderType: MessageSender.System,
                        senderName: 'System', content: `${minion.name} chose to remain silent.`, timestamp: Date.now(),
                    });
                }
            } else {
              const { messageContent, diary } = extractDiaryAndContent(accumulatedContent);
              const finalMessage: ChatMessageData = {
                id: tempMessageId, // Use the same ID as the temp message
                channelId, senderType: MessageSender.AI, senderName: minion.name,
                content: messageContent, timestamp: Date.now(), internalDiary: diary,
              };
              onMinionResponse(finalMessage); // Send the complete message

              // Update Minion's opinion scores (mock backend update)
              if (diary) {
                const opinionRegex = /- (\w+): (\d+)\/100/g;
                let match;
                const newOpinionScores = { ...minion.opinionScores };
                const diaryLines = diary.split('\n');
                const updatedScoresSectionIndex = diaryLines.findIndex(line => line.startsWith("Updated Opinion Scores:"));
                if (updatedScoresSectionIndex !== -1) {
                    for (let i = updatedScoresSectionIndex + 1; i < diaryLines.length; i++) {
                        const line = diaryLines[i].trim();
                        if (line.startsWith("- ")) {
                            opinionRegex.lastIndex = 0; 
                            match = opinionRegex.exec(line);
                            if (match && match[1] && match[2]) newOpinionScores[match[1]] = parseInt(match[2], 10);
                        } else if (line.includes(':') && !line.includes('Reason:') && !line.startsWith("Personal Notes:")) break;
                        else if (line.startsWith("Personal Notes:") || line.startsWith("Selected Response Mode for this turn")) break; 
                    }
                }
                const minionIdx = this.minionConfigs.findIndex(m => m.id === minion.id);
                if (minionIdx !== -1) this.minionConfigs[minionIdx].opinionScores = newOpinionScores;
                setStoredData(MINION_CONFIGS_STORAGE_KEY, this.minionConfigs);
              }
            }
            if (onMinionProcessingUpdate) onMinionProcessingUpdate(minion.id, false);
          }
        },
        (errorMessage) => { // onError from geminiService
          const errorResponseMessage: ChatMessageData = {
            id: tempMessageId, channelId, senderType: MessageSender.AI, senderName: minion.name,
            content: `Error: ${errorMessage}`, timestamp: Date.now(), isError: true,
          };
          onMinionResponse(errorResponseMessage);
          if (onMinionProcessingUpdate) onMinionProcessingUpdate(minion.id, false);
        },
        systemPromptForMinion
      );
    }
    // Save all messages after all Minions attempted to respond
    setStoredData(CHAT_HISTORY_STORAGE_KEY, this.messages);
    return Promise.resolve();
  }

  async deleteMessage(channelId: string, messageId: string): Promise<void> {
    this.messages[channelId] = (this.messages[channelId] || []).filter(m => m.id !== messageId);
    setStoredData(CHAT_HISTORY_STORAGE_KEY, this.messages);
    return Promise.resolve();
  }

  async editMessage(channelId: string, messageId: string, newContent: string): Promise<void> {
    this.messages[channelId] = (this.messages[channelId] || []).map(m => 
        m.id === messageId ? { ...m, content: newContent } : m
    );
    setStoredData(CHAT_HISTORY_STORAGE_KEY, this.messages);
    return Promise.resolve();
  }
}

const legionApiService = new LegionApiService();
export default legionApiService;
