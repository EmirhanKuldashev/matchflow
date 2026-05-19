import { Link } from '../components/Router';
import { PageHeader } from '../components/ui';
import { useAuth } from '../context/AuthContext';
import { getRoleLabel } from '../utils/format';

export function HomePage() {
  const { isAuthenticated, role } = useAuth();

  return (
    <>
      <section className="hero">
        <div className="hero__content">
          <p className="eyebrow">Организация любительского футбола без хаоса</p>
          <h1>Команды, турниры, заявки и матчи в одном интерфейсе.</h1>
          <p>
            MatchFlow помогает игрокам находить команды, капитанам управлять составом,
            организаторам проводить турниры, а болельщикам отслеживать расписание и результаты.
          </p>
          <div className="hero__actions">
            <Link to="/tournaments" className="button button--primary">Смотреть турниры</Link>
            <Link to="/teams" className="button button--secondary">Найти команду</Link>
          </div>
        </div>
        <div className="hero__panel">
          <div className="score-card">
            <span>Ближайший матч</span>
            <strong>FC Aurora · 19:30 · City Arena</strong>
            <small>Данные подтягиваются через `/api/matches/`</small>
          </div>
          <div className="stat-grid">
            <div><strong>Роли</strong><span>игрок · капитан · организатор</span></div>
            <div><strong>API</strong><span>Django REST + Token Auth</span></div>
            <div><strong>UX</strong><span>поиск · фильтры · пагинация</span></div>
          </div>
        </div>
      </section>

      <section className="section">
        <PageHeader
          eyebrow="Что уже доступно"
          title="Полноценная frontend-часть под требования ТЗ"
          text="Интерфейс закрывает публичные страницы, личный кабинет, ролевые действия и работу с файлами для подтверждения организаторов и турниров."
        />
        <div className="feature-grid">
          <article className="feature-card">
            <span>👤</span>
            <h3>Авторизация и роли</h3>
            <p>Регистрация, вход по email, сохранение токена, ролевое меню и защищённые действия.</p>
          </article>
          <article className="feature-card">
            <span>🏟️</span>
            <h3>Команды и заявки</h3>
            <p>Просмотр команд, создание команды капитаном, заявка игрока и рассмотрение заявок капитаном.</p>
          </article>
          <article className="feature-card">
            <span>🏆</span>
            <h3>Турниры</h3>
            <p>Список, фильтрация, подписки, подача команды на турнир и кабинет организатора.</p>
          </article>
          <article className="feature-card">
            <span>📅</span>
            <h3>Матчи</h3>
            <p>Расписание, карточка матча, создание, перенос, отмена и внесение результата.</p>
          </article>
        </div>
      </section>

      {isAuthenticated && (
        <section className="section section--accent">
          <h2>Вы вошли как {getRoleLabel(role)}.</h2>
          <p>Доступные действия автоматически подстраиваются под вашу роль.</p>
          <Link to="/profile" className="button button--primary">Перейти в кабинет</Link>
        </section>
      )}
    </>
  );
}
