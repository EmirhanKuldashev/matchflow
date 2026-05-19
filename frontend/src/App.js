import './App.css';
import { RouterProvider, useRouter } from './components/Router';
import { Layout } from './components/Layout';
import { AuthProvider } from './context/AuthContext';
import { HomePage } from './pages/HomePage';
import { LoginPage, RegisterPage } from './pages/AuthPages';
import { ProfileEditPage, ProfilePage } from './pages/ProfilePages';
import { CaptainRequestsPage, TeamDetailPage, TeamFormPage, TeamJoinPage, TeamsPage } from './pages/TeamPages';
import {
  MyTournamentsPage,
  OrganizerVerificationPage,
  TournamentApplicationsPage,
  TournamentApplyPage,
  TournamentDetailPage,
  TournamentFormPage,
  TournamentsPage,
} from './pages/TournamentPages';
import { MatchDetailPage, MatchFormPage, MatchResultPage, MatchesPage } from './pages/MatchPages';
import { Link } from './components/Router';

function Routes() {
  const { path } = useRouter();
  const parts = path.split('/').filter(Boolean);

  if (path === '/') return <HomePage />;
  if (path === '/login') return <LoginPage />;
  if (path === '/register') return <RegisterPage />;
  if (path === '/profile') return <ProfilePage />;
  if (path === '/profile/edit') return <ProfileEditPage />;

  if (path === '/teams') return <TeamsPage />;
  if (path === '/teams/create') return <TeamFormPage />;
  if (parts[0] === 'teams' && parts[2] === 'join') return <TeamJoinPage id={parts[1]} />;
  if (parts[0] === 'teams' && parts[2] === 'edit') return <TeamFormPage id={parts[1]} />;
  if (parts[0] === 'teams' && parts[1]) return <TeamDetailPage id={parts[1]} />;
  if (path === '/captain/join-requests') return <CaptainRequestsPage />;

  if (path === '/tournaments') return <TournamentsPage />;
  if (path === '/tournaments/create') return <TournamentFormPage />;
  if (parts[0] === 'tournaments' && parts[2] === 'apply') return <TournamentApplyPage id={parts[1]} />;
  if (parts[0] === 'tournaments' && parts[2] === 'edit') return <TournamentFormPage id={parts[1]} />;
  if (parts[0] === 'tournaments' && parts[1]) return <TournamentDetailPage id={parts[1]} />;
  if (path === '/organizer/verification') return <OrganizerVerificationPage />;
  if (path === '/organizer/tournament-applications') return <TournamentApplicationsPage />;
  if (path === '/my-tournaments') return <MyTournamentsPage />;

  if (path === '/matches') return <MatchesPage />;
  if (path === '/matches/create') return <MatchFormPage />;
  if (parts[0] === 'matches' && parts[2] === 'result') return <MatchResultPage id={parts[1]} />;
  if (parts[0] === 'matches' && parts[2] === 'edit') return <MatchFormPage id={parts[1]} />;
  if (parts[0] === 'matches' && parts[1]) return <MatchDetailPage id={parts[1]} />;

  return <NotFoundPage />;
}

function NotFoundPage() {
  return (
    <section className="section not-found">
      <h1>Страница не найдена</h1>
      <p>Такого маршрута нет в frontend-приложении.</p>
      <Link className="button button--primary" to="/">На главную</Link>
    </section>
  );
}

function AppContent() {
  return (
    <Layout>
      <Routes />
    </Layout>
  );
}

export default function App() {
  return (
    <RouterProvider>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </RouterProvider>
  );
}
