import { useState } from 'react'
import {
  Wallet, BarChart2, TrendingUp, TrendingDown,
  Activity, Bell, ArrowUpRight, ArrowDownRight,
  AlertTriangle, RefreshCw, LayoutDashboard, BookOpen,
} from 'lucide-react'

import { usePortfolio }      from './hooks/usePortfolio'
import { fmt }               from './utils/formatters'
import MainLayout            from './components/layout/MainLayout'
import Header                from './components/layout/Header'
import Footer                from './components/layout/Footer'
import KpiCard               from './components/dashboard/KpiCard'
import ReturnsBar            from './components/dashboard/ReturnsBar'
import EquityChart           from './components/dashboard/EquityChart'
import AlertsFeed            from './components/dashboard/AlertsFeed'
import PositionsTable        from './components/dashboard/PositionsTable'
import Button                from './components/common/Button'
import { Heading, SubText }  from './components/common/Typography'

const SUB_VIEWS = [
  { key: 'overview', label: 'Dashboard',               icon: LayoutDashboard },
  { key: 'holdings', label: 'Holdings & Fundamentals', icon: BookOpen        },
]

function LoadingScreen() {
  return (
    <MainLayout>
      <div className="flex-1 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-2 border-cyan-500/30 border-t-cyan-500
                          rounded-full animate-spin" />
          <p className="text-slate-400 text-sm">Loading portfolio data…</p>
        </div>
      </div>
    </MainLayout>
  )
}

function ErrorBanner({ error, onRetry }) {
  return (
    <div className="flex items-center gap-3 px-4 py-3 bg-rose-500/10 border border-rose-500/20
                    rounded-xl text-sm text-rose-400">
      <AlertTriangle className="w-4 h-4 flex-shrink-0" />
      <span className="flex-1">
        API unavailable — showing cached data.{' '}
        <span className="text-slate-500 text-xs">{error?.message}</span>
      </span>
      <Button variant="outline" size="sm" onClick={onRetry}>
        <RefreshCw className="w-3.5 h-3.5" /> Retry
      </Button>
    </div>
  )
}

function SubNav({ active, onChange }) {
  return (
    <div className="flex items-center gap-1 bg-slate-800/60 border border-slate-700/40
                    rounded-xl p-1 w-fit backdrop-blur-sm">
      {SUB_VIEWS.map(({ key, label, icon: Icon }) => (
        <button
          key={key}
          onClick={() => onChange(key)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium
                      transition-all duration-200
                      ${active === key
                        ? 'bg-gradient-to-r from-cyan-500/20 to-indigo-500/20 text-white border border-slate-600/50'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/40'}`}
        >
          <Icon className={`w-3.5 h-3.5 ${active === key ? 'text-cyan-400' : ''}`} />
          {label}
        </button>
      ))}
    </div>
  )
}

export default function App() {
  const [activeStrategy, setActiveStrategy] = useState('large_cap')
  const [activeView,     setActiveView]     = useState('overview')
  const { data, loading, error, refetch }   = usePortfolio(activeStrategy)

  if (loading && !data) return <LoadingScreen />

  const buyCount  = data.alerts.filter((a) => a.action === 'BUY').length
  const sellCount = data.alerts.filter((a) => a.action === 'SELL').length
  const winners   = data.positions.filter((p) => p.profitDollar >= 0).length
  const losers    = data.positions.filter((p) => p.profitDollar  < 0).length

  return (
    <MainLayout>
      <Header
        activeStrategy={activeStrategy}
        onStrategyChange={(s) => { setActiveStrategy(s); setActiveView('overview') }}
        universe={data.universe}
        lastUpdated={data.lastUpdated}
        onRefresh={refetch}
        loading={loading}
      />

      <main className="flex-1 max-w-screen-2xl mx-auto w-full px-6 py-8 space-y-6">
        {error && <ErrorBanner error={error} onRetry={refetch} />}

        {/* ── Section 1: Hero KPIs ── */}
        <section className="space-y-4">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard
              label="Portfolio Equity"
              value={fmt.currency(data.kpis.equity)}
              sub={`Cash: ${fmt.currency(data.kpis.cash)}`}
              icon={Wallet}
              accent="cyan"
            />
            <KpiCard
              label="Cash Balance"
              value={fmt.currency(data.kpis.cash)}
              sub={`${((data.kpis.cash / data.kpis.equity) * 100).toFixed(1)}% of portfolio`}
              icon={BarChart2}
              accent="amber"
            />
            <KpiCard
              label="Total Return"
              value={fmt.pct(data.kpis.totalReturn)}
              sub="Since inception"
              icon={TrendingUp}
              accent={data.kpis.totalReturn >= 0 ? 'emerald' : 'rose'}
              trend={data.kpis.totalReturn}
            />
            <KpiCard
              label="Max Drawdown"
              value={fmt.pct(data.kpis.maxDrawdown)}
              sub="Peak-to-trough"
              icon={TrendingDown}
              accent="rose"
              trend={data.kpis.maxDrawdown}
            />
          </div>

          <ReturnsBar returns={data.returns} />
        </section>

        {/* ── Sub-navigation ── */}
        <SubNav active={activeView} onChange={setActiveView} />

        {/* ── Section 2: Overview — Chart + Alerts ── */}
        {activeView === 'overview' && (
          <section className="grid grid-cols-3 gap-6 items-start">

            <div className="col-span-2 bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6
                            backdrop-blur-sm hover:border-slate-600/60 transition-colors duration-300">
              <div className="mb-5">
                <Heading>{data.label} — Equity Curve</Heading>
                <SubText>{data.universe} · 12-month performance vs benchmark</SubText>
              </div>
              <EquityChart
                data={data.equityCurve}
                includeIndex={true}
                height="h-72"
              />
            </div>

            <div className="col-span-1 bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6
                            backdrop-blur-sm hover:border-slate-600/60 transition-colors duration-300
                            flex flex-col" style={{ maxHeight: '26rem' }}>
              <div className="flex items-center justify-between mb-4 flex-shrink-0">
                <div>
                  <Heading className="flex items-center gap-2">
                    <Bell className="w-4 h-4 text-cyan-400" />
                    Weekly Alerts
                  </Heading>
                  <SubText>
                    {data.alerts.length} signal{data.alerts.length !== 1 ? 's' : ''} this week
                  </SubText>
                </div>
                <span className="text-xs font-bold px-2.5 py-1 rounded-full
                                 bg-cyan-400/10 text-cyan-400 border border-cyan-500/20 flex-shrink-0">
                  {buyCount} Buy · {sellCount} Sell
                </span>
              </div>

              <div className="flex-1 min-h-0 overflow-y-auto pr-0.5
                              [&::-webkit-scrollbar]:w-1
                              [&::-webkit-scrollbar-track]:bg-transparent
                              [&::-webkit-scrollbar-thumb]:bg-slate-600/60
                              [&::-webkit-scrollbar-thumb]:rounded-full
                              [&::-webkit-scrollbar-thumb:hover]:bg-slate-500">
                <AlertsFeed alerts={data.alerts} detailed={true} />
              </div>
            </div>

          </section>
        )}

        {/* ── Section 2: Holdings — Full-width Positions Table ── */}
        {activeView === 'holdings' && (
          <section className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6
                              backdrop-blur-sm hover:border-slate-600/60 transition-colors duration-300">
            <div className="flex items-center justify-between mb-6">
              <div>
                <Heading className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-cyan-400" />
                  Open Positions
                </Heading>
                <SubText>
                  {data.positions.length} active holding{data.positions.length !== 1 ? 's' : ''}
                  {' · '}fundamentals data included
                </SubText>
              </div>
              <div className="flex items-center gap-4 text-xs">
                <span className="flex items-center gap-1.5 text-emerald-400">
                  <ArrowUpRight className="w-3.5 h-3.5" />
                  {winners} winning
                </span>
                <span className="flex items-center gap-1.5 text-rose-400">
                  <ArrowDownRight className="w-3.5 h-3.5" />
                  {losers} losing
                </span>
              </div>
            </div>
            <PositionsTable positions={data.positions} detailed={true} />
          </section>
        )}

      </main>

      <Footer label={data.label} universe={data.universe} />
    </MainLayout>
  )
}
