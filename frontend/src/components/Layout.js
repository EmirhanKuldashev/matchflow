import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { getRoleLabel } from '../utils/format';
import { getCookie, setCookie } from '../utils/cookies';
import { Link, useRouter } from './Router';
import { RoleBadge } from './ui';

const navItems = [
  { to: '/', label: 'Главная' },
  { to: '/teams', label: 'Команды' },
  { to: '/tournaments', label: 'Турниры' },
  { to: '/matches', label: 'Матчи' },
];

export function Layout({ children }) {
  const { isAuthenticated, user, role, logout } = useAuth();
  const { path, navigate } = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);
  const [theme, setTheme] = useState(() => getCookie('matchflow_theme') || 'light');

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    setCookie('matchflow_theme', theme);
  }, [theme]);

  function handleLogout() {
    logout();
    navigate('/login');
  }

  return (
    <div className="app-shell">
      <header className="site-header">
        <div className="site-header__inner">
          <Link to="/" className="brand" onClick={() => setMenuOpen(false)}>
            <span className="brand__mark">⚽</span>
            <span>
              <strong>MatchFlow</strong>
              <small>любительский футбол</small>
            </span>
          </Link>

          <button className="menu-button" type="button" onClick={() => setMenuOpen((value) => !value)}>
            ☰
          </button>

          <nav className={`nav ${menuOpen ? 'nav--open' : ''}`}>
            {navItems.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className={path === item.to ? 'nav__link nav__link--active' : 'nav__link'}
                onClick={() => setMenuOpen(false)}
              >
                {item.label}
              </Link>
            ))}

            {isAuthenticated && (
              <>
                <Link to="/my-tournaments" className="nav__link" onClick={() => setMenuOpen(false)}>
                  Мои турниры
                </Link>
                <Link to="/profile" className="nav__link" onClick={() => setMenuOpen(false)}>
                  Кабинет
                </Link>
              </>
            )}
          </nav>

          <div className="header-actions">
            <button
              type="button"
              className="theme-toggle"
              onClick={() => setTheme((value) => (value === 'dark' ? 'light' : 'dark'))}
              title="Переключить тему"
            >
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>

            {isAuthenticated ? (
              <div className="user-pill">
                <RoleBadge role={role} label={getRoleLabel(role)} />
                <span>{user?.first_name || user?.username || user?.email}</span>
                <button type="button" onClick={handleLogout}>Выйти</button>
              </div>
            ) : (
              <div className="auth-links">
                <Link to="/login" className="button button--ghost">Вход</Link>
                <Link to="/register" className="button button--primary">Регистрация</Link>
              </div>
            )}
          </div>
        </div>
      </header>

      <main>{children}</main>

      <footer className="site-footer">
        <div>
          <strong>MatchFlow</strong>
          <p>Frontend React-клиент для Django REST API: команды, турниры, заявки, матчи и подписки.</p>
        </div>
        <span>Курсовой проект · 2026</span>
      </footer>
    </div>
  );
}
