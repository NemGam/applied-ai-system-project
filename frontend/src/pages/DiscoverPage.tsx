import type { FormEvent } from 'react';
import ResultsDisplay from '../components/ResultsDisplay';
import RequestBuilder from '../components/RequestBuilder';
import type { AIRecommendationResponse, Song } from '../types';
import type { Preferences } from '../utils/preferencesContext';

type DiscoverPageProps = {
    preferences: Preferences;
    isLoading: boolean;
    results: AIRecommendationResponse | null;
    selectedSong: Song | null;
    error: string;
    onPreferenceChange: <K extends keyof Preferences>(field: K, value: Preferences[K]) => void;
    onSubmit: (event: FormEvent<HTMLFormElement>) => void;
    onSongSelect: (song: Song | null) => void;
};

export default function DiscoverPage({
    preferences,
    isLoading,
    results,
    selectedSong,
    error,
    onPreferenceChange,
    onSubmit,
    onSongSelect,
}: DiscoverPageProps) {
    return (
        <div className="discover-page-layout">
            <RequestBuilder
                preferences={preferences}
                isLoading={isLoading}
                error={error}
                onPreferenceChange={onPreferenceChange}
                onSubmit={onSubmit}
            />

            <div className="discover-results-shell">
                <ResultsDisplay
                    isLoading={isLoading}
                    results={results}
                    error={error}
                    selectedSongId={selectedSong?.id ?? null}
                    onSongSelect={(song) => onSongSelect(song)}
                />
            </div>
        </div>
    );
}
