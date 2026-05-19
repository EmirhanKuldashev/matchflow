import { useEffect, useState } from 'react';
import { Link, useRouter } from '../components/Router';
import { Alert, FormField, Loading, PageHeader, RoleBadge } from '../components/ui';
import { useAuth } from '../context/AuthContext';
import { getErrorText, getRoleLabel } from '../utils/format';

export function RequireAuth({ children }) {
  const { isAuthenticated, loading } = useAuth();
  const { navigate } = useRouter();

  useEffect(() => {
    if (!loading && !isAuthenticated) navigate('/login');
  }, [loading, isAuthenticated, navigate]);

  if (loading) return <Loading text="Проверяем авторизацию…" />;
  if (!isAuthenticated) return null;
  return children;
}

export function ProfilePage() {
  const { user, role } = useAuth();

  return (
    <RequireAuth>
      <section className="section">
        <PageHeader
          eyebrow="Личный кабинет"
          title={`${user?.first_name || user?.username || 'Пользователь'} ${user?.last_name || ''}`.trim()}
          text="Здесь собраны данные аккаунта и быстрые переходы к действиям по вашей роли."
          actions={<Link to="/profile/edit" className="button button--primary">Редактировать профиль</Link>}
        />

        <div className="profile-grid">
          <article className="panel">
            <h2>Профиль</h2>
            <dl className="details-list">
              <div><dt>Username</dt><dd>{user?.username || '—'}</dd></div>
              <div><dt>Email</dt><dd>{user?.email || '—'}</dd></div>
              <div><dt>Роль</dt><dd><RoleBadge label={getRoleLabel(role)} role={role} /></dd></div>
              <div><dt>Телефон</dt><dd>{user?.phone || user?.profile?.phone || '—'}</dd></div>
              <div><dt>Город</dt><dd>{user?.city || user?.profile?.city || '—'}</dd></div>
            </dl>
          </article>

          <article className="panel">
            <h2>Действия</h2>
            <div className="quick-actions">
              <Link to="/my-tournaments" className="button button--secondary">Мои турниры</Link>
              {role === 'player' && <Link to="/teams" className="button button--secondary">Подать заявку в команду</Link>}
              {role === 'captain' && <Link to="/teams/create" className="button button--secondary">Создать команду</Link>}
              {role === 'captain' && <Link to="/captain/join-requests" className="button button--secondary">Заявки игроков</Link>}
              {role === 'organizer' && <Link to="/organizer/verification" className="button button--secondary">Подтвердить организатора</Link>}
              {role === 'organizer' && <Link to="/tournaments/create" className="button button--secondary">Создать турнир</Link>}
              {role === 'organizer' && <Link to="/organizer/tournament-applications" className="button button--secondary">Заявки команд</Link>}
              {role === 'organizer' && <Link to="/matches/create" className="button button--secondary">Создать матч</Link>}
            </div>
          </article>
        </div>
      </section>
    </RequireAuth>
  );
}

export function ProfileEditPage() {
  const { user, updateProfile } = useAuth();
  const { navigate } = useRouter();
  const [form, setForm] = useState({ first_name: '', last_name: '', phone: '', city: '' });
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setForm({
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
      phone: user?.phone || user?.profile?.phone || '',
      city: user?.city || user?.profile?.city || '',
    });
  }, [user]);

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);
    try {
      await updateProfile(form);
      setMessage('Профиль обновлён.');
      setTimeout(() => navigate('/profile'), 700);
    } catch (err) {
      setError(getErrorText(err));
    } finally {
      setLoading(false);
    }
  }

  function update(key, value) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  return (
    <RequireAuth>
      <section className="auth-page">
        <PageHeader eyebrow="Профиль" title="Редактирование профиля" text="Frontend отправляет PATCH на `/api/profile/update/`." />
        <form className="form-card form-card--wide" onSubmit={handleSubmit}>
          <Alert type="success">{message}</Alert>
          <Alert type="error">{error}</Alert>
          <div className="form-grid">
            <FormField label="Имя"><input value={form.first_name} onChange={(e) => update('first_name', e.target.value)} /></FormField>
            <FormField label="Фамилия"><input value={form.last_name} onChange={(e) => update('last_name', e.target.value)} /></FormField>
            <FormField label="Телефон"><input value={form.phone} onChange={(e) => update('phone', e.target.value)} /></FormField>
            <FormField label="Город"><input value={form.city} onChange={(e) => update('city', e.target.value)} /></FormField>
          </div>
          <button className="button button--primary" type="submit" disabled={loading}>{loading ? 'Сохраняем…' : 'Сохранить'}</button>
        </form>
      </section>
    </RequireAuth>
  );
}
