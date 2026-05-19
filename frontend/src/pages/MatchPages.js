import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { Link, useRouter } from '../components/Router';
import { Alert, ConfirmButton, EmptyState, FormField, Loading, PageHeader, Pagination, StatusBadge } from '../components/ui';
import { useAuth } from '../context/AuthContext';
import { asList, formatDateTime, getErrorText, nestedName, paginationFrom, titleOf } from '../utils/format';
import { RequireAuth } from './ProfilePages';

const matchStatuses = [
  { value: 'scheduled', label: 'Запланирован' },
  { value: 'played', label: 'Сыгран' },
  { value: 'cancelled', label: 'Отменён' },
];

export function MatchesPage() {
  const { role } = useAuth();
  const [filters, setFilters] = useState({ search: '', tournament: '', team: '', status: '', page: 1, page_size: 8 });
  const [payload, setPayload] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let ignore = false;
    setLoading(true);
    api.listMatches(filters)
      .then((data) => { if (!ignore) setPayload(data); })
      .catch((err) => { if (!ignore) setError(getErrorText(err)); })
      .finally(() => { if (!ignore) setLoading(false); });
    return () => { ignore = true; };
  }, [filters]);

  const matches = asList(payload);
  const pagination = paginationFrom(payload);

  function updateFilter(key, value) {
    setFilters((current) => ({ ...current, [key]: value, page: 1 }));
  }

  return (
    <section className="section">
      <PageHeader
        eyebrow="Матчи"
        title="Расписание и результаты матчей"
        text="Фильтрация по турниру, команде и статусу работает через `/api/matches/`."
        actions={role === 'organizer' && <Link to="/matches/create" className="button button--primary">Создать матч</Link>}
      />
      <div className="filters filters--wide">
        <input placeholder="Поиск" value={filters.search} onChange={(e) => updateFilter('search', e.target.value)} />
        <input placeholder="ID турнира" value={filters.tournament} onChange={(e) => updateFilter('tournament', e.target.value)} />
        <input placeholder="ID команды" value={filters.team} onChange={(e) => updateFilter('team', e.target.value)} />
        <select value={filters.status} onChange={(e) => updateFilter('status', e.target.value)}>
          <option value="">Любой статус</option>
          {matchStatuses.map((status) => <option key={status.value} value={status.value}>{status.label}</option>)}
        </select>
      </div>
      <Alert type="error">{error}</Alert>
      {loading ? <Loading /> : matches.length === 0 ? <EmptyState title="Матчи не найдены" /> : (
        <div className="match-list">
          {matches.map((match) => (
            <article className="match-card" key={match.id}>
              <div className="match-card__meta">
                <StatusBadge status={match.status} />
                <span>{formatDateTime(match.match_date)}</span>
              </div>
              <div className="match-card__score">
                <strong>{nestedName(match.team1)}</strong>
                <span>{match.team1_score ?? '—'} : {match.team2_score ?? '—'}</span>
                <strong>{nestedName(match.team2)}</strong>
              </div>
              <p>{nestedName(match.tournament)} · {nestedName(match.stadium)}</p>
              <div className="card-actions">
                <Link to={`/matches/${match.id}`} className="button button--ghost">Подробнее</Link>
                {role === 'organizer' && <Link to={`/matches/${match.id}/result`} className="button button--secondary">Внести результат</Link>}
              </div>
            </article>
          ))}
        </div>
      )}
      <Pagination pagination={pagination} onChange={(page) => setFilters((current) => ({ ...current, page }))} />
    </section>
  );
}

export function MatchDetailPage({ id }) {
  const { role } = useAuth();
  const [match, setMatch] = useState(null);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const data = await api.getMatch(id);
      setMatch(data);
    } catch (err) {
      setError(getErrorText(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [id]);

  async function cancelMatch() {
    setError('');
    setMessage('');
    try {
      const response = await api.cancelMatch(id);
      setMessage(response.message || 'Матч отменён.');
      await load();
    } catch (err) {
      setError(getErrorText(err));
    }
  }

  if (loading) return <Loading />;

  return (
    <section className="section">
      <Alert type="success">{message}</Alert>
      <Alert type="error">{error}</Alert>
      {match && (
        <>
          <PageHeader
            eyebrow="Матч"
            title={`${nestedName(match.team1)} vs ${nestedName(match.team2)}`}
            text={`${nestedName(match.tournament)} · ${formatDateTime(match.match_date)}`}
            actions={role === 'organizer' && <Link className="button button--primary" to={`/matches/${id}/result`}>Внести результат</Link>}
          />
          <div className="profile-grid">
            <article className="panel">
              <h2>Счёт</h2>
              <div className="big-score">
                <span>{nestedName(match.team1)}</span>
                <strong>{match.team1_score ?? '—'} : {match.team2_score ?? '—'}</strong>
                <span>{nestedName(match.team2)}</span>
              </div>
            </article>
            <article className="panel">
              <h2>Данные матча</h2>
              <dl className="details-list">
                <div><dt>Статус</dt><dd><StatusBadge status={match.status} /></dd></div>
                <div><dt>Площадка</dt><dd>{nestedName(match.stadium)}</dd></div>
                <div><dt>Турнир</dt><dd>{nestedName(match.tournament)}</dd></div>
                <div><dt>Дата и время</dt><dd>{formatDateTime(match.match_date)}</dd></div>
              </dl>
              {role === 'organizer' && <ConfirmButton className="button button--danger" onClick={cancelMatch}>Отменить матч</ConfirmButton>}
            </article>
          </div>
        </>
      )}
    </section>
  );
}

export function MatchFormPage({ id }) {
  const isEdit = Boolean(id);
  const { navigate } = useRouter();
  const [form, setForm] = useState({ tournament: '', team1: '', team2: '', stadium: '', match_date: '' });
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isEdit) return;
    api.getMatch(id)
      .then((match) => setForm({
        tournament: match.tournament?.id || match.tournament || '',
        team1: match.team1?.id || match.team1 || '',
        team2: match.team2?.id || match.team2 || '',
        stadium: match.stadium?.id || match.stadium || '',
        match_date: match.match_date ? match.match_date.slice(0, 16) : '',
      }))
      .catch((err) => setError(getErrorText(err)));
  }, [id, isEdit]);

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');
    const payload = {
      tournament: Number(form.tournament),
      team1: Number(form.team1),
      team2: Number(form.team2),
      stadium: Number(form.stadium),
      match_date: form.match_date,
    };
    try {
      const response = isEdit ? await api.updateMatch(id, payload) : await api.createMatch(payload);
      setMessage(response.message || 'Матч сохранён.');
      setTimeout(() => navigate('/matches'), 900);
    } catch (err) {
      setError(getErrorText(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <RequireAuth>
      <section className="auth-page">
        <PageHeader eyebrow="Организатор" title={isEdit ? 'Редактировать матч' : 'Создать матч'} text="Создание матча доступно организатору турнира." />
        <form className="form-card form-card--wide" onSubmit={handleSubmit}>
          <Alert type="success">{message}</Alert>
          <Alert type="error">{error}</Alert>
          <div className="form-grid">
            <FormField label="ID турнира"><input type="number" required value={form.tournament} onChange={(e) => setForm({ ...form, tournament: e.target.value })} /></FormField>
            <FormField label="ID первой команды"><input type="number" required value={form.team1} onChange={(e) => setForm({ ...form, team1: e.target.value })} /></FormField>
            <FormField label="ID второй команды"><input type="number" required value={form.team2} onChange={(e) => setForm({ ...form, team2: e.target.value })} /></FormField>
            <FormField label="ID площадки"><input type="number" required value={form.stadium} onChange={(e) => setForm({ ...form, stadium: e.target.value })} /></FormField>
            <FormField label="Дата и время"><input type="datetime-local" required value={form.match_date} onChange={(e) => setForm({ ...form, match_date: e.target.value })} /></FormField>
          </div>
          <button className="button button--primary" type="submit" disabled={loading}>{loading ? 'Сохраняем…' : 'Сохранить матч'}</button>
        </form>
      </section>
    </RequireAuth>
  );
}

export function MatchResultPage({ id }) {
  const { navigate } = useRouter();
  const [form, setForm] = useState({ team1_score: '', team2_score: '', status: 'played' });
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');
    try {
      const response = await api.updateMatchResult(id, {
        team1_score: Number(form.team1_score),
        team2_score: Number(form.team2_score),
        status: form.status,
      });
      setMessage(response.message || 'Результат сохранён.');
      setTimeout(() => navigate(`/matches/${id}`), 900);
    } catch (err) {
      setError(getErrorText(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <RequireAuth>
      <section className="auth-page">
        <PageHeader eyebrow="Организатор" title="Внесение результата матча" text="PATCH-запрос отправляется на `/api/matches/<id>/result/`." />
        <form className="form-card" onSubmit={handleSubmit}>
          <Alert type="success">{message}</Alert>
          <Alert type="error">{error}</Alert>
          <FormField label="Счёт первой команды"><input type="number" min="0" required value={form.team1_score} onChange={(e) => setForm({ ...form, team1_score: e.target.value })} /></FormField>
          <FormField label="Счёт второй команды"><input type="number" min="0" required value={form.team2_score} onChange={(e) => setForm({ ...form, team2_score: e.target.value })} /></FormField>
          <FormField label="Статус"><select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}><option value="played">Сыгран</option><option value="scheduled">Запланирован</option></select></FormField>
          <button className="button button--primary" type="submit" disabled={loading}>{loading ? 'Сохраняем…' : 'Сохранить результат'}</button>
        </form>
      </section>
    </RequireAuth>
  );
}
