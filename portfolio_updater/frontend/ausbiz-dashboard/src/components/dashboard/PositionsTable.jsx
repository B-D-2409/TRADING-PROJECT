import { ArrowUpRight, ArrowDownRight } from 'lucide-react'
import { fmt } from '../../utils/formatters'

const HEADERS = [
  'Ticker', 'Name', 'Sector', 'Shares',
  'Entry Price', 'Current Price', 'Profit $', 'Profit %',
]

function ProfitBadge({ value, pct }) {
  const positive = value >= 0
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-full
                     ${positive
                        ? 'bg-emerald-400/10 text-emerald-400 border border-emerald-500/20'
                        : 'bg-rose-400/10 text-rose-400 border border-rose-500/20'}`}>
      {positive ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
      {Math.abs(pct).toFixed(2)}%
    </span>
  )
}

export default function PositionsTable({ positions }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-700/50">
            {HEADERS.map((h) => (
              <th key={h}
                  className="text-left text-xs font-semibold text-slate-500 uppercase
                             tracking-widest pb-3 pr-4 whitespace-nowrap">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-700/30">
          {positions?.map(({ ticker, name, sector, shares, entryPrice, currentPrice, profitDollar, profitPct }, i) => {
            const positive = profitDollar >= 0
            return (
              <tr key={i}
                  className="hover:bg-slate-700/30 transition-colors duration-150 cursor-default">
                <td className="py-3.5 pr-4">
                  <span className="font-bold text-white">{ticker}</span>
                </td>
                <td className="py-3.5 pr-4 text-slate-300 whitespace-nowrap">{name}</td>
                <td className="py-3.5 pr-4">
                  <span className="text-xs px-2 py-0.5 rounded-full bg-slate-700/50 text-slate-400
                                   border border-slate-600/30 whitespace-nowrap">
                    {sector}
                  </span>
                </td>
                <td className="py-3.5 pr-4 text-slate-300 tabular-nums">
                  {shares.toLocaleString()}
                </td>
                <td className="py-3.5 pr-4 text-slate-300 tabular-nums">
                  ${entryPrice.toFixed(2)}
                </td>
                <td className="py-3.5 pr-4 tabular-nums font-medium">
                  <span className={positive ? 'text-emerald-400' : 'text-rose-400'}>
                    ${currentPrice.toFixed(2)}
                  </span>
                </td>
                <td className="py-3.5 pr-4 font-semibold tabular-nums">
                  <span className={positive ? 'text-emerald-400' : 'text-rose-400'}>
                    {positive ? '+' : ''}{fmt.currency(profitDollar)}
                  </span>
                </td>
                <td className="py-3.5">
                  <ProfitBadge value={profitDollar} pct={profitPct} />
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
