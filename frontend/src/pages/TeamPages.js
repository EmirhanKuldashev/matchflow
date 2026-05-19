import { useEffect, useMemo, useState } from 'react';
import { api } from '../api/client';
import { Link, useRouter } from '../components/Router';
import { Alert, ConfirmButton, EmptyState, FormField, Loading, PageHeader, Pagination, StatusBadge } from '../components/ui';
import { useAuth } from '../context/AuthContext';
import { GAME_FORMATS, asList, formatDate, getErrorText, nestedName, paginationFrom, titleOf } from '../utils/format';
import { RequireAuth } from './ProfilePages';

export function TeamsPage() {
  const { role, isAuthenticated } = useAuth();
  const [filters, setFilters] = useState({ search: '', city: '', game_format: '', page: 1, page_size: 6 });
  const [payload, setPayload] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let ignore = false;
    setLoading(true);
    api.listTeams(filters)
      .then((data) => { if (!ignore) setPayload(data); })
      .catch((err) => { if (!ignore) setError(getErrorText(err)); })
      .finally(() => { if (!ignore) setLoading(false); });
    return () => { ignore = true; };
  }, [filters]);

  const teams = asList(payload);
  const pagination = paginationFrom(payload);

  function updateFilter(key, value) {
    setFilters((current) => ({ ...current, [key]: value, page: 1 }));
  }

  return (
    <section className="section">
      <PageHeader
        eyebrow="Команды"
        title="Подтверждённые футбольные команды"
        text="Поиск, фильтрация и пагинация идут напрямую через query-параметры backend API."
        actions={role === 'captain' && <Link to="/teams/create" className="button button--primary">Создать команду</Link>}
      />

      <div className="filters">
        <input placeholder="Поиск по названию" value={filters.search} onChange={(e) => updateFilter('search', e.target.value)} />
        <input placeholder="Город" value={filters.city} onChange={(e) => updateFilter('city', e.target.value)} />
        <select value={filters.game_format} onChange={(e) => updateFilter('game_format', e.target.value)}>
          <option value="">Любой формат</option>
          {GAME_FORMATS.map((format) => <option key={format} value={format}>{format}</option>)}
        </select>
      </div>

      <Alert type="error">{error}</Alert>
      {loading ? <Loading /> : teams.length === 0 ? <EmptyState title="Команды не найдены" text="Попробуйте изменить фильтры или дождитесь подтверждения команд администратором." /> : (
        <div className="cards-grid">
          {teams.map((team) => (
            <article className="entity-card" key={team.id}>
              <div className="entity-card__top">
                <StatusBadge status={team.status} />
                <span>{team.game_format || 'формат не указан'}</span>
              </div>
              <h3>{titleOf(team)}</h3>
              <p>{team.description || 'Описание команды пока не заполнено.'}</p>
              <dl className="mini-details">
                <div><dt>Город</dt><dd>{team.city || '—'}</dd></div>
                <div><dt>Капитан</dt><dd>{nestedName(team.captain || team.captain_name || team.captain_username)}</dd></div>
                <div><dt>Создана</dt><dd>{formatDate(team.created_at)}</dd></div>
              </dl>
              <div className="card-actions">
                <Link className="button button--ghost" to={`/teams/${team.id}`}>Подробнее</Link>
                {isAuthenticated && role === 'player' && <Link className="button button--secondary" to={`/teams/${team.id}/join`}>Вступить</Link>}
              </div>
            </article>
          ))}
        </div>
      )}

      <Pagination pagination={pagination} onChange={(page) => setFilters((current) => ({ ...current, page }))} />
    </section>
  );
}

export function TeamDetailPage({ id }) {
  const { role, isAuthenticated } = useAuth();
  const [team, setTeam] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let ignore = false;
    setLoading(true);
    api.getTeam(id)
      .then((data) => { if (!ignore) setTeam(data); })
      .catch((err) => { if (!ignore) setError(getErrorText(err)); })
      .finally(() => { if (!ignore) setLoading(false); });
    return () => { ignore = true; };
  }, [id]);

  if (loading) return <Loading />;

  return (
    <section className="section">
      <Alert type="error">{error}</Alert>
      {team && (
        <>
          <PageHeader
            eyebrow="Карточка команды"
            title={titleOf(team)}
            text={team.description || 'Команда пока без подробного описания.'}
            actions={isAuthenticated && role === 'player' && <Link className="button button--primary" to={`/teams/${id}/join`}>Подать заявку</Link>}
          />
          <div className="panel">
            <dl className="details-list">
              <div><dt>Город</dt><dd>{team.city || '—'}</dd></div>
              <div><dt>Формат</dt><dd>{team.game_format || '—'}</dd></div>
              <div><dt>Статус</dt><dd><StatusBadge status={team.status} /></dd></div>
              <div><dt>Капитан</dt><dd>{nestedName(team.captain || team.captain_name || team.captain_username)}</dd></div>
              <div><dt>Создана</dt><dd>{formatDate(team.created_at)}</dd></div>
            </dl>
          </div>
        </>
      )}
    </section>
  );
}

export function TeamFormPage({ id }) {
  const isEdit = Boolean(id);
  const { navigate } = useRouter();
  const [form, setForm] = useState({ name: '', city: '', game_format: '5x5', description: '' });
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isEdit) return;
    api.getTeam(id)
      .then((team) => setForm({ name: team.name || '', city: team.city || '', game_format: team.game_format || '5x5', description: team.description || '' }))
      .catch((err) => setError(getErrorText(err)));
  }, [id, isEdit]);

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);
    try {
      const response = isEdit ? await api.updateTeam(id, form) : await api.createTeam(form);
      setMessage(response.message || 'Команда сохранена.');
      setTimeout(() => navigate('/teams'), 800);
    } catch (err) {
      setError(getErrorText(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <RequireAuth>
      <section className="auth-page">
        <PageHeader eyebrow="Капитан" title={isEdit ? 'Редактировать команду' : 'Создать команду'} text="После создания команда получает статус проверки у администратора." />
        <form className="form-card form-card--wide" onSubmit={handleSubmit}>
          <Alert type="success">{message}</Alert>
          <Alert type="error">{error}</Alert>
          <div className="form-grid">
            <FormField label="Название"><input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></FormField>
            <FormField label="Город"><input required value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} /></FormField>
            <FormField label="Формат игры">
              <select value={form.game_format} onChange={(e) => setForm({ ...form, game_format: e.target.value })}>
                {GAME_FORMATS.map((format) => <option key={format} value={format}>{format}</option>)}
              </select>
            </FormField>
          </div>
          <FormField label="Описание"><textarea rows="5" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></FormField>
          <button className="button button--primary" type="submit" disabled={loading}>{loading ? 'Сохраняем…' : 'Сохранить команду'}</button>
        </form>
      </section>
    </RequireAuth>
  );
}

export function TeamJoinPage({ id }) {
  const { navigate } = useRouter();
  const [form, setForm] = useState({ position: '', age: '', number: '', comment: '' });
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);
    try {
      const response = await api.joinTeam(id, { ...form, age: Number(form.age), number: Number(form.number) });
      setMessage(response.message || 'Заявка отправлена капитану.');
      setTimeout(() => navigate('/teams'), 900);
    } catch (err) {
      setError(getErrorText(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <RequireAuth>
      <section className="auth-page">
        <PageHeader eyebrow="Игрок" title="Заявка на вступление в команду" text="Заявка отправляется капитану команды через `/api/teams/<id>/join/`." />
        <form className="form-card" onSubmit={handleSubmit}>
          <Alert type="success">{message}</Alert>
          <Alert type="error">{error}</Alert>
          <FormField label="Игровая позиция"><input required value={form.position} onChange={(e) => setForm({ ...form, position: e.target.value })} /></FormField>
          <FormField label="Возраст"><input type="number" min="10" max="70" required value={form.age} onChange={(e) => setForm({ ...form, age: e.target.value })} /></FormField>
          <FormField label="Желаемый номер"><input type="number" min="1" max="99" required value={form.number} onChange={(e) => setForm({ ...form, number: e.target.value })} /></FormField>
          <FormField label="Комментарий"><textarea rows="4" value={form.comment} onChange={(e) => setForm({ ...form, comment: e.target.value })} /></FormField>
          <button className="button button--primary" type="submit" disabled={loading}>{loading ? 'Отправляем…' : 'Отправить заявку'}</button>
        </form>
      </section>
    </RequireAuth>
  );
}

export function CaptainRequestsPage() {
  const [requests, setRequests] = useState([]);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);

  const pendingCount = useMemo(() => requests.filter((item) => item.status === 'pending').length, [requests]);

  async function load() {
    setLoading(true);
    try {
      const data = await api.captainJoinRequests();
      setRequests(asList(data));
    } catch (err) {
      setError(getErrorText(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function act(id, action) {
    setError('');
    setMessage('');
    try {
      const response = action === 'approve' ? await api.approveJoinRequest(id) : await api.rejectJoinRequest(id);
      setMessage(response.message || 'Статус заявки обновлён.');
      await load();
    } catch (err) {
      setError(getErrorText(err));
    }
  }

  return (
    <RequireAuth>
      <section className="section">
        <PageHeader eyebrow="Капитан" title="Заявки игроков" text={`Ожидают рассмотрения: ${pendingCount}`} />
        <Alert type="success">{message}</Alert>
        <Alert type="error">{error}</Alert>
        {loading ? <Loading /> : requests.length === 0 ? <EmptyState title="Заявок пока нет" /> : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Игрок</th><th>Команда</th><th>Позиция</th><th>Номер</th><th>Статус</th><th>Действия</th></tr></thead>
              <tbody>
                {requests.map((item) => (
                  <tr key={item.id}>
                    <td>{nestedName(item.user)}</td>
                    <td>{nestedName(item.team)}</td>
                    <td>{item.position || '—'}</td>
                    <td>{item.number || '—'}</td>
                    <td><StatusBadge status={item.status} /></td>
                    <td className="table-actions">
                      <ConfirmButton className="button button--small button--primary" disabled={item.status !== 'pending'} onClick={() => act(item.id, 'approve')}>Одобрить</ConfirmButton>
                      <ConfirmButton className="button button--small button--danger" disabled={item.status !== 'pending'} onClick={() => act(item.id, 'reject')}>Отклонить</ConfirmButton>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </RequireAuth>
  );
}
