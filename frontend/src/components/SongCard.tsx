import type { Song } from '../types';
import styles from './SongCard.module.css';

type SongCardProps = {
    song: Song;
    score: number;
    retrievalScore: number;
    retrievalBreakdown: {
        metadata: number;
        lyrics: number;
    };
    matchedSources: string[];
    sourceReasons: {
        metadata: string[];
        lyrics: string[];
    };
    llmExplanation: string;
    mathExplanation: string;
    onSelect?: (song: Song) => void;
};

function parseReasons(explanation: string): string[] {
    return explanation
        .split(';')
        .map((part) => part.trim())
        .filter(Boolean);
}

function formatPercent(score: number): string {
    return `${Math.round(score * 100)}%`;
}

function formatSourceLabel(source: string): string {
    return source === 'lyrics' ? 'lyrics' : 'metadata';
}

export default function SongCard({
    song,
    score,
    retrievalScore,
    retrievalBreakdown,
    matchedSources,
    sourceReasons,
    llmExplanation,
    mathExplanation,
    onSelect,
}: SongCardProps) {
    const scoreReasons = parseReasons(mathExplanation);
    const retrievalReasons = matchedSources.flatMap((source) =>
        (sourceReasons[source as keyof typeof sourceReasons] || []).map((reason) => ({
            key: `${source}-${reason}`,
            label: `${formatSourceLabel(source)}: ${reason}`,
        })),
    );
    const isSelectable = typeof onSelect === 'function';

    function handleSelect() {
        onSelect?.(song);
    }

    return (
        <article
            className={`${styles.songCard} ${isSelectable ? styles.songCardSelectable : ''}`}
            onClick={isSelectable ? handleSelect : undefined}
            onKeyDown={
                isSelectable
                    ? (event) => {
                          if (event.key === 'Enter' || event.key === ' ') {
                              event.preventDefault();
                              handleSelect();
                          }
                      }
                    : undefined
            }
            role={isSelectable ? 'button' : undefined}
            tabIndex={isSelectable ? 0 : undefined}
        >
            {song.cover_url ? (
                <img
                    className={styles.songCover}
                    src={song.cover_url}
                    alt={`${song.title} cover`}
                />
            ) : (
                <div className={`${styles.songCover} ${styles.songCoverPlaceholder}`}>No cover</div>
            )}

            <div className={styles.songBody}>
                <div className={styles.songHeader}>
                    <div>
                        <h3>{song.title}</h3>
                        <p className={styles.artist}>{song.artist}</p>
                    </div>
                    <div className={styles.scoreBlock}>
                        <strong>{formatPercent(score)}</strong>
                        <span>retrieval {retrievalScore.toFixed(2)}</span>
                    </div>
                </div>

                <div className={styles.songFacts}>
                    <span>{song.genre}</span>
                    <span>{song.mood}</span>
                    {song.listening_context ? <span>{song.listening_context}</span> : null}
                    <span>{song.tempo_bpm} BPM</span>
                </div>

                <p className={styles.explanation}>{llmExplanation}</p>

                <div className={styles.sourceSummary}>
                    <span>metadata {retrievalBreakdown.metadata.toFixed(2)}</span>
                    <span>lyrics {retrievalBreakdown.lyrics.toFixed(2)}</span>
                    {matchedSources.map((source) => (
                        <span key={`${song.id}-${source}`} className={styles.sourcePill}>
                            matched via {formatSourceLabel(source)}
                        </span>
                    ))}
                </div>

                {retrievalReasons.length ? (
                    <div className={styles.reasonList}>
                        {retrievalReasons.map((reason) => (
                            <span key={`${song.id}-${reason.key}`} className={styles.sourceReasonPill}>
                                {reason.label}
                            </span>
                        ))}
                    </div>
                ) : null}

                <div className={styles.reasonList}>
                    {scoreReasons.map((reason) => (
                        <span key={`${song.id}-${reason}`} className={styles.reasonPill}>
                            {reason}
                        </span>
                    ))}
                </div>
            </div>
        </article>
    );
}
