import apiClient from './axiosConfig'

export const fetchPortfolio = (strategy) =>
  apiClient.get(`/portfolio/${strategy}`)
