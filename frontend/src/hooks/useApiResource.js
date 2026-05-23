import { useCallback, useEffect, useRef, useState } from "react";

const identity = (value) => value;

export default function useApiResource(
  fetcher,
  { initialData = null, enabled = true, transform = identity } = {}
) {
  const [data, setData] = useState(initialData);
  const [loading, setLoading] = useState(Boolean(enabled));
  const [error, setError] = useState(null);
  const fetcherRef = useRef(fetcher);
  const transformRef = useRef(transform);

  useEffect(() => {
    fetcherRef.current = fetcher;
  }, [fetcher]);

  useEffect(() => {
    transformRef.current = transform;
  }, [transform]);

  const refetch = useCallback(async () => {
    if (!enabled) return null;
    setLoading(true);
    setError(null);
    try {
      const result = await fetcherRef.current();
      const transformed = transformRef.current(result);
      setData(transformed);
      return transformed;
    } catch (err) {
      setError(err);
      return null;
    } finally {
      setLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    if (!enabled) return;
    refetch();
  }, [enabled, refetch]);

  return { data, loading, error, refetch, setData };
}
