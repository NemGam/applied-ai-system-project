import { type FormEvent, useState } from 'react';
import RequestBuilder from '../components/RequestBuilder';
import ResultsDisplay from '../components/ResultsDisplay';
import SongPlayer from '../components/SongPlayer';
import type {
    AIRecommendationResponse,
    ManualPreferencesPayload,
    Song,
} from '../types';
import type { Preferences } from '../utils/preferencesContext';

type HomePageProps = {
    hero?: {
        to: string;
        label: string;
        eyebrow: string;
        title: string;
        description: string;
        icon: string;
    };
    preferences: Preferences;
    isLoading: boolean;
    savedTasteProfile: ManualPreferencesPayload;
    results: AIRecommendationResponse | null;
    selectedSong: Song | null;
    error: string;
    onPreferenceChange: <K extends keyof Preferences>(field: K, value: Preferences[K]) => void;
    onSubmit: (event: FormEvent<HTMLFormElement>) => void;
    onSongSelect: (song: Song | null) => void;
};

export default function HomePage({
    preferences,
    isLoading,
    savedTasteProfile,
    results,
    selectedSong,
    error,
    onPreferenceChange,
    onSubmit,
    onSongSelect,
}: HomePageProps) {
    const [hasRequestedRecommendations, setHasRequestedRecommendations] = useState(false);
    const showResults = hasRequestedRecommendations && !(error && !isLoading && !results);

    function handleSubmit(event: FormEvent<HTMLFormElement>) {
        setHasRequestedRecommendations(true);
        onSubmit(event);
    }

    return (
        <>
            <div
                className={`layout home-layout${
                    showResults ? ' home-layout--results' : ''
                }`}
            >
                <div
                    className={`request-builder-wrap${
                        showResults ? ' request-builder-wrap--hidden' : ''
                    }`}
                    aria-hidden={showResults}
                >
                    <RequestBuilder
                        preferences={preferences}
                        isLoading={isLoading}
                        savedTasteProfile={savedTasteProfile}
                        error={error}
                        onPreferenceChange={onPreferenceChange}
                        onSubmit={handleSubmit}
                    />
                </div>

                <div
                    className={`results-area home-results${
                        showResults ? ' home-results--visible' : ''
                    }`}
                >
                    {selectedSong ? <SongPlayer song={selectedSong} /> : null}
                    <ResultsDisplay
                        isLoading={isLoading}
                        results={results}
                        error={error}
                        selectedSongId={selectedSong?.id ?? null}
                        onSongSelect={onSongSelect}
                        onReset={() => setHasRequestedRecommendations(false)}
                    />
                </div>
            </div>
        </>
    );
}
