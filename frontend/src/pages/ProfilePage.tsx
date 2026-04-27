import ProfilePreferencesPanel from '../components/ProfilePreferencesPanel';
import type { Preferences } from '../utils/preferencesContext';

type ProfilePageProps = {
    hero: {
        eyebrow: string;
        title: string;
        description: string;
    };
    preferences: Preferences;
    profileHighlights: Array<{ label: string; value: string }>;
    profileMetrics: Array<{ label: string; value: string }>;
    onPreferenceChange: <K extends keyof Preferences>(field: K, value: Preferences[K]) => void;
    onReset: () => void;
};

export default function ProfilePage({
    preferences,
    onPreferenceChange,
    onReset,
}: ProfilePageProps) {
    return (
        <>
            <div className="profile-layout">
                <ProfilePreferencesPanel
                    preferences={preferences}
                    onPreferenceChange={onPreferenceChange}
                    onReset={onReset}
                />
            </div>
        </>
    );
}
