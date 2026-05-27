import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { Link, useRouter } from '../components/Router';
import { Alert, ConfirmButton, EmptyState, FormField, Loading, PageHeader, Pagination, StatusBadge } from '../components/ui';
import { useAuth } from '../context/AuthContext';
import { GAME_FORMATS, asList, formatDate, getErrorText, nestedName, paginationFrom, titleOf } from '../utils/format';
import { RequireAuth } from './ProfilePages';

const tournamentStatuses = [
  { value: 'approved', label: 'Подтверждён' },
  { value: 'registration', label: 'Регистрация' },
  { value: 'active', label: 'Активный' },
  { value: 'finished', label: 'Завершён' },
];

function getCookie(name) {
  const cookies = document.cookie.split('; ');

  for (const cookie of cookies) {
    const [key, value] = cookie.split('=');

    if (key === name) {
      return decodeURIComponent(value || '');
    }
  }

  return '';
}

function buildTournamentQuery(params) {
  const query = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, value);
    }
  });

  return decodeURIComponent(query.toString());
}

export function TournamentsPage() {
  const { isAuthenticated, role } = useAuth();
  const savedCity = getCookie('last_tournament_city');
  const [filters, setFilters] = useState({ search: '', city: savedCity, game_format: '', status: '', page: 1, page_size: 6 });
  const [cookieCity, setCookieCity] = useState(savedCity);
  const [payload, setPayload] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [cacheCheck, setCacheCheck] = useState(null);
  const [cacheLoading, setCacheLoading] = useState(false);

  useEffect(() => {
    let ignore = false;
    setLoading(true);
    api.listTournaments(filters)
      .then((data) => { if (!ignore) setPayload(data); })
      .catch((err) => { if (!ignore) setError(getErrorText(err)); })
      .finally(() => { if (!ignore) setLoading(false); });
    return () => { ignore = true; };
  }, [filters]);

  const tournaments = asList(payload);
  const pagination = paginationFrom(payload);

  function updateFilter(key, value) {
    if (key === 'city') setCookieCity('');
    setFilters((current) => ({ ...current, [key]: value, page: 1 }));
  }

  function clearSavedCity() {
    document.cookie = 'last_tournament_city=; Max-Age=0; path=/';
    setCookieCity('');
    setFilters((current) => ({ ...current, city: '', page: 1 }));
  }

  async function repeatCacheRequest() {
    setCacheLoading(true);
    setError('');

    const startedAt = performance.now();

    try {
      const data = await api.listTournaments(filters);
      const finishedAt = performance.now();

      setPayload(data);
      setCacheCheck({
        duration: Math.round((finishedAt - startedAt) * 10) / 10,
        query: buildTournamentQuery(filters) || 'без query-параметров',
      });
    } catch (err) {
      setError(getErrorText(err));
    } finally {
      setCacheLoading(false);
    }
  }

  return (
    <section className="section">
      <PageHeader
        eyebrow="Турниры"
        title="Публичные турниры MatchFlow"
        text="Показываются только турниры, опубликованные после проверки администратора."
        actions={role === 'organizer' && <Link to="/tournaments/create" className="button button--primary">Создать турнир</Link>}
      />

      <div className="filters filters--wide">
        <input placeholder="Поиск по названию" value={filters.search} onChange={(e) => updateFilter('search', e.target.value)} />
        <input placeholder="Город" value={filters.city} onChange={(e) => updateFilter('city', e.target.value)} />
        <select value={filters.game_format} onChange={(e) => updateFilter('game_format', e.target.value)}>
          <option value="">Любой формат</option>
          {GAME_FORMATS.map((format) => <option key={format} value={format}>{format}</option>)}
        </select>
        <select value={filters.status} onChange={(e) => updateFilter('status', e.target.value)}>
          <option value="">Любой статус</option>
          {tournamentStatuses.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
        </select>
      </div>

      {cookieCity && (
        <div className="cookie-demo">
          <span>Город загружен из cookie: {cookieCity}</span>
          <button className="button button--ghost button--small" type="button" onClick={clearSavedCity}>Очистить сохранённый город</button>
        </div>
      )}

      <article className="panel cache-demo">
        <div>
          <h2>Cache API</h2>
          <p>Список турниров кэшируется backend-ом на 300 секунд.</p>
          <p>Ключ кэша зависит от параметров фильтрации.</p>
          <p>Повторный запрос с теми же параметрами должен использовать cache на backend.</p>
        </div>
        <div className="cache-demo__actions">
          <button className="button button--primary" type="button" disabled={cacheLoading} onClick={repeatCacheRequest}>
            {cacheLoading ? 'Проверяем...' : 'Повторить запрос для проверки cache'}
          </button>
          {cacheCheck && (
            <div className="cache-demo__result">
              <strong>Время последнего запроса: {cacheCheck.duration} мс</strong>
              <span>Query-параметры: {cacheCheck.query}</span>
              <span>Повторный запрос отправлен с теми же параметрами. Backend использует cache для таких повторных запросов.</span>
            </div>
          )}
        </div>
      </article>

      <Alert type="error">{error}</Alert>
      {loading ? <Loading /> : tournaments.length === 0 ? <EmptyState title="Турниры не найдены" text="Попробуйте изменить параметры фильтрации." /> : (
        <div className="cards-grid">
          {tournaments.map((tournament) => (
            <article className="entity-card" key={tournament.id}>
              <div className="entity-card__top"><StatusBadge status={tournament.status} /><span>{tournament.game_format}</span></div>
              <h3>{titleOf(tournament)}</h3>
              <p>{tournament.description || 'Описание турнира пока не заполнено.'}</p>
              <dl className="mini-details">
                <div><dt>Город</dt><dd>{tournament.city || '—'}</dd></div>
                <div><dt>Даты</dt><dd>{formatDate(tournament.start_date)} — {formatDate(tournament.end_date)}</dd></div>
                <div><dt>Организатор</dt><dd>{nestedName(tournament.organizer)}</dd></div>
              </dl>
              <div className="card-actions">
                <Link className="button button--ghost" to={`/tournaments/${tournament.id}`}>Подробнее</Link>
                {isAuthenticated && <SubscribeButton id={tournament.id} />}
                {role === 'captain' && <Link className="button button--secondary" to={`/tournaments/${tournament.id}/apply`}>Подать команду</Link>}
              </div>
            </article>
          ))}
        </div>
      )}

      <Pagination pagination={pagination} onChange={(page) => setFilters((current) => ({ ...current, page }))} />
    </section>
  );
}

function SubscribeButton({ id }) {
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);

  async function subscribe() {
    setBusy(true);
    setMessage('');
    try {
      const response = await api.subscribeTournament(id);
      setMessage(response.message || 'Подписка оформлена.');
    } catch (err) {
      setMessage(getErrorText(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <span className="inline-action">
      <button className="button button--secondary" type="button" disabled={busy} onClick={subscribe}>{busy ? '…' : 'Подписаться'}</button>
      {message && <small>{message}</small>}
    </span>
  );
}

export function TournamentDetailPage({ id }) {
  const { isAuthenticated, role } = useAuth();
  const [tournament, setTournament] = useState(null);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let ignore = false;
    setLoading(true);
    api.getTournament(id)
      .then((data) => { if (!ignore) setTournament(data); })
      .catch((err) => { if (!ignore) setError(getErrorText(err)); })
      .finally(() => { if (!ignore) setLoading(false); });
    return () => { ignore = true; };
  }, [id]);

  async function unsubscribe() {
    setMessage('');
    setError('');
    try {
      const response = await api.unsubscribeTournament(id);
      setMessage(response.message || 'Вы отписались от турнира.');
    } catch (err) {
      setError(getErrorText(err));
    }
  }

  if (loading) return <Loading />;

  return (
    <section className="section">
      <Alert type="success">{message}</Alert>
      <Alert type="error">{error}</Alert>
      {tournament && (
        <>
          <PageHeader
            eyebrow="Турнир"
            title={titleOf(tournament)}
            text={tournament.description || 'Описание турнира пока не заполнено.'}
            actions={role === 'captain' && <Link className="button button--primary" to={`/tournaments/${id}/apply`}>Подать заявку команды</Link>}
          />
          <div className="profile-grid">
            <article className="panel">
              <h2>Информация</h2>
              <dl className="details-list">
                <div><dt>Город</dt><dd>{tournament.city || '—'}</dd></div>
                <div><dt>Формат</dt><dd>{tournament.game_format || '—'}</dd></div>
                <div><dt>Статус</dt><dd><StatusBadge status={tournament.status} /></dd></div>
                <div><dt>Площадка</dt><dd>{nestedName(tournament.stadium)}</dd></div>
                <div><dt>Даты</dt><dd>{formatDate(tournament.start_date)} — {formatDate(tournament.end_date)}</dd></div>
              </dl>
            </article>
            <article className="panel">
              <h2>Правила участия</h2>
              <p>{tournament.rules || 'Правила пока не указаны.'}</p>
              {isAuthenticated && <button className="button button--ghost" type="button" onClick={unsubscribe}>Отписаться</button>}
            </article>
          </div>
        </>
      )}
    </section>
  );
}

export function TournamentFormPage({ id }) {
  const isEdit = Boolean(id);
  const { navigate } = useRouter();
  const [form, setForm] = useState({
    name: '', city: '', game_format: '5x5', start_date: '', end_date: '', description: '', rules: '', stadium: '', confirmation_document: null,
  });
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isEdit) return;
    api.getTournament(id)
      .then((tournament) => setForm({
        name: tournament.name || '', city: tournament.city || '', game_format: tournament.game_format || '5x5',
        start_date: tournament.start_date || '', end_date: tournament.end_date || '', description: tournament.description || '',
        rules: tournament.rules || '', stadium: tournament.stadium?.id || tournament.stadium || '', confirmation_document: null,
      }))
      .catch((err) => setError(getErrorText(err)));
  }, [id, isEdit]);

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');
    try {
      const data = { ...form };
      if (!data.confirmation_document) delete data.confirmation_document;
      const response = isEdit ? await api.updateTournament(id, data) : await api.createTournament(data);
      setMessage(response.message || 'Турнир сохранён.');
      setTimeout(() => navigate('/tournaments'), 900);
    } catch (err) {
      setError(getErrorText(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <RequireAuth>
      <section className="auth-page">
        <PageHeader eyebrow="Организатор" title={isEdit ? 'Редактировать турнир' : 'Создать турнир'} text="При создании отправляется multipart/form-data с подтверждающим документом." />
        <form className="form-card form-card--wide" onSubmit={handleSubmit}>
          <Alert type="success">{message}</Alert>
          <Alert type="error">{error}</Alert>
          <div className="form-grid">
            <FormField label="Название"><input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></FormField>
            <FormField label="Город"><input required value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} /></FormField>
            <FormField label="Формат"><select value={form.game_format} onChange={(e) => setForm({ ...form, game_format: e.target.value })}>{GAME_FORMATS.map((format) => <option key={format} value={format}>{format}</option>)}</select></FormField>
            <FormField label="ID площадки"><input required value={form.stadium} onChange={(e) => setForm({ ...form, stadium: e.target.value })} hint="Пока отдельного endpoint списка площадок нет, поэтому указывается ID Stadium." /></FormField>
            <FormField label="Дата начала"><input type="date" required value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} /></FormField>
            <FormField label="Дата окончания"><input type="date" required value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} /></FormField>
            <FormField label="Документ"><input type="file" onChange={(e) => setForm({ ...form, confirmation_document: e.target.files[0] })} /></FormField>
          </div>
          <FormField label="Описание"><textarea rows="4" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></FormField>
          <FormField label="Правила участия"><textarea rows="4" value={form.rules} onChange={(e) => setForm({ ...form, rules: e.target.value })} /></FormField>
          <button className="button button--primary" type="submit" disabled={loading}>{loading ? 'Сохраняем…' : 'Сохранить турнир'}</button>
        </form>
      </section>
    </RequireAuth>
  );
}

export function TournamentApplyPage({ id }) {
  const { navigate } = useRouter();
  const [form, setForm] = useState({ team_id: '', comment: '' });
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');
    try {
      const response = await api.applyTournament(id, { team_id: Number(form.team_id), comment: form.comment });
      setMessage(response.message || 'Заявка команды отправлена организатору.');
      setTimeout(() => navigate(`/tournaments/${id}`), 900);
    } catch (err) {
      setError(getErrorText(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <RequireAuth>
      <section className="auth-page">
        <PageHeader eyebrow="Капитан" title="Подача команды на турнир" text="Укажите ID своей подтверждённой команды и комментарий для организатора." />
        <form className="form-card" onSubmit={handleSubmit}>
          <Alert type="success">{message}</Alert>
          <Alert type="error">{error}</Alert>
          <FormField label="ID команды"><input type="number" required value={form.team_id} onChange={(e) => setForm({ ...form, team_id: e.target.value })} /></FormField>
          <FormField label="Комментарий"><textarea rows="4" value={form.comment} onChange={(e) => setForm({ ...form, comment: e.target.value })} /></FormField>
          <button className="button button--primary" type="submit" disabled={loading}>{loading ? 'Отправляем…' : 'Подать заявку'}</button>
        </form>
      </section>
    </RequireAuth>
  );
}

export function OrganizerVerificationPage() {
  const [form, setForm] = useState({ organization_name: '', city: '', phone: '', experience_description: '', comment: '', document: null });
  const [current, setCurrent] = useState(null);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.organizerVerification()
      .then((data) => setCurrent(data))
      .catch((err) => setError(getErrorText(err)));
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');
    try {
      const response = await api.createOrganizerVerification(form);
      setMessage(response.message || 'Заявка отправлена администратору.');
      setCurrent(response.verification);
    } catch (err) {
      setError(getErrorText(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <RequireAuth>
      <section className="section">
        <PageHeader eyebrow="Организатор" title="Подтверждение статуса организатора" text="Без подтверждения администратором создание турниров недоступно." />
        <Alert type="success">{message}</Alert>
        <Alert type="error">{error}</Alert>
        {current && !current.message && <div className="panel"><h2>Текущая заявка</h2><StatusBadge status={current.status} /><p>{current.organization_name}</p></div>}
        <form className="form-card form-card--wide" onSubmit={handleSubmit}>
          <div className="form-grid">
            <FormField label="Организация"><input required value={form.organization_name} onChange={(e) => setForm({ ...form, organization_name: e.target.value })} /></FormField>
            <FormField label="Город"><input required value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} /></FormField>
            <FormField label="Телефон"><input required value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></FormField>
            <FormField label="Документ"><input type="file" required onChange={(e) => setForm({ ...form, document: e.target.files[0] })} /></FormField>
          </div>
          <FormField label="Опыт проведения турниров"><textarea rows="4" required value={form.experience_description} onChange={(e) => setForm({ ...form, experience_description: e.target.value })} /></FormField>
          <FormField label="Комментарий"><textarea rows="3" value={form.comment} onChange={(e) => setForm({ ...form, comment: e.target.value })} /></FormField>
          <button className="button button--primary" type="submit" disabled={loading}>{loading ? 'Отправляем…' : 'Отправить заявку'}</button>
        </form>
      </section>
    </RequireAuth>
  );
}

export function TournamentApplicationsPage() {
  const [filters, setFilters] = useState({ status: '', tournament: '' });
  const [items, setItems] = useState([]);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const data = await api.tournamentApplications(filters);
      setItems(asList(data));
    } catch (err) {
      setError(getErrorText(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [filters.status, filters.tournament]);

  async function act(id, action) {
    setError('');
    setMessage('');
    try {
      const response = action === 'approve' ? await api.approveTournamentApplication(id) : await api.rejectTournamentApplication(id);
      setMessage(response.message || 'Заявка обновлена.');
      await load();
    } catch (err) {
      setError(getErrorText(err));
    }
  }

  return (
    <RequireAuth>
      <section className="section">
        <PageHeader eyebrow="Организатор" title="Заявки команд на турниры" text="Организатор видит заявки только на свои турниры." />
        <div className="filters">
          <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
            <option value="">Любой статус</option>
            <option value="pending">На проверке</option>
            <option value="approved">Подтверждены</option>
            <option value="rejected">Отклонены</option>
          </select>
          <input placeholder="ID турнира" value={filters.tournament} onChange={(e) => setFilters({ ...filters, tournament: e.target.value })} />
        </div>
        <Alert type="success">{message}</Alert>
        <Alert type="error">{error}</Alert>
        {loading ? <Loading /> : items.length === 0 ? <EmptyState title="Заявок нет" /> : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Команда</th><th>Турнир</th><th>Комментарий</th><th>Статус</th><th>Действия</th></tr></thead>
              <tbody>{items.map((item) => (
                <tr key={item.id}>
                  <td>{nestedName(item.team)}</td>
                  <td>{nestedName(item.tournament)}</td>
                  <td>{item.comment || '—'}</td>
                  <td><StatusBadge status={item.status} /></td>
                  <td className="table-actions">
                    <ConfirmButton className="button button--small button--primary" disabled={item.status !== 'pending'} onClick={() => act(item.id, 'approve')}>Одобрить</ConfirmButton>
                    <ConfirmButton className="button button--small button--danger" disabled={item.status !== 'pending'} onClick={() => act(item.id, 'reject')}>Отклонить</ConfirmButton>
                  </td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </section>
    </RequireAuth>
  );
}

export function MyTournamentsPage() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const data = await api.myTournaments();
      setItems(asList(data));
    } catch (err) {
      setError(getErrorText(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function unsubscribe(tournamentId) {
    setMessage('');
    setError('');
    try {
      const response = await api.unsubscribeTournament(tournamentId);
      setMessage(response.message || 'Подписка удалена.');
      await load();
    } catch (err) {
      setError(getErrorText(err));
    }
  }

  return (
    <RequireAuth>
      <section className="section">
        <PageHeader eyebrow="Подписки" title="Мои турниры" text="Здесь отображаются турниры, на которые подписан текущий пользователь." />
        <Alert type="success">{message}</Alert>
        <Alert type="error">{error}</Alert>
        {loading ? <Loading /> : items.length === 0 ? <EmptyState title="Вы пока не подписаны на турниры" text="Откройте список турниров и нажмите «Подписаться»." /> : (
          <div className="cards-grid">
            {items.map((item) => {
              const tournament = item.tournament || item;
              return (
                <article className="entity-card" key={item.id || tournament.id}>
                  <StatusBadge status={tournament.status} />
                  <h3>{titleOf(tournament)}</h3>
                  <p>{tournament.city || 'Город не указан'} · {formatDate(tournament.start_date)} — {formatDate(tournament.end_date)}</p>
                  <div className="card-actions">
                    <Link className="button button--ghost" to={`/tournaments/${tournament.id}`}>Открыть</Link>
                    <ConfirmButton className="button button--danger" onClick={() => unsubscribe(tournament.id)}>Отписаться</ConfirmButton>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </RequireAuth>
  );
}
