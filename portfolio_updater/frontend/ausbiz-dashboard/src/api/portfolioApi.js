import apiClient from './axiosConfig'

export const fetchPortfolio = (strategy) =>
  apiClient.get(`/portfolio/${strategy}`)

export const runTradingEngine = (strategy, runType) =>
  apiClient.post('/engine/run', { strategy, run_type: runType }, { timeout: 600_000 })
