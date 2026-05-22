import { Trash2 } from 'lucide-react'

const mealColors = {
  breakfast: '#F0A500',
  lunch: '#00D4AA',
  dinner: '#7C6AF7',
  snack: '#F85149',
  meal: '#8B949E',
}

export default function MealCard({ meal, onDelete }) {
  const color = mealColors[meal.meal_type] || '#8B949E'
  return (
    <div className="flex items-center justify-between py-3 border-b border-border last:border-0">
      <div className="flex items-center gap-3 min-w-0">
        <span
          className="w-2 h-8 rounded-full flex-shrink-0"
          style={{ backgroundColor: color }}
        />
        <div className="min-w-0">
          <p className="text-text-primary font-medium truncate">{meal.food_name}</p>
          <p className="text-text-muted text-xs mt-0.5">
            {meal.quantity} · {meal.meal_type}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-3 flex-shrink-0 ml-3">
        <div className="text-right">
          <p className="text-text-primary font-semibold">{Math.round(meal.calories)} kcal</p>
          <p className="text-text-muted text-xs">P:{Math.round(meal.protein)}g C:{Math.round(meal.carbs)}g F:{Math.round(meal.fat)}g</p>
        </div>
        {onDelete && (
          <button
            onClick={() => onDelete(meal.id)}
            className="text-text-muted hover:text-accent-danger transition-colors p-1"
          >
            <Trash2 size={14} />
          </button>
        )}
      </div>
    </div>
  )
}
