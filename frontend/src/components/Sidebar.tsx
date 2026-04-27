import { NavLink } from 'react-router-dom';
import styles from './Sidebar.module.css';

export default function Sidebar({ tabs }) {
    return (
        <aside className={styles.sidebar}>
            <div className={styles.brand}>
                <p>VibeFlow</p>
                <span>Music recommender</span>
            </div>

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
