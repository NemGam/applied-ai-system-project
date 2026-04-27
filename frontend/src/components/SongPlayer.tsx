import { useEffect, useRef, useState } from 'react';
import styles from './SongPlayer.module.css';
import type { Song } from '../types';

type SongPlayerProps = {
    song: Song;
};

export default function SongPlayer({ song }: SongPlayerProps) {
    const audioRef = useRef<HTMLAudioElement | null>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [lyrics, setLyrics] = useState<string | null>(null);
    const [isLyricsLoading, setIsLyricsLoading] = useState(false);
    const [lyricsError, setLyricsError] = useState('');

    useEffect(() => {
        setIsPlaying(false);
        setCurrentTime(0);
        setDuration(0);
    }, [song.id, song.audio_url]);

    useEffect(() => {
        if (!song.has_lyrics || !song.lyrics_url) {
            setLyrics(null);
            setLyricsError('');
            setIsLyricsLoading(false);
            return;
        }

        const abortController = new AbortController();

        async function loadLyrics() {
            setIsLyricsLoading(true);
            setLyrics(null);
            setLyricsError('');

            try {
                const response = await fetch(song.lyrics_url as string, {
                    signal: abortController.signal,
                });

                if (!response.ok) {
                    throw new Error(`Lyrics request failed with status ${response.status}`);
                }

                const payload = (await response.json()) as { lyrics?: string };
                const nextLyrics = payload.lyrics?.trim() ?? '';
                if (!nextLyrics) {
                    setLyricsError('Lyrics are unavailable right now.');
                    setLyrics(null);
                    return;
                }

                setLyrics(nextLyrics);
            } catch (error) {
                if (abortController.signal.aborted) {
                    return;
                }

                setLyrics(null);
                setLyricsError(
                    error instanceof Error ? error.message : 'Lyrics are unavailable right now.',
                );
            } finally {
                if (!abortController.signal.aborted) {
                    setIsLyricsLoading(false);
                }
            }
        }

        void loadLyrics();

        return () => {
            abortController.abort();
        };
    }, [song.has_lyrics, song.id, song.lyrics_url]);

    async function togglePlayback() {
        if (!song.audio_url) {
            return;
        }

        if (!audioRef.current) {
            return;
        }

        if (isPlaying) {
            audioRef.current.pause();
            setIsPlaying(false);
            return;
        }

        try {
            await audioRef.current.play();
            setIsPlaying(true);
        } catch {
            setIsPlaying(false);
        }
    }

    function seekTo(value: number) {
        if (!audioRef.current) {
            return;
        }

        audioRef.current.currentTime = value;
        setCurrentTime(value);
    }

    function skipBy(seconds: number) {
        if (!audioRef.current) {
            return;
        }

        const nextTime = Math.min(
            Math.max(audioRef.current.currentTime + seconds, 0),
            duration || 0,
        );
        seekTo(nextTime);
    }

    function formatTime(seconds: number): string {
        if (!Number.isFinite(seconds) || seconds < 0) {
            return '0:00';
        }

        const totalSeconds = Math.floor(seconds);
        const mins = Math.floor(totalSeconds / 60);
        const secs = String(totalSeconds % 60).padStart(2, '0');
        return `${mins}:${secs}`;
    }

    return (
        <section className={`panel ${styles.songPlayerPanel}`}>
            {song.cover_url ? (
                <img
                    className={styles.songCover}
                    src={song.cover_url}
                    alt={`${song.title} cover`}
                />
            ) : (
                <div className={`${styles.songCover} ${styles.coverPlaceholder}`}>No cover</div>
            )}
            <div>
                <h3 className={styles.title}>{song.title}</h3>
                <p className={styles.artist}>{song.artist}</p>
            </div>

            <div className={styles.timelineWrap}>
                <input
                    type="range"
                    className={styles.timeline}
                    min={0}
                    max={duration || 0}
                    step={0.1}
                    value={currentTime}
                    onChange={(event) => seekTo(Number(event.target.value))}
                    disabled={!song.audio_url || duration <= 0}
                />
                <div className={styles.timeLabels}>
                    <span>{formatTime(currentTime)}</span>
                    <span>{formatTime(duration)}</span>
                </div>
            </div>

            <div className={styles.controls}>
                <button
                    type="button"
                    className={styles.skipButton}
                    onClick={() => skipBy(-5)}
                    disabled={!song.audio_url}>
                    -5s
                </button>
                <button
                    type="button"
                    className={styles.playButton}
                    onClick={togglePlayback}
                    disabled={!song.audio_url}>
                    {song.audio_url ? (isPlaying ? 'Pause' : 'Play') : 'No audio'}
                </button>
                <button
                    type="button"
                    className={styles.skipButton}
                    onClick={() => skipBy(5)}
                    disabled={!song.audio_url}>
                    +5s
                </button>
            </div>

            {song.has_lyrics ? (
                <section className={styles.lyricsSection} aria-live="polite">
                    <h4 className={styles.lyricsHeading}>Lyrics</h4>
                    {isLyricsLoading ? (
                        <p className={styles.lyricsStatus}>Loading lyrics...</p>
                    ) : lyricsError ? (
                        <p className={styles.lyricsStatus}>{lyricsError}</p>
                    ) : lyrics ? (
                        <pre className={styles.lyricsText}>{lyrics}</pre>
                    ) : null}
                </section>
            ) : null}

            {song.audio_url ? (
                <audio
                    ref={audioRef}
                    src={song.audio_url}
                    onEnded={() => setIsPlaying(false)}
                    onPause={() => setIsPlaying(false)}
                    onPlay={() => setIsPlaying(true)}
                    onTimeUpdate={(event) => setCurrentTime(event.currentTarget.currentTime)}
                    onLoadedMetadata={(event) => {
                        const loadedDuration = event.currentTarget.duration;
                        setDuration(Number.isFinite(loadedDuration) ? loadedDuration : 0);
                    }}
                    hidden
                />
            ) : null}
        </section>
    );
}
