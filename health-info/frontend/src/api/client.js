import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

export const getDashboard = (date) => api.get(`/dashboard/${date}`)
export const getProfile = () => api.get('/profile')
export const updateProfile = (data) => api.put('/profile', data)

export const logMeal = (data) => api.post('/meals', data)
export const getMeals = (date) => api.get(`/meals/${date}`)
export const deleteMeal = (id) => api.delete(`/meals/${id}`)

export const logActivity = (data) => api.post('/activity', data)
export const getActivity = (date) => api.get(`/activity/${date}`)
export const deleteActivity = (id) => api.delete(`/activity/${id}`)

export const analyzeRecipe = (data) => api.post('/recipes/analyze', data)
export const listRecipes = () => api.get('/recipes')

export default api
