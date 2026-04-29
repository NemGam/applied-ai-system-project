import { useEffect, useRef, useState } from 'react';
import styles from './SongPlayer.module.css';
import type { Song } from '../types';
import { Volume1Icon, Volume2Icon, VolumeOffIcon } from 'lucide-react';

const END_FADE_SECONDS = 4;

type SongPlayerProps = {
    song: Song | null;
};

export default function SongPlayer({ song }: SongPlayerProps) {
    const audioRef = useRef<HTMLAudioElement | null>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [volume, setVolume] = useState(0.7);
    const [lyrics, setLyrics] = useState<string | null>(null);
    const [isLyricsLoading, setIsLyricsLoading] = useState(false);
    const [lyricsError, setLyricsError] = useState('');

    useEffect(() => {
        if (!song) {
            setIsPlaying(false);
            setCurrentTime(0);
            setDuration(0);
            return;
        }

        setIsPlaying(false);
        setCurrentTime(0);
        setDuration(0);
    }, [song]);

    useEffect(() => {
        if (!audioRef.current) {
            return;
        }

        syncAudioVolume(audioRef.current, volume);
    }, [duration, volume, song]);

    useEffect(() => {
        if (!song) {
            setLyrics(null);
            setLyricsError('');
            setIsLyricsLoading(false);
            return;
        }

        if (!song.has_lyrics || !song.lyrics_url) {
            setLyrics(null);
            setLyricsError('');
            setIsLyricsLoading(false);
            return;
        }

        const lyricsUrl: string = song.lyrics_url;

        const abortController = new AbortController();

        async function loadLyrics() {
            setIsLyricsLoading(true);
            setLyrics(null);
            setLyricsError('');

            try {
                const response = await fetch(lyricsUrl, {
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
    }, [song]);

    async function togglePlayback() {
        if (!song) {
            return;
        }

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

    function formatVolume(value: number): string {
        return `${Math.round(value * 100)}%`;
    }

    function getEffectiveVolume(
        baseVolume: number,
        playbackCurrentTime: number,
        playbackDuration: number,
    ): number {
        if (
            !Number.isFinite(playbackCurrentTime) ||
            !Number.isFinite(playbackDuration) ||
            playbackDuration <= END_FADE_SECONDS
        ) {
            return baseVolume;
        }

        const remainingSeconds = playbackDuration - playbackCurrentTime;
        if (remainingSeconds >= END_FADE_SECONDS) {
            return baseVolume;
        }

        return Math.max(0, baseVolume * (remainingSeconds / END_FADE_SECONDS));
    }

    function syncAudioVolume(
        audioElement: HTMLAudioElement,
        baseVolume: number,
        playbackCurrentTime = audioElement.currentTime,
        playbackDuration = audioElement.duration,
    ) {
        audioElement.volume = getEffectiveVolume(baseVolume, playbackCurrentTime, playbackDuration);
    }

    if (!song) {
        return (
            <aside className={styles.songPlayerPanel}>
                <div className={`${styles.songCover} ${styles.coverPlaceholder}`}>Pick a song</div>
                <div>
                    <h3 className={styles.title}>Player queue</h3>
                    <p className={styles.artist}>
                        Select a recommendation to load its preview, artwork, and lyrics here.
                    </p>
                </div>
            </aside>
        );
    }

    return (
        <aside className={styles.songPlayerPanel}>
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

            <label className={styles.volumeControl}>
                <div className={styles.volumeRow}>
                    <span className={styles.volumeLabel}>
                        {volume == 0 ? (
                            <VolumeOffIcon />
                        ) : volume < 0.35 ? (
                            <Volume1Icon />
                        ) : (
                            <Volume2Icon />
                        )}
                    </span>
                    <input
                        type="range"
                        className={styles.volumeSlider}
                        min={0}
                        max={1}
                        step={0.01}
                        value={volume}
                        onChange={(event) => setVolume(Number(event.target.value))}
                        disabled={!song.audio_url}
                    />
                    <span className={styles.volumeValue}>{formatVolume(volume)}</span>
                </div>
            </label>

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
                    onTimeUpdate={(event) => {
                        const playbackCurrentTime = event.currentTarget.currentTime;
                        setCurrentTime(playbackCurrentTime);
                        syncAudioVolume(
                            event.currentTarget,
                            volume,
                            playbackCurrentTime,
                            event.currentTarget.duration,
                        );
                    }}
                    onLoadedMetadata={(event) => {
                        const loadedDuration = event.currentTarget.duration;
                        setDuration(Number.isFinite(loadedDuration) ? loadedDuration : 0);
                        syncAudioVolume(
                            event.currentTarget,
                            volume,
                            event.currentTarget.currentTime,
                            loadedDuration,
                        );
                    }}
                    hidden
                />
            ) : null}
        </aside>
    );
}
