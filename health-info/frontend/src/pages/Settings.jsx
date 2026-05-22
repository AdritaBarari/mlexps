import { useState, useEffect } from 'react'
import { getProfile, updateProfile } from '../api/client'
import { Save, CheckCircle, Loader2 } from 'lucide-react'

export default function Settings() {
  const [form, setForm] = useState({
    name: '', daily_calorie_goal: 2000,
    protein_goal: 150, carbs_goal: 250, fat_goal: 65, whatsapp_number: '',
  })
  const [loading, setLoading] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    getProfile().then((res) => setForm(res.data)).catch(() => {})
  }, [])

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await updateProfile(form)
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } finally {
      setLoading(false)
    }
  }

  const field = (key, label, type = 'text', placeholder = '') => (
    <div>
      <label className="label">{label}</label>
      <input
        type={type} className="input" placeholder={placeholder}
        value={form[key] ?? ''}
        onChange={(e) => setForm({ ...form, [key]: type === 'number' ? parseInt(e.target.value) || 0 : e.target.value })}
      />
    </div>
  )

  return (
    <div className="max-w-xl space-y-5">
      <h1 className="font-heading font-bold text-2xl text-text-primary">Settings</h1>

      <form onSubmit={submit} className="card space-y-5">
        <h2 className="font-heading font-semibold text-text-primary">Profile</h2>
        {field('name', 'Your name', 'text', 'Adrita')}

        <div className="border-t border-border pt-4 space-y-3">
          <h2 className="font-heading font-semibold text-text-primary">Daily Goals</h2>
          <div className="grid grid-cols-2 gap-3">
            {field('daily_calorie_goal', 'Calories (kcal)', 'number', '2000')}
            {field('protein_goal', 'Protein (g)', 'number', '150')}
            {field('carbs_goal', 'Carbs (g)', 'number', '250')}
            {field('fat_goal', 'Fat (g)', 'number', '65')}
          </div>
        </div>

        <div className="border-t border-border pt-4 space-y-3">
          <h2 className="font-heading font-semibold text-text-primary">WhatsApp Alerts</h2>
          <p className="text-text-muted text-sm">
            Your number for calorie warnings and daily summaries via Twilio sandbox.
          </p>
          {field('whatsapp_number', 'WhatsApp number', 'text', '+91XXXXXXXXXX')}
          <div className="bg-bg-elevated rounded-lg p-3 text-sm text-text-muted space-y-1">
            <p className="font-medium text-text-primary">Twilio Sandbox Setup:</p>
            <p>1. Message <span className="text-accent">+1 415 523 8886</span> on WhatsApp</p>
            <p>2. Send the join code from your Twilio console</p>
            <p>3. Set <code className="text-accent text-xs">TWILIO_*</code> keys in <code className="text-xs">.env</code></p>
          </div>
        </div>

        <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2">
          {loading ? <Loader2 size={16} className="animate-spin" /> : saved ? <CheckCircle size={16} /> : <Save size={16} />}
          {saved ? 'Saved!' : 'Save Settings'}
        </button>
      </form>
    </div>
  )
}
