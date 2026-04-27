import type { AIRecommendationResponse, DetectedPreferences, Song } from '../types';
import SongCard from './SongCard';
import styles from './ResultsDisplay.module.css';

type ResultsDisplayProps = {
    error: string;
    isLoading: boolean;
    results: AIRecommendationResponse | null;
    selectedSongId: number | null;
    onSongSelect: (song: Song) => void;
};

const PREFERENCE_LABELS: Record<keyof DetectedPreferences, string> = {
    genres: 'Genres',
    moods: 'Moods',
    contexts: 'Contexts',
    mood_tags: 'Mood tags',
    energy: 'Energy',
    danceability: 'Danceability',
    acousticness: 'Acousticness',
    vocal_presence: 'Vocal presence',
    instrumental_focus: 'Instrumental focus',
    valence: 'Valence',
    tempo_bpm: 'Tempo',
};

function formatPreferenceValue(value: string[] | number | undefined): string {
    if (Array.isArray(value)) {
        return value.join(', ');
    }
    if (typeof value === 'number') {
        return Number.isInteger(value) ? String(value) : value.toFixed(2);
    }
    return '';
}

export default function ResultsDisplay({
    error,
    isLoading,
    results,
    selectedSongId,
    onSongSelect,
}: ResultsDisplayProps) {
    const detectedPreferenceEntries = results
        ? (Object.entries(results.detected_preferences) as Array<
              [keyof DetectedPreferences, string[] | number | undefined]
          >).filter(([, value]) => value !== undefined && (!(Array.isArray(value)) || value.length > 0))
        : [];
    const featuredSongId = selectedSongId ?? results?.results[0]?.song.id ?? null;
    const featuredResult = results?.results.find((item) => item.song.id === featuredSongId) ?? null;
    const otherResults = results?.results.filter((item) => item.song.id !== featuredSongId) ?? [];
    const preferencesLabel =
        results?.input_mode === 'hybrid' ? 'Merged preferences' : 'Detected preferences';
    const personalizationEntries = results
        ? (Object.entries(results.personalization.taste_profile) as Array<
              [keyof DetectedPreferences, string[] | number | undefined]
          >).filter(([, value]) => value !== undefined && (!(Array.isArray(value)) || value.length > 0))
        : [];

    return (
        <section className="panel results-panel results-panel--visible">
            <div className="panel-header">
                <div>
                    <h2>Top recommendations</h2>
                    <p>Retrieval narrows the catalog, then the math recommender ranks the candidates.</p>
                </div>
            </div>

            {error ? <p className="status error">{error}</p> : null}
            {!results && !error && !isLoading ? (
                <p className="status">Submit a request to run the full recommendation pipeline.</p>
            ) : null}
            {isLoading ? <p className="status">Parsing request, retrieving songs, and ranking results...</p> : null}

            {results ? (
                <div className={styles.resultsStack}>
                    <section className={styles.summaryCard}>
                        <span className={styles.summaryLabel}>User request</span>
                        <p className={styles.summaryText}>{results.user_request}</p>

                        <div className={styles.summaryMeta}>
                            <span>Parser: {results.providers.parser}</span>
                            <span>Explanations: {results.providers.explanations}</span>
                            <span>Retrieval: {results.retrieval.strategy}</span>
                            <span>Candidates retrieved: {results.retrieval.candidate_count}</span>
                            <span>
                                Personalization:{' '}
                                {results.personalization.enabled ? results.personalization.source : 'off'}
                            </span>
                            <span>Metadata matches: {results.retrieval.source_counts.metadata}</span>
                            <span>Lyrics matches: {results.retrieval.source_counts.lyrics}</span>
                            <span>Multi-source: {results.retrieval.source_counts.both}</span>
                        </div>

                        <p className={styles.overallExplanation}>{results.overall_explanation}</p>
                    </section>

                    <section className={styles.preferenceCard}>
                        <span className={styles.summaryLabel}>{preferencesLabel}</span>
                        <div className={styles.preferenceGrid}>
                            {detectedPreferenceEntries.map(([key, value]) => (
                                <div key={key} className={styles.preferenceItem}>
                                    <span className={styles.preferenceName}>{PREFERENCE_LABELS[key]}</span>
                                    <strong>{formatPreferenceValue(value)}</strong>
                                </div>
                            ))}
                        </div>
                    </section>

                    {results.personalization.enabled ? (
                        <section className={styles.preferenceCard}>
                            <span className={styles.summaryLabel}>Taste profile used</span>
                            <div className={styles.preferenceGrid}>
                                {personalizationEntries.map(([key, value]) => (
                                    <div key={`taste-${key}`} className={styles.preferenceItem}>
                                        <span className={styles.preferenceName}>{PREFERENCE_LABELS[key]}</span>
                                        <strong>{formatPreferenceValue(value)}</strong>
                                    </div>
                                ))}
                            </div>
                        </section>
                    ) : null}

                    {featuredResult ? (
                        <section className={styles.listSection}>
                            <div className={styles.sectionHeader}>
                                <h3>Selected recommendation</h3>
                                <span>{Math.round(featuredResult.score * 100)}% match</span>
                            </div>
                            <p className={styles.sectionText}>
                                The large player card is the currently selected song. Click any song below
                                to switch the selection.
                            </p>
                            <p className={styles.sectionText}>
                                Retrieved via {featuredResult.matched_sources.join(' + ') || 'no source match'}.
                                Metadata {featuredResult.retrieval_breakdown.metadata.toFixed(2)}, lyrics{' '}
                                {featuredResult.retrieval_breakdown.lyrics.toFixed(2)}.
                            </p>
                        </section>
                    ) : null}

                    <section className={styles.listSection}>
                        <div className={styles.sectionHeader}>
                            <h3>Other songs you might like</h3>
                            <span>{otherResults.length} more</span>
                        </div>

                        {otherResults.length ? (
                            <div className={styles.resultsGrid}>
                                {otherResults.map((item) => (
                                    <SongCard
                                        key={item.song.id}
                                        song={item.song}
                                        score={item.score}
                                        retrievalScore={item.retrieval_score}
                                        retrievalBreakdown={item.retrieval_breakdown}
                                        matchedSources={item.matched_sources}
                                        sourceReasons={item.source_reasons}
                                        llmExplanation={item.llm_explanation}
                                        mathExplanation={item.math_explanation}
                                        onSelect={onSongSelect}
                                    />
                                ))}
                            </div>
                        ) : (
                            <p className={styles.sectionText}>No additional recommendations were returned.</p>
                        )}
                    </section>
                </div>
            ) : null}
        </section>
    );
}
