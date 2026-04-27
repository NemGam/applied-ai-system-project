export type Song = {
    id: number;
    title: string;
    artist: string;
    genre: string;
    mood: string;
    energy: number;
    tempo_bpm: number;
    valence: number;
    danceability: number;
    acousticness: number;
    vocal_presence?: number;
    instrumental_focus?: number;
    listening_context?: string;
    detailed_mood_tags?: string;
    cover_url: string | null;
    audio_url: string | null;
    has_lyrics: boolean;
    lyrics_url: string | null;
};

export type RequestInputMode = 'natural_language' | 'manual';

export type ManualPreferencesPayload = {
    genre?: string;
    mood?: string;
    energy?: number;
    tempo_bpm?: number;
    danceability?: number;
    acousticness?: number;
    vocal_presence?: number;
    valence?: number;
    listening_context?: string;
    preferred_mood_tags: string[];
};

export type AIRecommendationRequestPayload = {
    user_text: string | null;
    manual_preferences: ManualPreferencesPayload | null;
    taste_profile: ManualPreferencesPayload | null;
    k: number;
    retrieval_k: number;
};

export type DetectedPreferences = {
    genres?: string[];
    moods?: string[];
    contexts?: string[];
    mood_tags?: string[];
    energy?: number;
    danceability?: number;
    acousticness?: number;
    vocal_presence?: number;
    instrumental_focus?: number;
    valence?: number;
    tempo_bpm?: number;
};

export type RecommendationResult = {
    song: Song;
    score: number;
    retrieval_score: number;
    lyric_snippets: string[];
    retrieval_breakdown: {
        metadata: number;
        lyrics: number;
    };
    matched_sources: string[];
    source_reasons: {
        metadata: string[];
        lyrics: string[];
    };
    math_explanation: string;
    llm_explanation: string;
};

export type AIRecommendationResponse = {
    input_mode: 'manual' | 'natural_language' | 'hybrid';
    user_request: string;
    detected_preferences: DetectedPreferences;
    personalization: {
        enabled: boolean;
        source: string | null;
        taste_profile: DetectedPreferences;
    };
    providers: {
        parser: string;
        ranking: string;
        explanations: string;
    };
    retrieval: {
        strategy: string;
        candidate_count: number;
        source_counts: {
            metadata: number;
            lyrics: number;
            both: number;
        };
        candidates: Array<{
            song_id: number;
            title: string;
            artist: string;
            genre: string;
            mood: string;
            listening_context: string;
            retrieval_score: number;
        retrieval_breakdown: {
            metadata: number;
            lyrics: number;
        };
        lyric_snippets: string[];
        matched_sources: string[];
        source_reasons: {
            metadata: string[];
            lyrics: string[];
        };
        }>;
    };
    guardrail?: {
        triggered: boolean;
        category: string;
        message: string;
    };
    overall_explanation: string;
    results: RecommendationResult[];
};
