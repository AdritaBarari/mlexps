export default function CalorieRing({ caloriesIn, caloriesOut, goal }) {
  const size = 200
  const strokeWidth = 16
  const r = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * r
  const inPct = Math.min((caloriesIn / goal) * 100, 100)
  const outPct = Math.min((caloriesOut / goal) * 100, 100)
  const inOffset = circumference - (inPct / 100) * circumference
  const outOffset = circumference - (outPct / 100) * circumference
  const net = caloriesIn - caloriesOut
  const isOver = caloriesIn > goal

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90 block">
          {/* Track */}
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#21262D" strokeWidth={strokeWidth} />
          {/* Calories out (inner) */}
          <circle
            cx={size / 2} cy={size / 2} r={r - strokeWidth - 4}
            fill="none" stroke="#21262D" strokeWidth={strokeWidth - 4}
          />
          {/* Calories in arc */}
          <circle
            cx={size / 2} cy={size / 2} r={r}
            fill="none"
            stroke={isOver ? '#F85149' : '#00D4AA'}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={inOffset}
            strokeLinecap="round"
            className="transition-all duration-700"
          />
          {/* Calories out arc */}
          <circle
            cx={size / 2} cy={size / 2} r={r - strokeWidth - 4}
            fill="none"
            stroke="#F0A500"
            strokeWidth={strokeWidth - 4}
            strokeDasharray={circumference - (strokeWidth + 4) * 2 * Math.PI * 0}
            strokeDashoffset={outOffset}
            strokeLinecap="round"
            className="transition-all duration-700"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`font-heading font-bold text-3xl ${isOver ? 'text-accent-danger' : 'text-text-primary'}`}>
            {Math.round(caloriesIn)}
          </span>
          <span className="text-text-muted text-xs">of {goal} kcal</span>
          <span className={`text-xs mt-1 font-medium ${net > 0 ? 'text-accent-warn' : 'text-accent'}`}>
            net {Math.round(net)} kcal
          </span>
        </div>
      </div>
      <div className="flex gap-5 text-xs text-text-muted">
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-accent inline-block" /> Intake
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-accent-warn inline-block" /> Burned
        </span>
      </div>
    </div>
  )
}
