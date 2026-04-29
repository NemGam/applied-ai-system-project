import { useEffect, useMemo, useRef } from 'react';
import ResultsDisplay from '../components/ResultsDisplay';
import type { AIRecommendationResponse, ManualPreferencesPayload, Song } from '../types';
import type { Preferences } from '../utils/preferencesContext';

type HomePageProps = {
    preferences: Preferences;
    isLoading: boolean;
    savedTasteProfile: ManualPreferencesPayload;
    results: AIRecommendationResponse | null;
    selectedSong: Song | null;
    error: string;
    onLoadRecommendations: () => Promise<void>;
    onSongSelect: (song: Song | null) => void;
};

export default function HomePage({
    preferences,
    isLoading,
    savedTasteProfile,
    results,
    selectedSong,
    error,
    onLoadRecommendations,
    onSongSelect,
}: HomePageProps) {
    const lastProfileRequestKeyRef = useRef<string>('');
    const profileRequestKey = useMemo(
        () =>
            JSON.stringify({
                savedTasteProfile,
                k: preferences.k,
            }),
        [preferences.k, savedTasteProfile],
    );

    useEffect(() => {
        if (lastProfileRequestKeyRef.current === profileRequestKey) {
            return;
        }

        lastProfileRequestKeyRef.current = profileRequestKey;
        void onLoadRecommendations();
    }, [onLoadRecommendations, profileRequestKey]);

    return (
        <div className={`home-layout`}>
            <ResultsDisplay
                isLoading={isLoading}
                results={results}
                error={error}
                selectedSongId={selectedSong?.id ?? null}
                onSongSelect={onSongSelect}
            />
        </div>
    );
}
