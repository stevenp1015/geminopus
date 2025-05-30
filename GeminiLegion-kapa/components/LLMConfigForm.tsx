
import React, { useState, useEffect } from 'react';
import { MinionConfig, ModelOption } from '../types';
import { GEMINI_MODELS_OPTIONS } from '../constants'; // Default/example models
import Spinner from './Spinner';
// import { legionApiService } from '../services/legionApiService'; // To be used for model fetching

interface MinionConfigFormProps {
  initialConfig?: MinionConfig;
  onSave: (config: MinionConfig) => void;
  onCancel: () => void;
  existingNames: string[];
  // In future, this might take a legionApiService instance or use a context
}

const MinionConfigForm: React.FC<MinionConfigFormProps> = ({ initialConfig, onSave, onCancel, existingNames }) => {
  const [config, setConfig] = useState<MinionConfig>(
    initialConfig || {
      id: `minion-${Date.now()}`, // Temporary ID for new configs
      name: '',
      provider: 'google', // Handled by backend, but good for UI consistency
      model_id: GEMINI_MODELS_OPTIONS[0]?.id || '',
      system_prompt_persona: 'You are a helpful and devoted Minion of the Gemini Legion, serving Legion Commander Steven.',
      params: { temperature: 0.7 },
      opinionScores: {}, // Initialized by backend or App.tsx when fully added
      status: 'Pending Configuration',
    }
  );
  const [nameError, setNameError] = useState<string | null>(null);
  const [modelOptions, setModelOptions] = useState<ModelOption[]>(GEMINI_MODELS_OPTIONS); // Init with defaults
  const [isLoadingModels, setIsLoadingModels] = useState(false);
  const [modelError, setModelError] = useState<string | null>(null);


  useEffect(() => {
    if (initialConfig) {
      setConfig(initialConfig);
    }
  }, [initialConfig]);

  useEffect(() => {
    // This would fetch models from the Legion Backend in a real scenario
    // For now, we use defaults, but structure for async fetching.
    const fetchModels = async () => {
      setIsLoadingModels(true);
      setModelError(null);
      try {
        // const models = await legionApiService.getMinionModels(); // Example future call
        // setModelOptions(models.length > 0 ? models : GEMINI_MODELS_OPTIONS);
        setModelOptions(GEMINI_MODELS_OPTIONS); // Mock: use constants for now
      } catch (error: any) {
        setModelError(`Failed to fetch models: ${error.message}`);
        setModelOptions(GEMINI_MODELS_OPTIONS); // Fallback to defaults
      } finally {
        setIsLoadingModels(false);
      }
    };
    fetchModels();
  }, []);


  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    if (name === 'temperature') {
      setConfig(prev => ({ ...prev, params: { ...prev.params, temperature: parseFloat(value) } }));
    } else if (name === 'name') {
      setConfig(prev => ({ ...prev, [name]: value }));
      if (!initialConfig || (initialConfig && initialConfig.name !== value)) {
        if (existingNames.includes(value)) {
          setNameError('This Minion name is already in use. Please choose a unique name.');
        } else {
          setNameError(null);
        }
      } else {
        setNameError(null);
      }
    } else {
      setConfig(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (nameError) return;
    if (!config.name.trim()) {
      setNameError("Minion Name cannot be empty.");
      return;
    }
    const configToSave: MinionConfig = { 
        ...config, 
        opinionScores: config.opinionScores || {},
        status: config.status || 'Idle' // Ensure status is set
    };
    onSave(configToSave);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 text-gray-200">
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-300 mb-1">
          Minion Name (Unique)
        </label>
        <input
          type="text"
          name="name"
          id="name"
          value={config.name}
          onChange={handleChange}
          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md shadow-sm focus:ring-sky-500 focus:border-sky-500 sm:text-sm placeholder-gray-500"
          placeholder="e.g., Alpha, CodexMinion, Grandma Hairstylist"
          required
        />
        {nameError && <p className="mt-1 text-xs text-red-400">{nameError}</p>}
      </div>

      <div>
        <label htmlFor="provider" className="block text-sm font-medium text-gray-300 mb-1">
          Provider (via ADK Backend)
        </label>
        <select
          name="provider"
          id="provider"
          value={config.provider}
          onChange={handleChange}
          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md shadow-sm focus:ring-sky-500 focus:border-sky-500 sm:text-sm"
          disabled // Provider is determined by backend ADK agent setup
        >
          <option value="google">Google (Gemini via ADK)</option>
        </select>
      </div>
      
      <div>
        <label htmlFor="model_id" className="block text-sm font-medium text-gray-300 mb-1">
          Model ID
        </label>
        {isLoadingModels && <div className="flex items-center gap-2 text-sm text-gray-400"><Spinner size="sm"/> Fetching models...</div>}
        {modelError && <div className="text-xs text-red-400 my-1">{modelError}</div>}
        <select
          name="model_id"
          id="model_id"
          value={config.model_id}
          onChange={handleChange}
          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md shadow-sm focus:ring-sky-500 focus:border-sky-500 sm:text-sm"
          disabled={isLoadingModels || modelError !== null && modelOptions.length === GEMINI_MODELS_OPTIONS.length}
        >
          {modelOptions.length === 0 && !isLoadingModels && <option value="">No models available</option>}
          {modelOptions.map(model => (
            <option key={model.id} value={model.id}>{model.name}</option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="system_prompt_persona" className="block text-sm font-medium text-gray-300 mb-1">
          Persona & Fire Code (System Prompt)
        </label>
        <textarea
          name="system_prompt_persona"
          id="system_prompt_persona"
          value={config.system_prompt_persona}
          onChange={handleChange}
          rows={8}
          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md shadow-sm focus:ring-sky-500 focus:border-sky-500 sm:text-sm placeholder-gray-500"
          placeholder="Describe the Minion's personality, core directives (Fire Code), skills, quirks, etc."
        />
        <p className="mt-1 text-xs text-gray-400">This prompt dictates the Minion's behavior and is used by the ADK backend.</p>
      </div>

      <div>
        <label htmlFor="temperature" className="block text-sm font-medium text-gray-300 mb-1">
          Temperature: {config.params.temperature.toFixed(2)}
        </label>
        <input
          type="range"
          name="temperature"
          id="temperature"
          min="0"
          max="1" 
          step="0.01"
          value={config.params.temperature}
          onChange={handleChange}
          className="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer accent-sky-500"
        />
      </div>
      
      <div className="flex justify-end gap-3 pt-4">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm font-medium text-gray-300 bg-gray-600 hover:bg-gray-500 rounded-md shadow-sm transition-colors"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={!!nameError || !config.name.trim() || isLoadingModels}
          className="px-4 py-2 text-sm font-medium text-white bg-sky-600 hover:bg-sky-700 rounded-md shadow-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Save Minion Configuration
        </button>
      </div>
    </form>
  );
};

export default MinionConfigForm;
