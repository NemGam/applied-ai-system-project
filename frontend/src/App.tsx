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
const HOME_RECOMMENDATION_CACHE_PREFIX = 'home-recommendations:';

const APP_TABS = [
    {
        to: '/',
        label: 'Home',
        description: 'Explore your recommendations.',
        icon: 'H',
    },
    {
        to: '/discover',
        label: 'Discover',
        description: 'Discover new songs that match your current vibe.',
        icon: 'D',
    },
    {
        to: '/profile',
        label: 'Profile',
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

function getRecommendationCacheKey(payload: AIRecommendationRequestPayload): string {
    return `${HOME_RECOMMENDATION_CACHE_PREFIX}${JSON.stringify(payload)}`;
}

function readCachedRecommendations(cacheKey: string): AIRecommendationResponse | null {
    if (typeof window === 'undefined') {
        return null;
    }

    const cachedValue = window.sessionStorage.getItem(cacheKey);
    if (!cachedValue) {
        return null;
    }

    try {
        return JSON.parse(cachedValue) as AIRecommendationResponse;
    } catch {
        window.sessionStorage.removeItem(cacheKey);
        return null;
    }
}

function writeCachedRecommendations(
    cacheKey: string,
    data: AIRecommendationResponse,
) {
    if (typeof window === 'undefined') {
        return;
    }

    window.sessionStorage.setItem(cacheKey, JSON.stringify(data));
}

export default function App() {
    const { preferences, updatePreference } = usePreferencesContext();
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

    const homeRequestPayload = useMemo<AIRecommendationRequestPayload>(
        () => ({
            user_text: null,
            manual_preferences: manualPreferences,
            taste_profile: null,
            k: parseNumber(preferences.k) ?? 5,
            retrieval_k: 20,
        }),
        [manualPreferences, preferences.k],
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
            cacheKey?: string;
        },
    ) {
        const autoSelectFirstSong = options?.autoSelectFirstSong ?? true;
        const preserveSelectedSong = options?.preserveSelectedSong ?? false;
        const cacheKey = options?.cacheKey;
        const cachedResults = cacheKey ? readCachedRecommendations(cacheKey) : null;

        if (cachedResults) {
            handlers.setError('');
            handlers.setLoading(false);
            handlers.setResults(cachedResults);
            if (autoSelectFirstSong) {
                setSelectedSong(cachedResults.results[0]?.song ?? null);
            }
            return;
        }

        handlers.setLoading(true);
        handlers.setError('');
        handlers.setResults(null);
        if (!preserveSelectedSong) {
            setSelectedSong(null);
        }

        try {
            const data = await fetchRecommendations(payload);
            if (cacheKey) {
                writeCachedRecommendations(cacheKey, data);
            }
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
            homeRequestPayload,
            {
                setLoading: setIsHomeLoading,
                setError: setHomeError,
                setResults: setHomeResults,
            },
            {
                autoSelectFirstSong: false,
                preserveSelectedSong: true,
                cacheKey: getRecommendationCacheKey(homeRequestPayload),
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
                                onPreferenceChange={updatePreference}
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
