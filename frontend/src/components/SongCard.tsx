import { useEffect, useId, useRef, useState } from 'react';
import type { Song } from '../types';
import styles from './SongCard.module.css';
import { InfoIcon } from 'lucide-react';
import { createPortal } from 'react-dom';

const TOOLTIP_WIDTH = 320;
const TOOLTIP_MARGIN = 16;
const TOOLTIP_OFFSET = 10;

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
    selected?: boolean;
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
    selected = false,
    onSelect,
}: SongCardProps) {
    const tooltipId = useId();
    const buttonRef = useRef<HTMLButtonElement | null>(null);
    const tooltipRef = useRef<HTMLDivElement | null>(null);
    const [isTooltipOpen, setIsTooltipOpen] = useState(false);
    const [tooltipPosition, setTooltipPosition] = useState({ top: 0, left: 0 });
    const scoreReasons = parseReasons(mathExplanation);
    const retrievalReasons = matchedSources.flatMap((source) =>
        (sourceReasons[source as keyof typeof sourceReasons] || []).map((reason) => ({
            key: `${source}-${reason}`,
            label: `${formatSourceLabel(source)}: ${reason}`,
        })),
    );
    const metadataItems = [
        song.genre,
        song.mood,
        song.listening_context,
        `${song.tempo_bpm} BPM`,
        `metadata ${retrievalBreakdown.metadata.toFixed(2)}`,
        `lyrics ${retrievalBreakdown.lyrics.toFixed(2)}`,
        ...matchedSources.map((source) => `matched via ${formatSourceLabel(source)}`),
        ...retrievalReasons.map((reason) => reason.label),
        ...scoreReasons,
    ].filter((item): item is string => Boolean(item));
    const isSelectable = song.audio_url !== null;

    useEffect(() => {
        if (!isTooltipOpen) {
            return;
        }

        function updateTooltipPosition() {
            if (!buttonRef.current) {
                return;
            }

            const buttonRect = buttonRef.current.getBoundingClientRect();
            const tooltipWidth = Math.min(TOOLTIP_WIDTH, window.innerWidth - TOOLTIP_MARGIN * 2);
            const tooltipHeight = tooltipRef.current?.offsetHeight ?? 220;
            const nextLeft = Math.min(
                Math.max(TOOLTIP_MARGIN, buttonRect.right - tooltipWidth),
                window.innerWidth - tooltipWidth - TOOLTIP_MARGIN,
            );
            const spaceBelow = window.innerHeight - buttonRect.bottom;
            const spaceAbove = buttonRect.top;
            const shouldOpenAbove =
                spaceBelow < tooltipHeight + TOOLTIP_OFFSET + TOOLTIP_MARGIN &&
                spaceAbove > spaceBelow;

            const preferredTop = shouldOpenAbove
                ? buttonRect.top - tooltipHeight - TOOLTIP_OFFSET
                : buttonRect.bottom + TOOLTIP_OFFSET;
            const maxTop = window.innerHeight - tooltipHeight - TOOLTIP_MARGIN;
            const nextTop = Math.min(
                Math.max(TOOLTIP_MARGIN, preferredTop),
                Math.max(TOOLTIP_MARGIN, maxTop),
            );

            setTooltipPosition({ top: nextTop, left: nextLeft });
        }

        updateTooltipPosition();
        window.addEventListener('scroll', updateTooltipPosition, true);
        window.addEventListener('resize', updateTooltipPosition);

        return () => {
            window.removeEventListener('scroll', updateTooltipPosition, true);
            window.removeEventListener('resize', updateTooltipPosition);
        };
    }, [isTooltipOpen]);

    function handleSelect() {
        onSelect?.(song);
    }

    return (
        <article
            className={`${styles.songCard} ${selected ? styles.selected : ''} ${isSelectable ? styles.songCardSelectable : ''}`}
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
            tabIndex={isSelectable ? 0 : undefined}>
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
                    <div className={styles.headerMeta}>
                        <div className={styles.scoreBlock}>
                            <strong>{formatPercent(score)}</strong>
                            <span>retrieval {retrievalScore.toFixed(2)}</span>
                        </div>
                        <div className={styles.metaTooltipGroup}>
                            <button
                                ref={buttonRef}
                                type="button"
                                className={styles.metaButton}
                                aria-label={`Show metadata for ${song.title}`}
                                aria-describedby={isTooltipOpen ? tooltipId : undefined}
                                onClick={(event) => event.stopPropagation()}
                                onMouseEnter={() => setIsTooltipOpen(true)}
                                onMouseLeave={() => setIsTooltipOpen(false)}
                                onFocus={() => setIsTooltipOpen(true)}
                                onBlur={() => setIsTooltipOpen(false)}>
                                <InfoIcon size={16} />
                            </button>
                        </div>
                    </div>
                </div>

                <p className={styles.explanation}>{llmExplanation}</p>
            </div>
            {isTooltipOpen
                ? createPortal(
                      <div
                          id={tooltipId}
                          ref={tooltipRef}
                          className={styles.metaTooltipPortal}
                          style={{
                              top: `${tooltipPosition.top}px`,
                              left: `${tooltipPosition.left}px`,
                              width: `${Math.min(TOOLTIP_WIDTH, typeof window === 'undefined' ? TOOLTIP_WIDTH : window.innerWidth - TOOLTIP_MARGIN * 2)}px`,
                          }}
                          role="tooltip">
                          <p className={styles.metaTooltipTitle}>Track details</p>
                          <ul className={styles.metaTooltipList}>
                              {metadataItems.map((item) => (
                                  <li key={`${song.id}-${item}`}>{item}</li>
                              ))}
                          </ul>
                      </div>,
                      document.body,
                  )
                : null}
        </article>
    );
}
