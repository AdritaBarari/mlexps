import { useState } from 'react'
import { logMeal } from '../api/client'
import { CheckCircle, Loader2 } from 'lucide-react'

const MEAL_TYPES = ['breakfast', 'lunch', 'dinner', 'snack', 'meal']

export default function LogMeal() {
  const [form, setForm] = useState({ food_name: '', quantity: '1 serving', meal_type: 'meal' })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    if (!form.food_name.trim()) return
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = await logMeal(form)
      setResult(res.data)
      setForm((f) => ({ ...f, food_name: '', quantity: '1 serving' }))
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to log meal. Check your GROQ_API_KEY.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-xl space-y-5">
      <h1 className="font-heading font-bold text-2xl text-text-primary">Log Meal</h1>
      <p className="text-text-muted text-sm">
        Describe any food — CalorIQ uses AI to estimate calories and macros instantly.
      </p>

      <form onSubmit={submit} className="card space-y-4">
        <div>
          <label className="label">Food description</label>
          <input
            className="input"
            placeholder="e.g. 2 rotis, dal makhani, grilled chicken..."
            value={form.food_name}
            onChange={(e) => setForm({ ...form, food_name: e.target.value })}
            required
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Quantity</label>
            <input
              className="input"
              placeholder="e.g. 1 bowl, 200g, 2 pieces"
              value={form.quantity}
              onChange={(e) => setForm({ ...form, quantity: e.target.value })}
            />
          </div>
          <div>
            <label className="label">Meal type</label>
            <select
              className="input"
              value={form.meal_type}
              onChange={(e) => setForm({ ...form, meal_type: e.target.value })}
            >
              {MEAL_TYPES.map((t) => (
                <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
              ))}
            </select>
          </div>
        </div>
        <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2">
          {loading ? <><Loader2 size={16} className="animate-spin" /> Analyzing...</> : 'Log Meal'}
        </button>
      </form>

      {error && (
        <div className="bg-accent-danger/10 border border-accent-danger/30 text-accent-danger rounded-xl px-4 py-3 text-sm">
          {error}
        </div>
      )}

      {result && (
        <div className="card border-accent/30 space-y-3">
          <div className="flex items-center gap-2 text-accent">
            <CheckCircle size={18} />
            <span className="font-semibold">Logged: {result.food_name}</span>
          </div>
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: 'Calories', value: `${Math.round(result.calories)} kcal` },
              { label: 'Protein', value: `${result.protein}g` },
              { label: 'Carbs', value: `${result.carbs}g` },
              { label: 'Fat', value: `${result.fat}g` },
              { label: 'Fiber', value: `${result.fiber}g` },
              { label: 'Sugar', value: `${result.sugar}g` },
            ].map(({ label, value }) => (
              <div key={label} className="bg-bg-elevated rounded-lg p-3 text-center">
                <p className="text-text-muted text-xs">{label}</p>
                <p className="text-text-primary font-semibold mt-0.5">{value}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
