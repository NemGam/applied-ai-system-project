import type { FormEvent } from 'react';
import type { Preferences } from '../utils/preferencesContext';
import type { ManualPreferencesPayload } from '../types';
import PreferenceInput from './PreferenceInput';
import styles from './RequestBuilder.module.css';

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
                    <h2>Vibe Search</h2>
                    <p>Describe your current vibe and get recommendations.</p>
                </div>
            </div>

            <form className={styles.preferenceForm} onSubmit={onSubmit}>
                <div className={styles.searchBar}>
                    <PreferenceInput
                        value={preferences.userText}
                        onChange={(value) => onPreferenceChange('userText', value)}
                        placeholder="I want chill music for late-night studying with soft vocals"
                    />
                    <button type="submit" disabled={isLoading}>
                        {isLoading ? 'Flowing...' : 'Find vibes'}
                    </button>
                    {error ? <p className="status error">{error}</p> : null}
                </div>
            </form>
        </section>
    );
}
