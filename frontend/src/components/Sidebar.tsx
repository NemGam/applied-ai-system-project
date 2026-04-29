import { NavLink } from 'react-router-dom';
import styles from './Sidebar.module.css';

type SidebarTab = {
    to: string;
    label: string;
    description: string;
    icon: string;
};

type SidebarProps = {
    tabs: readonly SidebarTab[];
};

export default function Sidebar({ tabs }: SidebarProps) {
    return (
        <aside className={styles.sidebar}>
            <div className={styles.brand}>
                <p>VibeFlow</p>
                <span>Music recommender</span>
            </div>
            <hr></hr>

            <nav className={styles.nav} aria-label="Primary">
                {tabs.map((tab) => (
                    <NavLink
                        key={tab.to}
                        to={tab.to}
                        end={tab.to === '/'}
                        className={({ isActive }) =>
                            `${styles.tab} ${isActive ? `${styles.tabActive}` : ''}`
                        }>
                        <span className={styles.tabIcon} aria-hidden="true">
                            {tab.icon}
                        </span>
                        <span className={styles.tabCopy}>
                            <strong>{tab.label}</strong>
                            <small>{tab.description}</small>
                        </span>
                    </NavLink>
                ))}
            </nav>
        </aside>
    );
}
