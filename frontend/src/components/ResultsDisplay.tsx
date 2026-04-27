import type { AIRecommendationResponse, Song } from '../types';
import heroImage from '../assets/hero.png';
import SongCard from './SongCard';
import styles from './ResultsDisplay.module.css';

type ResultsDisplayProps = {
    error: string;
    isLoading: boolean;
    results: AIRecommendationResponse | null;
    selectedSongId: number | null;
    onSongSelect: (song: Song) => void;
    onReset: () => void;
};

export default function ResultsDisplay({
    error,
    isLoading,
    results,
    selectedSongId,
    onSongSelect,
    onReset,
}: ResultsDisplayProps) {
    const featuredSongId = selectedSongId ?? results?.results[0]?.song.id ?? null;
    const otherResults = results?.results.filter((item) => item.song.id !== featuredSongId) ?? [];
    const rankingStatus =
        results?.providers.ranking === 'gemini'
            ? 'Ranking: Gemini reranked the final list'
            : 'Ranking: Deterministic order kept';

    return (
        <section className="panel results-panel results-panel--visible">
            <div className="panel-header">
                <div>
                    <h2>Top recommendations</h2>
                    <p>
                        Retrieval narrows the catalog, then the deterministic recommender ranks the
                        candidates, with optional Gemini reranking on top.
                    </p>
                </div>
                {results && !isLoading ? (
                    <button type="button" className={styles.resetButton} onClick={onReset}>
                        Pick something else
                    </button>
                ) : null}
            </div>

            {error ? <p className="status error">{error}</p> : null}
            {!results && !error && !isLoading ? (
                <p className="status">Submit a request to run the full recommendation pipeline.</p>
            ) : null}
            {isLoading ? (
                <div className={styles.loadingState}>
                    <img
                        className={styles.loadingImage}
                        src={heroImage}
                        alt="Illustration for recommendation loading state"
                    />
                    <div className={styles.loadingCopy}>
                        <p className={styles.loadingTitle}>Surfing your vibes...</p>
                        <p className={styles.loadingText}>
                            Parsing your request, digging through the catalog, and lining up the
                            best matches.
                        </p>
                    </div>
                </div>
            ) : null}

            {results ? (
                <div className={styles.resultsStack}>
                    <section className={styles.summaryCard}>
                        <span className={styles.summaryLabel}>User request</span>
                        <p className={styles.summaryText}>{results.user_request}</p>
                        <div className={styles.summaryMeta}>
                            {/* <span className={styles.highlightChip}>{rankingStatus}</span> */}
                            {/* <span>Parser: {results.providers.parser}</span> */}
                            {/* <span>Explanations: {results.providers.explanations}</span> */}
                            <span>Retrieval: {results.retrieval.strategy}</span>
                            <span>Candidates retrieved: {results.retrieval.candidate_count}</span>
                        </div>

                        <p className={styles.overallExplanation}>{results.overall_explanation}</p>
                    </section>

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
