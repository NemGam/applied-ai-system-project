const GENRE_ICON_BY_KEY: Record<string, string> = {
    ambient: '🌌',
    electronic: '🎛️',
    'hip hop': '🎤',
    'indie pop': '✨',
    jazz: '🎷',
    lofi: '📼',
    pop: '🎉',
    rock: '🎸',
    synthwave: '🌃',
};

const MOOD_ICON_BY_KEY: Record<string, string> = {
    chill: '🧊',
    energetic: '⚡',
    focused: '🎯',
    happy: '😄',
    intense: '🔥',
    moody: '🌙',
    relaxed: '🛋️',
};

function normalizeLabel(value: string): string {
    return value.trim().toLowerCase();
}

export function getGenreIcon(genre: string): string {
    return GENRE_ICON_BY_KEY[normalizeLabel(genre)] ?? '🎵';
}

export function formatGenreWithIcon(genre: string): string {
    return `${getGenreIcon(genre)} ${genre}`;
}

export function getMoodIcon(mood: string): string {
    return MOOD_ICON_BY_KEY[normalizeLabel(mood)] ?? '🎵';
}

export function formatMoodWithIcon(mood: string): string {
    return `${getMoodIcon(mood)} ${mood}`;
}
