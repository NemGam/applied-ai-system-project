import type { Preferences } from '../utils/preferencesContext';
import { formatGenreWithIcon, formatMoodWithIcon } from '../utils/genreIcons';
import GenreSelect from './GenreSelect';
import PreferenceInput from './PreferenceInput';

const GENRE_OPTIONS = [
    'ambient',
    'electronic',
    'hip hop',
    'indie pop',
    'jazz',
    'lofi',
    'pop',
    'rock',
    'synthwave',
];

const MOOD_OPTIONS = ['chill', 'energetic', 'focused', 'happy', 'intense', 'moody', 'relaxed'];

const CONTEXT_OPTIONS = [
    'cafe',
    'commute',
    'deep_work',
    'dinner',
    'night_drive',
    'party',
    'reading',
    'sleep',
    'study',
    'walk',
    'workout',
];

type ProfilePreferencesPanelProps = {
    preferences: Preferences;
    onPreferenceChange: <K extends keyof Preferences>(field: K, value: Preferences[K]) => void;
};

export default function ProfilePreferencesPanel({
    preferences,
    onPreferenceChange
}: ProfilePreferencesPanelProps) {
    return (
        <section className="panel preferences-panel">
            <div className="panel-header">
                <div>
                    <h2>Your taste profile</h2>
                    <p>These manual values shape your saved profile and support personalization on Home.</p>
                </div>
            </div>

            <div className="inputs">
                <div className="main-selectors">
                    <GenreSelect
                        label="Genre"
                        value={preferences.genre}
                        options={GENRE_OPTIONS}
                        onChange={(value) => onPreferenceChange('genre', value)}
                        formatOptionLabel={formatGenreWithIcon}
                    />

                    <GenreSelect
                        label="Mood"
                        value={preferences.mood}
                        options={MOOD_OPTIONS}
                        onChange={(value) => onPreferenceChange('mood', value)}
                        formatOptionLabel={formatMoodWithIcon}
                    />

                    <GenreSelect
                        label="Listening context"
                        value={preferences.listeningContext}
                        options={CONTEXT_OPTIONS}
                        onChange={(value) => onPreferenceChange('listeningContext', value)}
                    />

                    <PreferenceInput
                        label="Mood tags"
                        value={preferences.preferredMoodTags}
                        onChange={(value) => onPreferenceChange('preferredMoodTags', value)}
                        placeholder="focused, nocturnal, warm"
                    />
                </div>

                <div className="numeric-fields-grid">
                    <PreferenceInput
                        label="Energy"
                        type="number"
                        min="0"
                        max="1"
                        step="0.01"
                        value={preferences.energy}
                        onChange={(value) => onPreferenceChange('energy', value)}
                    />

                    <PreferenceInput
                        label="Danceability"
                        type="number"
                        min="0"
                        max="1"
                        step="0.01"
                        value={preferences.danceability}
                        onChange={(value) => onPreferenceChange('danceability', value)}
                    />

                    <PreferenceInput
                        label="Acousticness"
                        type="number"
                        min="0"
                        max="1"
                        step="0.01"
                        value={preferences.acousticness}
                        onChange={(value) => onPreferenceChange('acousticness', value)}
                    />

                    <PreferenceInput
                        label="Vocal presence"
                        type="number"
                        min="0"
                        max="1"
                        step="0.01"
                        value={preferences.vocalPresence}
                        onChange={(value) => onPreferenceChange('vocalPresence', value)}
                    />

                    <PreferenceInput
                        label="Valence"
                        type="number"
                        min="0"
                        max="1"
                        step="0.01"
                        value={preferences.valence}
                        onChange={(value) => onPreferenceChange('valence', value)}
                    />

                    <PreferenceInput
                        label="Tempo"
                        type="number"
                        min="0"
                        step="1"
                        value={preferences.tempoBpm}
                        onChange={(value) => onPreferenceChange('tempoBpm', value)}
                    />
                </div>
            </div>
        </section>
    );
}
