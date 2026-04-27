import type { FormEvent } from 'react';
import type { Preferences } from '../utils/preferencesContext';
import type { ManualPreferencesPayload } from '../types';
import PreferenceInput from './PreferenceInput';

type RequestBuilderProps = {
    preferences: Preferences;
    isLoading: boolean;
    savedTasteProfile: ManualPreferencesPayload;
    error: string;
    onPreferenceChange: <K extends keyof Preferences>(field: K, value: Preferences[K]) => void;
    onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

export default function RequestBuilder({
    preferences,
    isLoading,
    error,
    onPreferenceChange,
    onSubmit,
}: RequestBuilderProps) {

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
                    {error ? <p className="status error">{error}</p> : null}
                    <label className="helper-text" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                        <input
                            style={{flex: 0}}
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
                        label="Top K songs"
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
