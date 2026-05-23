import { useCallback, useEffect, useState } from "react";
import { getHealth } from "../services/api";

const INITIAL_STATE = {
  loading: true,
  online: false,
  data: null,
  error: null,
};

let healthCache = null;
let healthRequestPromise = null;

async function fetchHealth({ force = false } = {}) {
  if (!force && healthCache) {
    return healthCache;
  }

  if (!force && healthRequestPromise) {
    return healthRequestPromise;
  }

  healthRequestPromise = (async () => {
    try {
      const data = await getHealth();
      healthCache = {
        loading: false,
        online: true,
        data,
        error: null,
      };
      return healthCache;
    } catch (error) {
      healthCache = {
        loading: false,
        online: false,
        data: null,
        error,
      };
      return healthCache;
    } finally {
      healthRequestPromise = null;
    }
  })();

  return healthRequestPromise;
}

export default function useHealth() {
  const [state, setState] = useState(() => healthCache || INITIAL_STATE);

  const checkHealth = useCallback(async ({ force = false } = {}) => {
    if (!healthCache || force) {
      setState((prev) => ({ ...prev, loading: true, error: null }));
    }

    const nextState = await fetchHealth({ force });
    setState(nextState);
    return nextState;
  }, []);

  useEffect(() => {
    let cancelled = false;

    if (healthCache) {
      setState(healthCache);
      return () => {
        cancelled = true;
      };
    }

    (async () => {
      const nextState = await fetchHealth();
      if (!cancelled) {
        setState(nextState);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [checkHealth]);

  return {
    ...state,
    refetch: () => checkHealth({ force: true }),
  };
}
