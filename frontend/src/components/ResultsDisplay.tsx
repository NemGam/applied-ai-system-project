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
};

export default function ResultsDisplay({
    error,
    isLoading,
    results,
    selectedSongId,
    onSongSelect,
}: ResultsDisplayProps) {

    return (
        <section className={`panel ${styles.resultsPanel}`}>
            <div className="panel-header">
                <div>
                    <h2> Vibe Match</h2>
                    <p>
                        Retrieval narrows the catalog, then the deterministic recommender ranks the
                        candidates, with optional Gemini reranking on top.
                    </p>
                </div>
            </div>

            {error ? <p className="status error">{error}</p> : null}
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
                    {results.results.length ? (
                        <div className={styles.resultsGrid}>
                            {results.results?.map((item) => (
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
                                    selected={item.song.id === selectedSongId}
                                />
                            ))}
                        </div>
                    ) : (
                        <p className={styles.sectionText}>
                            No additional recommendations were returned.
                        </p>
                    )}
                </div>
            ) : null}
        </section>
    );
}
