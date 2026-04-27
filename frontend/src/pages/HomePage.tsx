import type { FormEvent } from 'react';
import RequestBuilder from '../components/RequestBuilder';
import ResultsDisplay from '../components/ResultsDisplay';
import SongPlayer from '../components/SongPlayer';
import type {
    AIRecommendationRequestPayload,
    AIRecommendationResponse,
    ManualPreferencesPayload,
    Song,
} from '../types';
import type { Preferences } from '../utils/preferencesContext';

type HomePageProps = {
    preferences: Preferences;
    isLoading: boolean;
    requestPreview: AIRecommendationRequestPayload;
    savedTasteProfile: ManualPreferencesPayload;
    results: AIRecommendationResponse | null;
    selectedSong: Song | null;
    error: string;
    onPreferenceChange: <K extends keyof Preferences>(field: K, value: Preferences[K]) => void;
    onReset: () => void;
    onSubmit: (event: FormEvent<HTMLFormElement>) => void;
    onSongSelect: (song: Song | null) => void;
};

export default function HomePage({
    preferences,
    isLoading,
    requestPreview,
    savedTasteProfile,
    results,
    selectedSong,
    error,
    onPreferenceChange,
    onSubmit,
    onSongSelect,
}: HomePageProps) {
    return (
        <>
            <div className="layout">
                <RequestBuilder
                    preferences={preferences}
                    isLoading={isLoading}
                    savedTasteProfile={savedTasteProfile}
                    onPreferenceChange={onPreferenceChange}
                    onSubmit={onSubmit}
                />

                <div className="results-area">
                    {selectedSong ? <SongPlayer song={selectedSong} /> : null}
                    <ResultsDisplay
                        isLoading={isLoading}
                        results={results}
                        error={error}
                        selectedSongId={selectedSong?.id ?? null}
                        onSongSelect={onSongSelect}
                    />
                </div>
            </div>
        </>
    );
}
