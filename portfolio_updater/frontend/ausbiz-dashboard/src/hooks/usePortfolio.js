import { useState, useEffect, useCallback } from 'react'
import { fetchPortfolio } from '../api/portfolioApi'
import { DUMMY_DATA } from '../data/mockData'

export function usePortfolio(strategy) {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetchPortfolio(strategy)
      setData(response.data)
    } catch (err) {
      setError(err)
      setData(DUMMY_DATA[strategy])
    } finally {
      setLoading(false)
    }
  }, [strategy])

  useEffect(() => {
    load()
  }, [load])

  return { data, loading, error, refetch: load }
}
