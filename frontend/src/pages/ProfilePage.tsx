import ProfilePreferencesPanel from '../components/ProfilePreferencesPanel';
import type { Preferences } from '../utils/preferencesContext';

type ProfilePageProps = {
    preferences: Preferences;
    onPreferenceChange: <K extends keyof Preferences>(field: K, value: Preferences[K]) => void;
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
