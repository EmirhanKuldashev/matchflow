export const ROLE_LABELS = {
  user: 'Пользователь',
  player: 'Игрок команды',
  captain: 'Капитан команды',
  organizer: 'Организатор турниров',
  admin: 'Администратор',
};

export const STATUS_LABELS = {
  pending: 'На проверке',
  approved: 'Подтверждено',
  rejected: 'Отклонено',
  registration: 'Регистрация',
  active: 'Активно',
  finished: 'Завершено',
  scheduled: 'Запланирован',
  played: 'Сыгран',
  cancelled: 'Отменён',
};

export const GAME_FORMATS = ['5x5', '6x6', '7x7', '8x8', '11x11'];

export function getRoleLabel(role, fallback = 'Гость') {
  return ROLE_LABELS[role] || fallback;
}

export function getStatusLabel(status) {
  return STATUS_LABELS[status] || status || 'Не указано';
}

export function formatDate(value) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(date);
}

export function formatDateTime(value) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

export function asList(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.results)) return payload.results;
  return [];
}

export function paginationFrom(payload) {
  if (!payload || Array.isArray(payload)) {
    return { count: 0, page: 1, page_size: 0, total_pages: 1, has_next: false, has_previous: false };
  }
  return {
    count: payload.count || 0,
    page: payload.page || 1,
    page_size: payload.page_size || 0,
    total_pages: payload.total_pages || 1,
    has_next: Boolean(payload.has_next),
    has_previous: Boolean(payload.has_previous),
  };
}

export function titleOf(item, fallback = 'Без названия') {
  return item?.name || item?.title || item?.username || item?.email || fallback;
}

export function nestedName(value, fallback = '—') {
  if (!value) return fallback;
  if (typeof value === 'string' || typeof value === 'number') return value;
  return value.name || value.username || value.email || value.title || fallback;
}

export function getErrorText(error) {
  const payload = error?.payload;

  if (!payload) return error?.message || 'Произошла ошибка запроса.';
  if (typeof payload === 'string') return payload;
  if (payload.error) return payload.error;
  if (payload.detail) return payload.detail;
  if (payload.message) return payload.message;

  return Object.entries(payload)
    .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : String(value)}`)
    .join('\n');
}
