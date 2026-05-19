import { render, screen } from '@testing-library/react';
import App from './App';

test('renders MatchFlow home page', () => {
  render(<App />);
  expect(screen.getAllByText(/MatchFlow/i).length).toBeGreaterThan(0);
});
