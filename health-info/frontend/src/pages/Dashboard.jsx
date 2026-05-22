import { useState, useEffect, useCallback } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { getDashboard, deleteMeal } from '../api/client'
import CalorieRing from '../components/CalorieRing'
import MacroBars from '../components/MacroBars'
import MealCard from '../components/MealCard'
import AlertBanner from '../components/AlertBanner'
import { Flame, Footprints, RefreshCw } from 'lucide-react'

function today() {
  return new Date().toISOString().split('T')[0]
}

export default function Dashboard() {
  const [date, setDate] = useState(today())
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await getDashboard(date)
      setData(res.data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }, [date])

  useEffect(() => { load() }, [load])

  const handleDelete = async (id) => {
    await deleteMeal(id)
    load()
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw size={24} className="animate-spin text-accent" />
      </div>
    )
  }

  if (!data) return <p className="text-text-muted">Failed to load dashboard.</p>

  const { calories_in, calories_burned, calorie_goal, calorie_pct, macros, goals, meals, activities, trend } = data

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="font-heading font-bold text-2xl text-text-primary">Dashboard</h1>
        <div className="flex items-center gap-2">
          <input
            type="date"
            value={date}
            max={today()}
            onChange={(e) => setDate(e.target.value)}
            className="input w-auto text-sm"
          />
          <button onClick={load} className="btn-ghost p-2.5">
            <RefreshCw size={15} />
          </button>
        </div>
      </div>

      <AlertBanner caloriePct={calorie_pct} />

      {/* Top row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Calorie ring */}
        <div className="card flex items-center justify-center">
          <CalorieRing caloriesIn={calories_in} caloriesOut={calories_burned} goal={calorie_goal} />
        </div>

        {/* Macros */}
        <div className="card md:col-span-2 space-y-4">
          <h2 className="font-heading font-semibold text-lg">Macronutrients</h2>
          <MacroBars macros={macros} goals={goals} />
          <div className="grid grid-cols-3 gap-3 pt-2">
            {[
              { label: 'Fiber', value: macros.fiber, unit: 'g' },
              { label: 'Sugar', value: macros.sugar, unit: 'g' },
              { label: 'Burned', value: calories_burned, unit: 'kcal', icon: Flame },
            ].map(({ label, value, unit, icon: Icon }) => (
              <div key={label} className="bg-bg-elevated rounded-lg p-3 text-center">
                <p className="text-text-muted text-xs">{label}</p>
                <p className="text-text-primary font-semibold mt-1">{Math.round(value)}<span className="text-text-muted text-xs ml-1">{unit}</span></p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 7-day trend */}
      <div className="card">
        <h2 className="font-heading font-semibold text-lg mb-4">7-Day Calorie Trend</h2>
        <ResponsiveContainer width="100%" height={160}>
          <LineChart data={trend}>
            <XAxis dataKey="date" tick={{ fill: '#8B949E', fontSize: 11 }} tickFormatter={(d) => d.slice(5)} />
            <YAxis tick={{ fill: '#8B949E', fontSize: 11 }} width={45} />
            <Tooltip
              contentStyle={{ background: '#161B22', border: '1px solid #30363D', borderRadius: 8 }}
              labelStyle={{ color: '#8B949E' }}
              itemStyle={{ color: '#00D4AA' }}
            />
            <Line type="monotone" dataKey="calories" stroke="#00D4AA" strokeWidth={2} dot={{ fill: '#00D4AA', r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Today's meals */}
      <div className="card">
        <h2 className="font-heading font-semibold text-lg mb-3">Today's Meals</h2>
        {meals.length === 0 ? (
          <p className="text-text-muted text-sm py-4 text-center">No meals logged yet. <a href="/log" className="text-accent hover:underline">Log your first meal →</a></p>
        ) : (
          meals.map((m) => <MealCard key={m.id} meal={m} onDelete={handleDelete} />)
        )}
      </div>

      {/* Activity */}
      {activities.length > 0 && (
        <div className="card">
          <h2 className="font-heading font-semibold text-lg mb-3">Activity</h2>
          {activities.map((a) => (
            <div key={a.id} className="flex items-center justify-between py-2.5 border-b border-border last:border-0">
              <div className="flex items-center gap-2">
                <Footprints size={15} className="text-accent-warn" />
                <span className="text-text-primary capitalize">{a.activity_type}</span>
                {a.steps > 0 && <span className="text-text-muted text-sm">{a.steps.toLocaleString()} steps</span>}
              </div>
              <span className="text-accent-warn font-semibold">{Math.round(a.calories_burned)} kcal</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
