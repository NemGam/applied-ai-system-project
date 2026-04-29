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
import DiscoverPage from './pages/DiscoverPage';
import SongPlayer from './components/SongPlayer';

const API_BASE_URL = 'http://127.0.0.1:8000';

const APP_TABS = [
    {
        to: '/',
        label: 'Home',
        eyebrow: 'Discover',
        title: 'VibeFlow',
        description: 'Explore your recommendations.',
        icon: 'H',
    },
    {
        to: '/discover',
        label: 'Discover',
        eyebrow: 'Taste profile',
        title: 'Your Profile',
        description: 'Discover new songs that match your current vibe.',
        icon: 'D',
    },
    {
        to: '/profile',
        label: 'Profile',
        eyebrow: 'Taste profile',
        title: 'Your Profile',
        description: 'Edit your listening profile in VibeFlow.',
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
    const [homeResults, setHomeResults] = useState<AIRecommendationResponse | null>(null);
    const [discoverResults, setDiscoverResults] = useState<AIRecommendationResponse | null>(null);
    const [selectedSong, setSelectedSong] = useState<Song | null>(null);
    const [homeError, setHomeError] = useState('');
    const [discoverError, setDiscoverError] = useState('');
    const [isHomeLoading, setIsHomeLoading] = useState(false);
    const [isDiscoverLoading, setIsDiscoverLoading] = useState(false);

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

    async function fetchRecommendations(
        payload: AIRecommendationRequestPayload,
    ): Promise<AIRecommendationResponse> {
        const response = await fetch(`${API_BASE_URL}/recommendations/ai`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            const errorBody = (await response.json().catch(() => null)) as
                | { detail?: string }
                | null;
            throw new Error(errorBody?.detail || `Request failed with status ${response.status}`);
        }

        const data: AIRecommendationResponse = await response.json();
        if (data.guardrail?.triggered) {
            throw new Error(
                data.guardrail.message || 'That request is outside the supported music scope.',
            );
        }

        return data;
    }

    async function runRecommendations(
        payload: AIRecommendationRequestPayload,
        handlers: {
            setLoading: (value: boolean) => void;
            setError: (value: string) => void;
            setResults: (value: AIRecommendationResponse | null) => void;
        },
        options?: {
            autoSelectFirstSong?: boolean;
            preserveSelectedSong?: boolean;
        },
    ) {
        const autoSelectFirstSong = options?.autoSelectFirstSong ?? true;
        const preserveSelectedSong = options?.preserveSelectedSong ?? false;
        handlers.setLoading(true);
        handlers.setError('');
        handlers.setResults(null);
        if (!preserveSelectedSong) {
            setSelectedSong(null);
        }

        try {
            const data = await fetchRecommendations(payload);
            handlers.setResults(data);
            if (autoSelectFirstSong) {
                setSelectedSong(data.results[0]?.song ?? null);
            }
        } catch (submissionError) {
            const message =
                submissionError instanceof Error
                    ? submissionError.message
                    : 'Unexpected request error';
            handlers.setError(message);
        } finally {
            handlers.setLoading(false);
        }
    }

    async function handleSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        await runRecommendations(
            requestPreview,
            {
                setLoading: setIsDiscoverLoading,
                setError: setDiscoverError,
                setResults: setDiscoverResults,
            },
        );
    }

    async function handleHomeRecommendations() {
        await runRecommendations(
            {
                user_text: null,
                manual_preferences: manualPreferences,
                taste_profile: null,
                k: parseNumber(preferences.k) ?? 5,
                retrieval_k: 20,
            },
            {
                setLoading: setIsHomeLoading,
                setError: setHomeError,
                setResults: setHomeResults,
            },
            {
                autoSelectFirstSong: false,
                preserveSelectedSong: true,
            },
        );
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
                                preferences={preferences}
                                isLoading={isHomeLoading}
                                savedTasteProfile={manualPreferences}
                                results={homeResults}
                                selectedSong={selectedSong}
                                error={homeError}
                                onLoadRecommendations={handleHomeRecommendations}
                                onSongSelect={setSelectedSong}
                            />
                        }
                    />
                    <Route
                        path="/discover"
                        element={
                            <DiscoverPage
                                preferences={preferences}
                                isLoading={isDiscoverLoading}
                                savedTasteProfile={manualPreferences}
                                results={discoverResults}
                                selectedSong={selectedSong}
                                error={discoverError}
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

            <SongPlayer song={selectedSong} />
        </main>
    );
}
