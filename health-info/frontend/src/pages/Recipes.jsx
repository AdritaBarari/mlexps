import { useState } from 'react'
import { analyzeRecipe } from '../api/client'
import { ChefHat, Loader2 } from 'lucide-react'

export default function Recipes() {
  const [form, setForm] = useState({ name: '', ingredients_raw: '', servings: 2, save: false })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    if (!form.ingredients_raw.trim()) return
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = await analyzeRecipe({ ...form, servings: parseInt(form.servings) })
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to analyze recipe.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-xl space-y-5">
      <h1 className="font-heading font-bold text-2xl text-text-primary">Recipe Calculator</h1>
      <p className="text-text-muted text-sm">Paste a recipe and get per-serving nutrition in seconds.</p>

      <form onSubmit={submit} className="card space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Recipe name (optional)</label>
            <input
              className="input" placeholder="Palak Paneer"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </div>
          <div>
            <label className="label">Servings</label>
            <input
              type="number" min="1" className="input"
              value={form.servings}
              onChange={(e) => setForm({ ...form, servings: e.target.value })}
            />
          </div>
        </div>
        <div>
          <label className="label">Ingredients</label>
          <textarea
            className="input min-h-[140px] resize-y"
            placeholder="200g paneer&#10;500g spinach&#10;2 tbsp cream&#10;1 tbsp ghee&#10;..."
            value={form.ingredients_raw}
            onChange={(e) => setForm({ ...form, ingredients_raw: e.target.value })}
            required
          />
        </div>
        <label className="flex items-center gap-2 text-sm text-text-muted cursor-pointer">
          <input
            type="checkbox"
            checked={form.save}
            onChange={(e) => setForm({ ...form, save: e.target.checked })}
            className="accent-accent"
          />
          Save recipe to library
        </label>
        <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2">
          {loading ? <><Loader2 size={16} className="animate-spin" /> Analyzing...</> : <><ChefHat size={16} /> Analyze Recipe</>}
        </button>
      </form>

      {error && (
        <div className="bg-accent-danger/10 border border-accent-danger/30 text-accent-danger rounded-xl px-4 py-3 text-sm">
          {error}
        </div>
      )}

      {result && (
        <div className="card space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-heading font-semibold text-lg">{result.name}</h2>
            <span className="badge bg-accent/10 text-accent">{result.servings} servings</span>
          </div>
          <div className="text-center py-3 bg-bg-elevated rounded-xl">
            <p className="font-heading font-bold text-4xl text-text-primary">{Math.round(result.calories_per_serving)}</p>
            <p className="text-text-muted text-sm mt-1">kcal per serving</p>
          </div>
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: 'Protein', value: result.protein, color: 'text-accent' },
              { label: 'Carbs', value: result.carbs, color: 'text-purple-400' },
              { label: 'Fat', value: result.fat, color: 'text-accent-warn' },
            ].map(({ label, value, color }) => (
              <div key={label} className="bg-bg-elevated rounded-lg p-3 text-center">
                <p className="text-text-muted text-xs">{label}</p>
                <p className={`font-semibold mt-0.5 ${color}`}>{value}g</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
