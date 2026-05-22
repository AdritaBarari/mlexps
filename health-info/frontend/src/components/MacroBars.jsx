function Bar({ label, value, goal, color }) {
  const pct = Math.min((value / goal) * 100, 100)
  const isOver = value > goal
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="text-text-muted font-medium">{label}</span>
        <span className={isOver ? 'text-accent-danger font-semibold' : 'text-text-primary'}>
          {Math.round(value)}g <span className="text-text-muted font-normal">/ {goal}g</span>
        </span>
      </div>
      <div className="h-2 bg-bg-elevated rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, backgroundColor: isOver ? '#F85149' : color }}
        />
      </div>
    </div>
  )
}

export default function MacroBars({ macros, goals }) {
  return (
    <div className="space-y-3.5">
      <Bar label="Protein" value={macros.protein} goal={goals.protein} color="#00D4AA" />
      <Bar label="Carbs" value={macros.carbs} goal={goals.carbs} color="#7C6AF7" />
      <Bar label="Fat" value={macros.fat} goal={goals.fat} color="#F0A500" />
    </div>
  )
}
