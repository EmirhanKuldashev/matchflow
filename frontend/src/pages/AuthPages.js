import { useState } from 'react';
import { Link, useRouter } from '../components/Router';
import { Alert, FormField, PageHeader } from '../components/ui';
import { useAuth } from '../context/AuthContext';
import { getErrorText } from '../utils/format';

const roleOptions = [
  { value: 'user', label: 'Пользователь' },
  { value: 'player', label: 'Игрок команды' },
  { value: 'captain', label: 'Капитан команды' },
  { value: 'organizer', label: 'Организатор турниров' },
];

export function LoginPage() {
  const { login } = useAuth();
  const { navigate } = useRouter();
  const [form, setForm] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(form);
      navigate('/profile');
    } catch (err) {
      setError(getErrorText(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="auth-page">
      <PageHeader eyebrow="Вход" title="Вернитесь в MatchFlow" text="Войдите по email и паролю, backend вернёт DRF token для дальнейших запросов." />
      <form className="form-card" onSubmit={handleSubmit}>
        <Alert type="error">{error}</Alert>
        <FormField label="Email">
          <input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        </FormField>
        <FormField label="Пароль">
          <input type="password" required value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
        </FormField>
        <button className="button button--primary" type="submit" disabled={loading}>{loading ? 'Входим…' : 'Войти'}</button>
        <p className="form-note">Нет аккаунта? <Link to="/register">Зарегистрироваться</Link></p>
      </form>
    </section>
  );
}

export function RegisterPage() {
  const { register } = useAuth();
  const { navigate } = useRouter();
  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    password2: '',
    first_name: '',
    last_name: '',
    role: 'user',
  });
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setMessage('');

    if (form.password !== form.password2) {
      setError('Пароли не совпадают.');
      return;
    }

    setLoading(true);
    try {
      await register(form);
      setMessage('Аккаунт создан. Теперь можно войти в систему. Если backend включит email-подтверждение, проверьте почту.');
      setTimeout(() => navigate('/login'), 900);
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
    <section className="auth-page">
      <PageHeader eyebrow="Регистрация" title="Создайте аккаунт и выберите роль" text="Роль сохраняется в профиле и определяет доступные действия во frontend и backend." />
      <form className="form-card form-card--wide" onSubmit={handleSubmit}>
        <Alert type="success">{message}</Alert>
        <Alert type="error">{error}</Alert>
        <div className="form-grid">
          <FormField label="Username"><input required value={form.username} onChange={(e) => update('username', e.target.value)} /></FormField>
          <FormField label="Email"><input type="email" required value={form.email} onChange={(e) => update('email', e.target.value)} /></FormField>
          <FormField label="Имя"><input value={form.first_name} onChange={(e) => update('first_name', e.target.value)} /></FormField>
          <FormField label="Фамилия"><input value={form.last_name} onChange={(e) => update('last_name', e.target.value)} /></FormField>
          <FormField label="Пароль"><input type="password" required minLength="6" value={form.password} onChange={(e) => update('password', e.target.value)} /></FormField>
          <FormField label="Повтор пароля"><input type="password" required minLength="6" value={form.password2} onChange={(e) => update('password2', e.target.value)} /></FormField>
          <FormField label="Роль">
            <select value={form.role} onChange={(e) => update('role', e.target.value)}>
              {roleOptions.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
            </select>
          </FormField>
        </div>
        <button className="button button--primary" type="submit" disabled={loading}>{loading ? 'Создаём…' : 'Зарегистрироваться'}</button>
      </form>
    </section>
  );
}
