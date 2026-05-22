import { AlertTriangle, XCircle } from 'lucide-react'

export default function AlertBanner({ caloriePct }) {
  if (caloriePct < 90) return null

  const isOver = caloriePct >= 100
  return (
    <div
      className={`flex items-center gap-3 px-4 py-3 rounded-xl border mb-4 ${
        isOver
          ? 'bg-accent-danger/10 border-accent-danger/30 text-accent-danger'
          : 'bg-accent-warn/10 border-accent-warn/30 text-accent-warn'
      }`}
    >
      {isOver ? <XCircle size={18} /> : <AlertTriangle size={18} />}
      <span className="font-medium text-sm">
        {isOver
          ? `You've exceeded your daily calorie goal by ${Math.round(caloriePct - 100)}%`
          : `You're at ${Math.round(caloriePct)}% of your daily calorie goal`}
      </span>
    </div>
  )
}
