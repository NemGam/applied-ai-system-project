import {
    createContext,
    type PropsWithChildren,
    useContext,
    useEffect,
    useMemo,
    useState,
} from 'react';

export type Preferences = {
    userText: string;
    useTasteProfile: boolean;
    genre: string;
    mood: string;
    listeningContext: string;
    preferredMoodTags: string;
    energy: string;
    tempoBpm: string;
    danceability: string;
    acousticness: string;
    vocalPresence: string;
    valence: string;
    k: string;
};

export const initialPreferences: Preferences = {
    userText: 'I want chill music for late-night studying with soft vocals',
    useTasteProfile: true,
    genre: '',
    mood: 'chill',
    listeningContext: 'study',
    preferredMoodTags: 'focused, nocturnal',
    energy: '0.30',
    tempoBpm: '82',
    danceability: '0.35',
    acousticness: '0.80',
    vocalPresence: '0.35',
    valence: '0.55',
    k: '5',
};

const STORAGE_KEY = 'vibeflow.preferences.v1';

type PreferencesContextValue = {
    preferences: Preferences;
    updatePreference: <K extends keyof Preferences>(field: K, value: Preferences[K]) => void;
    resetPreferences: () => void;
};

const PreferencesContext = createContext<PreferencesContextValue | undefined>(undefined);

function loadStoredPreferences(): Preferences {
    try {
        const raw = window.localStorage.getItem(STORAGE_KEY);
        if (!raw) {
            return initialPreferences;
        }

        const parsed = JSON.parse(raw) as Partial<Preferences>;
        return {
            ...initialPreferences,
            ...parsed,
        };
    } catch {
        return initialPreferences;
    }
}

export function PreferencesProvider({ children }: PropsWithChildren) {
    const [preferences, setPreferences] = useState<Preferences>(() => loadStoredPreferences());

    useEffect(() => {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
    }, [preferences]);

    const value = useMemo<PreferencesContextValue>(
        () => ({
            preferences,
            updatePreference(field, value) {
                setPreferences((current) => ({
                    ...current,
                    [field]: value,
                }));
            },
            resetPreferences() {
                setPreferences(initialPreferences);
            },
        }),
        [preferences],
    );

    return <PreferencesContext.Provider value={value}>{children}</PreferencesContext.Provider>;
}

export function usePreferencesContext() {
    const context = useContext(PreferencesContext);
    if (!context) {
        throw new Error('usePreferencesContext must be used within PreferencesProvider');
    }
    return context;
}
