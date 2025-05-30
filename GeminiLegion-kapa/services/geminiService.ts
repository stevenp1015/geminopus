
import { GoogleGenAI, GenerateContentResponse, Part, GenerateContentParameters, Content } from "@google/genai";
import { UI_API_KEY } from '../constants'; // Using UI_API_KEY for direct UI calls if any

export interface GeminiResponse {
  text: string;
  error?: string;
}

const diaryRegex = /~\*~(.*?)~\*~/s;
export const extractDiaryAndContent = (responseText: string): { messageContent: string; diary: string | null } => {
  const match = responseText.match(diaryRegex);
  if (match && match[1]) {
    const diary = match[1].trim();
    const messageContent = responseText.substring(0, match.index).trim() + responseText.substring(match.index! + match[0].length).trim();
    return { messageContent: messageContent.trim(), diary };
  }
  return { messageContent: responseText.trim(), diary: null };
};

// Helper to convert mixed array of strings and Parts into an array of Parts
const convertToParts = (items: (string | Part)[]): Part[] => {
    return items.map(item => (typeof item === 'string' ? { text: item } : item));
};

// Fix: Changed return type to Content and adjusted logic
const prepareContentParam = (promptContent: string | Part | (string | Part)[]): Content => {
    if (typeof promptContent === 'string') {
        // Fix: Wrap string promptContent in {parts: [{text: promptContent}]} to ensure it's treated as Content by TypeScript, resolving "Type 'string' has no properties in common with type 'Content'" error for line 28.
        return { parts: [{ text: promptContent }] };
    }
    if (Array.isArray(promptContent)) { // This is (string | Part)[]
        const partsArray: Part[] = convertToParts(promptContent);
        return { parts: partsArray }; // {parts: Part[]} is Content
    }
    // This is Part
    // Fix: Wrap Part promptContent in {parts: [promptContent]} to ensure it's treated as Content by TypeScript, resolving "Type 'Part' has no properties in common with type 'Content'" error for line 35.
    return { parts: [promptContent] };
};

export const callGeminiAPI = async (
  promptContent: string | Part | (string | Part)[],
  model: string,
  temperature: number,
  systemInstruction?: string,
): Promise<GeminiResponse> => {
  if (!UI_API_KEY) {
    console.error("Gemini API Key for UI operations is not configured.");
    return { text: "", error: "UI API Key not configured." };
  }

  try {
    // Fix: Ensure apiKey is passed in an object
    const ai = new GoogleGenAI({ apiKey: UI_API_KEY });
    
    const geminiApiConfig: GenerateContentParameters['config'] = {
      temperature: temperature,
    };

    if (systemInstruction) {
       geminiApiConfig.systemInstruction = systemInstruction;
    }
    
    const processedContents = prepareContentParam(promptContent);

    const requestPayload: GenerateContentParameters = {
      model: model,
      contents: processedContents,
      config: geminiApiConfig,
    };
    
    const response: GenerateContentResponse = await ai.models.generateContent(requestPayload);
    
    // Fix: Directly use response.text as per guidelines
    const text = response.text;
    return { text };

  } catch (error: any) {
    console.error("Error calling Gemini API (direct):", error);
    let errorMessage = "An unknown error occurred with the Gemini API.";
    if (error.message) {
      errorMessage = error.message;
    } else if (typeof error === 'string') {
      errorMessage = error;
    }
    return { text: "", error: `Gemini API Error: ${errorMessage}` };
  }
};

export const callGeminiAPIStream = async (
  promptContent: string | Part | (string | Part)[],
  model: string,
  temperature: number,
  onStreamChunk: (chunkText: string, isFinal: boolean) => void,
  onError: (errorMessage: string) => void,
  systemInstruction?: string
): Promise<void> => {
  if (!UI_API_KEY) {
    const errorMsg = "UI API Key not configured for streaming.";
    console.error(errorMsg);
    onError(errorMsg);
    return;
  }

  try {
    // Fix: Ensure apiKey is passed in an object
    const ai = new GoogleGenAI({ apiKey: UI_API_KEY });

    const geminiApiConfig: GenerateContentParameters['config'] = {
      temperature: temperature,
    };

    if (systemInstruction) {
       geminiApiConfig.systemInstruction = systemInstruction;
    }
    
    const processedContents = prepareContentParam(promptContent);

    const requestPayload: GenerateContentParameters = {
      model: model,
      contents: processedContents,
      config: geminiApiConfig,
    };

    const stream = await ai.models.generateContentStream(requestPayload);

    let fullText = ""; // Not strictly needed here if only passing chunks through
    for await (const chunk of stream) {
      const chunkText = chunk.text; // chunk.text is string type
      // Sending chunkText even if it's an empty string, as it might be a valid part of the stream
      onStreamChunk(chunkText, false);
      fullText += chunkText; // Accumulate fullText if needed for local processing, though not used in this function's return
    }
    onStreamChunk("", true); // Signal completion of stream

  } catch (error: any) {
    console.error("Error calling Gemini API (stream):", error);
    let errorMessage = "An unknown error occurred with the Gemini API stream.";
     if (error.message) {
      errorMessage = error.message;
    } else if (typeof error === 'string') {
      errorMessage = error;
    }
    onError(`Gemini API Stream Error: ${errorMessage}`);
  }
};