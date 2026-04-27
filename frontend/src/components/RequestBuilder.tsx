import type { FormEvent } from 'react';
import type { Preferences } from '../utils/preferencesContext';
import type { ManualPreferencesPayload } from '../types';
import PreferenceInput from './PreferenceInput';

type RequestBuilderProps = {
    preferences: Preferences;
    isLoading: boolean;
    savedTasteProfile: ManualPreferencesPayload;
    onPreferenceChange: <K extends keyof Preferences>(field: K, value: Preferences[K]) => void;
    onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

function summarizeTasteProfile(profile: ManualPreferencesPayload): string[] {
    const items: string[] = [];
    if (profile.genre) items.push(`genre ${profile.genre}`);
    if (profile.mood) items.push(`mood ${profile.mood}`);
    if (profile.listening_context) items.push(`context ${profile.listening_context}`);
    if (profile.preferred_mood_tags.length) items.push(`tags ${profile.preferred_mood_tags.join(', ')}`);
    if (profile.energy !== undefined) items.push(`energy ${profile.energy.toFixed(2)}`);
    if (profile.acousticness !== undefined) items.push(`acousticness ${profile.acousticness.toFixed(2)}`);
    if (profile.vocal_presence !== undefined) items.push(`vocal ${profile.vocal_presence.toFixed(2)}`);
    if (profile.tempo_bpm !== undefined) items.push(`tempo ${profile.tempo_bpm}`);
    return items;
}

export default function RequestBuilder({
    preferences,
    isLoading,
    savedTasteProfile,
    onPreferenceChange,
    onSubmit,
}: RequestBuilderProps) {
    const tasteProfileSummary = summarizeTasteProfile(savedTasteProfile);

    return (
        <section className="panel preferences-panel">
            <div className="panel-header">
                <div>
                    <h2>Request builder</h2>
                    <p>Describe the vibe in plain English, then run the recommender.</p>
                </div>
            </div>

            <form className="preference-form" onSubmit={onSubmit}>
                <div className="natural-language-panel">
                    <PreferenceInput
                        label="Describe the vibe"
                        value={preferences.userText}
                        onChange={(value) => onPreferenceChange('userText', value)}
                        placeholder="I want chill music for late-night studying with soft vocals"
                        multiline
                        rows={6}
                    />
                    <p className="helper-text">
                        The backend parses this into structured preferences before retrieval and scoring.
                    </p>
                    <label className="helper-text" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                        <input
                            type="checkbox"
                            checked={preferences.useTasteProfile}
                            onChange={(event) =>
                                onPreferenceChange('useTasteProfile', event.target.checked)
                            }
                        />
                        Use my saved taste profile to personalize vague requests
                    </label>
                </div>

                <div className="form-footer">
                    <PreferenceInput
                        label="Top K"
                        type="number"
                        min="1"
                        max="20"
                        step="1"
                        value={preferences.k}
                        onChange={(value) => onPreferenceChange('k', value)}
                    />

                    <button type="submit" disabled={isLoading}>
                        {isLoading ? 'Running pipeline...' : 'Get recommendations'}
                    </button>
                </div>
            </form>
        </section>
    );
}
