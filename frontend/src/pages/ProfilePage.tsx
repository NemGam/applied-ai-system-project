import ProfilePreferencesPanel from '../components/ProfilePreferencesPanel';
import type { Preferences } from '../utils/preferencesContext';

type ProfilePageProps = {
    hero?: {
        to: string;
        label: string;
        eyebrow: string;
        title: string;
        description: string;
        icon: string;
    };
    preferences: Preferences;
    profileHighlights: Array<{ label: string; value: string }>;
    profileMetrics: Array<{ label: string; value: string }>;
    onPreferenceChange: <K extends keyof Preferences>(field: K, value: Preferences[K]) => void;
    onReset?: () => void;
};

export default function ProfilePage({
    preferences,
    onPreferenceChange,
}: ProfilePageProps) {
    return (
        <>
            <div className="profile-layout">
                <ProfilePreferencesPanel
                    preferences={preferences}
                    onPreferenceChange={onPreferenceChange}
                />
            </div>
        </>
    );
}
