import { getStatusLabel } from '../utils/format';

export function Alert({ type = 'info', children, onClose }) {
  if (!children) return null;

  return (
    <div className={`alert alert--${type}`}>
      <span>{children}</span>
      {onClose && (
        <button className="alert__close" type="button" onClick={onClose} aria-label="Закрыть уведомление">
          ×
        </button>
      )}
    </div>
  );
}

export function Loading({ text = 'Загрузка данных…' }) {
  return <div className="loading">{text}</div>;
}

export function EmptyState({ title = 'Пока ничего нет', text = 'Данные появятся после добавления записей.' }) {
  return (
    <div className="empty-state">
      <h3>{title}</h3>
      <p>{text}</p>
    </div>
  );
}

export function StatusBadge({ status }) {
  const normalized = status || 'unknown';
  return <span className={`badge badge--${normalized}`}>{getStatusLabel(status)}</span>;
}

export function RoleBadge({ role, label }) {
  return <span className="role-badge">{label || role || 'Гость'}</span>;
}

export function PageHeader({ eyebrow, title, text, actions }) {
  return (
    <section className="page-header">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1>{title}</h1>
        {text && <p>{text}</p>}
      </div>
      {actions && <div className="page-header__actions">{actions}</div>}
    </section>
  );
}

export function Pagination({ pagination, onChange }) {
  if (!pagination || pagination.total_pages <= 1) return null;

  return (
    <div className="pagination">
      <button type="button" className="button button--ghost" disabled={!pagination.has_previous} onClick={() => onChange(pagination.page - 1)}>
        Назад
      </button>
      <span>
        Страница {pagination.page} из {pagination.total_pages} · всего {pagination.count}
      </span>
      <button type="button" className="button button--ghost" disabled={!pagination.has_next} onClick={() => onChange(pagination.page + 1)}>
        Вперёд
      </button>
    </div>
  );
}

export function FormField({ label, children, hint }) {
  return (
    <label className="form-field">
      <span>{label}</span>
      {children}
      {hint && <small>{hint}</small>}
    </label>
  );
}

export function ConfirmButton({ children, confirmText = 'Подтвердить действие?', onClick, ...props }) {
  return (
    <button
      type="button"
      onClick={() => {
        if (window.confirm(confirmText)) onClick?.();
      }}
      {...props}
    >
      {children}
    </button>
  );
}
