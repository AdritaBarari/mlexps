import { useState, useEffect } from 'react'
import { logActivity, getActivity, deleteActivity } from '../api/client'
import { Flame, Trash2, Loader2, CheckCircle } from 'lucide-react'

const ACTIVITY_TYPES = ['steps', 'walk', 'run', 'gym', 'cycling', 'swimming', 'yoga', 'other']

function today() {
  return new Date().toISOString().split('T')[0]
}

export default function Activity() {
  const [form, setForm] = useState({ activity_type: 'walk', steps: '', duration_minutes: '' })
  const [activities, setActivities] = useState([])
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const loadActivities = async () => {
    try {
      const res = await getActivity(today())
      setActivities(res.data)
    } catch (_) {}
  }

  useEffect(() => { loadActivities() }, [])

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setResult(null)
    try {
      const payload = {
        activity_type: form.activity_type,
        steps: form.steps ? parseInt(form.steps) : 0,
        duration_minutes: form.duration_minutes ? parseInt(form.duration_minutes) : 0,
      }
      const res = await logActivity(payload)
      setResult(res.data)
      setForm({ activity_type: 'walk', steps: '', duration_minutes: '' })
      loadActivities()
    } catch (_) {} finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id) => {
    await deleteActivity(id)
    loadActivities()
  }

  const totalBurned = activities.reduce((s, a) => s + a.calories_burned, 0)

  return (
    <div className="max-w-xl space-y-5">
      <h1 className="font-heading font-bold text-2xl text-text-primary">Log Activity</h1>

      <form onSubmit={submit} className="card space-y-4">
        <div>
          <label className="label">Activity type</label>
          <select
            className="input"
            value={form.activity_type}
            onChange={(e) => setForm({ ...form, activity_type: e.target.value })}
          >
            {ACTIVITY_TYPES.map((t) => (
              <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
            ))}
          </select>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Steps (optional)</label>
            <input
              type="number" className="input" placeholder="e.g. 8000"
              value={form.steps}
              onChange={(e) => setForm({ ...form, steps: e.target.value })}
            />
          </div>
          <div>
            <label className="label">Duration (minutes)</label>
            <input
              type="number" className="input" placeholder="e.g. 30"
              value={form.duration_minutes}
              onChange={(e) => setForm({ ...form, duration_minutes: e.target.value })}
            />
          </div>
        </div>
        <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2">
          {loading ? <><Loader2 size={16} className="animate-spin" /> Logging...</> : 'Log Activity'}
        </button>
      </form>

      {result && (
        <div className="card border-accent-warn/30 flex items-center gap-3">
          <CheckCircle size={18} className="text-accent-warn" />
          <div>
            <p className="font-semibold capitalize">{result.activity_type}</p>
            <p className="text-text-muted text-sm">~{Math.round(result.calories_burned)} kcal burned</p>
          </div>
        </div>
      )}

      {activities.length > 0 && (
        <div className="card space-y-1">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-heading font-semibold">Today's Activity</h2>
            <span className="text-accent-warn font-semibold flex items-center gap-1">
              <Flame size={15} /> {Math.round(totalBurned)} kcal
            </span>
          </div>
          {activities.map((a) => (
            <div key={a.id} className="flex items-center justify-between py-2.5 border-b border-border last:border-0">
              <div>
                <p className="text-text-primary font-medium capitalize">{a.activity_type}</p>
                <p className="text-text-muted text-xs">
                  {a.steps > 0 && `${a.steps.toLocaleString()} steps · `}
                  {a.duration_minutes > 0 && `${a.duration_minutes} min`}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-accent-warn font-semibold">{Math.round(a.calories_burned)} kcal</span>
                <button onClick={() => handleDelete(a.id)} className="text-text-muted hover:text-accent-danger transition-colors">
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
