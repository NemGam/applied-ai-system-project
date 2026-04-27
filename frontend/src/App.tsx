import { type FormEvent, useMemo, useState } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import HomePage from './pages/HomePage';
import ProfilePage from './pages/ProfilePage';
import type {
    AIRecommendationRequestPayload,
    AIRecommendationResponse,
    ManualPreferencesPayload,
    Song,
} from './types';
import { usePreferencesContext } from './utils/preferencesContext';
import Sidebar from './components/Sidebar';

const API_BASE_URL = 'http://127.0.0.1:8000';

const APP_TABS = [
    {
        to: '/',
        label: 'Home',
        eyebrow: 'Discover',
        title: 'VibeFlow',
        description: 'Build prompts, run recommendations, and explore ranked results.',
        icon: 'H',
    },
    {
        to: '/profile',
        label: 'Profile',
        eyebrow: 'Taste profile',
        title: 'Your Profile',
        description: 'Edit the listening signals and defaults saved in VibeFlow.',
        icon: 'P',
    },
] as const;

function splitCsv(value: string): string[] {
    return value
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean);
}

function parseNumber(value: string): number | undefined {
    if (!value.trim()) {
        return undefined;
    }

    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : undefined;
}

export default function App() {
    const { preferences, updatePreference, resetPreferences } = usePreferencesContext();
    const [results, setResults] = useState<AIRecommendationResponse | null>(null);
    const [selectedSong, setSelectedSong] = useState<Song | null>(null);
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const manualPreferences = useMemo<ManualPreferencesPayload>(
        () => ({
            genre: preferences.genre || undefined,
            mood: preferences.mood || undefined,
            listening_context: preferences.listeningContext || undefined,
            preferred_mood_tags: splitCsv(preferences.preferredMoodTags),
            energy: parseNumber(preferences.energy),
            tempo_bpm: parseNumber(preferences.tempoBpm),
            danceability: parseNumber(preferences.danceability),
            acousticness: parseNumber(preferences.acousticness),
            vocal_presence: parseNumber(preferences.vocalPresence),
            valence: parseNumber(preferences.valence),
        }),
        [preferences],
    );

    const requestPreview = useMemo<AIRecommendationRequestPayload>(
        () => ({
            user_text: preferences.userText,
            manual_preferences: null,
            taste_profile: preferences.useTasteProfile ? manualPreferences : null,
            k: parseNumber(preferences.k) ?? 5,
            retrieval_k: 20,
        }),
        [manualPreferences, preferences.k, preferences.useTasteProfile, preferences.userText],
    );

    const profileHighlights = useMemo(
        () => [
            { label: 'Favorite genre', value: preferences.genre || 'Open to anything' },
            { label: 'Current mood', value: preferences.mood || 'Not set' },
            { label: 'Listening context', value: preferences.listeningContext || 'Not set' },
            {
                label: 'Mood tags',
                value: splitCsv(preferences.preferredMoodTags).join(', ') || 'Not set',
            },
        ],
        [
            preferences.genre,
            preferences.listeningContext,
            preferences.mood,
            preferences.preferredMoodTags,
        ],
    );

    const profileMetrics = useMemo(
        () => [
            { label: 'Energy', value: preferences.energy || 'Not set' },
            { label: 'Tempo BPM', value: preferences.tempoBpm || 'Not set' },
            { label: 'Danceability', value: preferences.danceability || 'Not set' },
            { label: 'Acousticness', value: preferences.acousticness || 'Not set' },
            { label: 'Vocal presence', value: preferences.vocalPresence || 'Not set' },
            { label: 'Valence', value: preferences.valence || 'Not set' },
        ],
        [
            preferences.acousticness,
            preferences.danceability,
            preferences.energy,
            preferences.tempoBpm,
            preferences.valence,
            preferences.vocalPresence,
        ],
    );

    async function handleSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setIsLoading(true);
        setError('');
        setResults(null);
        setSelectedSong(null);

        try {
            const response = await fetch(`${API_BASE_URL}/recommendations/ai`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestPreview),
            });

            if (!response.ok) {
                const errorBody = (await response.json().catch(() => null)) as
                    | { detail?: string }
                    | null;
                throw new Error(errorBody?.detail || `Request failed with status ${response.status}`);
            }

            const data: AIRecommendationResponse = await response.json();
            if (data.guardrail?.triggered) {
                setError(data.guardrail.message || 'That request is outside the supported music scope.');
                return;
            }
            setResults(data);
            setSelectedSong(data.results[0]?.song ?? null);
        } catch (submissionError) {
            const message =
                submissionError instanceof Error
                    ? submissionError.message
                    : 'Unexpected request error';
            setError(message);
        } finally {
            setIsLoading(false);
        }
    }

    return (
        <main className="app-shell">
            <Sidebar tabs={APP_TABS} />

            <section className="page-shell">
                <Routes>
                    <Route
                        path="/"
                        element={
                            <HomePage
                                hero={APP_TABS[0]}
                                preferences={preferences}
                                isLoading={isLoading}
                                savedTasteProfile={manualPreferences}
                                results={results}
                                selectedSong={selectedSong}
                                error={error}
                                onPreferenceChange={updatePreference}
                                onSubmit={handleSubmit}
                                onSongSelect={setSelectedSong}
                            />
                        }
                    />
                    <Route
                        path="/profile"
                        element={
                            <ProfilePage
                                hero={APP_TABS[1]}
                                preferences={preferences}
                                profileHighlights={profileHighlights}
                                profileMetrics={profileMetrics}
                                onPreferenceChange={updatePreference}
                                onReset={resetPreferences}
                            />
                        }
                    />
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
            </section>
        </main>
    );
}
