const API_BASE_URL = (process.env.REACT_APP_API_URL || '/api').replace(/\/$/, '');
const TOKEN_KEY = 'matchflow_token';
const USER_KEY = 'matchflow_user';

function buildUrl(path, params = {}) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const url = new URL(`${API_BASE_URL}${normalizedPath}`, window.location.origin);

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      url.searchParams.set(key, value);
    }
  });

  return /^https?:\/\//.test(API_BASE_URL) ? url.toString() : url.pathname + url.search;
}


async function request(path, { method = 'GET', data, params, auth = true, multipart = false } = {}) {
  const headers = {};
  const token = getToken();
  const options = { method, headers };

  if (auth && token) {
    headers.Authorization = `Token ${token}`;
  }

  if (data !== undefined) {
    if (multipart) {
      const formData = new FormData();
      Object.entries(data).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          formData.append(key, value);
        }
      });
      options.body = formData;
    } else {
      headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(data);
    }
  }

  const response = await fetch(buildUrl(path, params), options);
  const contentType = response.headers.get('content-type') || '';
  const payload = contentType.includes('application/json') ? await response.json() : await response.text();

  if (!response.ok) {
    const error = new Error('API request failed');
    error.status = response.status;
    error.payload = payload;
    throw error;
  }

  return payload;
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setSession(token, user) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getStoredUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY));
  } catch {
    return null;
  }
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export const api = {
  register: (data) => request('/register/', { method: 'POST', data, auth: false }),
  login: (data) => request('/login/', { method: 'POST', data, auth: false }),
  profile: () => request('/profile/'),
  updateProfile: (data) => request('/profile/update/', { method: 'PATCH', data }),

  listTeams: (params) => request('/teams/', { params, auth: false }),
  getTeam: async (id) => {
    try {
      return await request(`/teams/${id}/`, { auth: false });
    } catch (error) {
      if (![404, 405].includes(error.status)) throw error;
      const data = await request('/teams/', { params: { page_size: 50 }, auth: false });
      const team = (data.results || data || []).find((item) => String(item.id) === String(id));
      if (!team) throw error;
      return team;
    }
  },
  createTeam: (data) => request('/teams/create/', { method: 'POST', data }),
  updateTeam: (id, data) => request(`/teams/${id}/update/`, { method: 'PATCH', data }),
  joinTeam: (teamId, data) => request(`/teams/${teamId}/join/`, { method: 'POST', data }),
  captainJoinRequests: () => request('/captain/join-requests/'),
  approveJoinRequest: (id) => request(`/join-requests/${id}/approve/`, { method: 'POST' }),
  rejectJoinRequest: (id) => request(`/join-requests/${id}/reject/`, { method: 'POST' }),
  approveTeam: (id) => request(`/admin/teams/${id}/approve/`, { method: 'POST' }),
  rejectTeam: (id) => request(`/admin/teams/${id}/reject/`, { method: 'POST' }),

  organizerVerification: () => request('/organizer/verification/'),
  createOrganizerVerification: (data) => request('/organizer/verification/', { method: 'POST', data, multipart: true }),

  listTournaments: (params) => request('/tournaments/', { params, auth: false }),
  getTournament: (id) => request(`/tournaments/${id}/`, { auth: false }),
  createTournament: (data) => request('/tournaments/create/', { method: 'POST', data, multipart: true }),
  updateTournament: (id, data) => request(`/tournaments/${id}/update/`, { method: 'PATCH', data, multipart: Boolean(data.confirmation_document) }),
  applyTournament: (id, data) => request(`/tournaments/${id}/apply/`, { method: 'POST', data }),
  tournamentApplications: (params) => request('/organizer/tournament-applications/', { params }),
  approveTournamentApplication: (id) => request(`/tournament-applications/${id}/approve/`, { method: 'POST' }),
  rejectTournamentApplication: (id) => request(`/tournament-applications/${id}/reject/`, { method: 'POST' }),
  subscribeTournament: (id) => request(`/tournaments/${id}/subscribe/`, { method: 'POST' }),
  unsubscribeTournament: (id) => request(`/tournaments/${id}/unsubscribe/`, { method: 'POST' }),
  myTournaments: () => request('/my-tournaments/'),

  listMatches: (params) => request('/matches/', { params, auth: false }),
  getMatch: (id) => request(`/matches/${id}/`, { auth: false }),
  createMatch: (data) => request('/matches/create/', { method: 'POST', data }),
  updateMatch: (id, data) => request(`/matches/${id}/update/`, { method: 'PATCH', data }),
  updateMatchResult: (id, data) => request(`/matches/${id}/result/`, { method: 'PATCH', data }),
  cancelMatch: (id) => request(`/matches/${id}/cancel/`, { method: 'POST' }),
  rescheduleMatch: (id, data) => request(`/matches/${id}/reschedule/`, { method: 'PATCH', data }),
};
