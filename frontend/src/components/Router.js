import { createContext, useContext, useEffect, useMemo, useState } from 'react';

const RouterContext = createContext(null);

function getLocationState() {
  return {
    path: window.location.pathname || '/',
    query: new URLSearchParams(window.location.search),
  };
}

export function RouterProvider({ children }) {
  const [location, setLocation] = useState(getLocationState());

  useEffect(() => {
    const onPopState = () => setLocation(getLocationState());
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, []);

  function navigate(to) {
    if (window.location.pathname + window.location.search === to) return;
    window.history.pushState({}, '', to);
    setLocation(getLocationState());
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  const value = useMemo(() => ({ ...location, navigate }), [location]);
  return <RouterContext.Provider value={value}>{children}</RouterContext.Provider>;
}

export function useRouter() {
  const context = useContext(RouterContext);
  if (!context) throw new Error('useRouter must be used inside RouterProvider');
  return context;
}

export function Link({ to, children, className, onClick, ...props }) {
  const { navigate } = useRouter();

  return (
    <a
      href={to}
      className={className}
      onClick={(event) => {
        event.preventDefault();
        onClick?.(event);
        navigate(to);
      }}
      {...props}
    >
      {children}
    </a>
  );
}
