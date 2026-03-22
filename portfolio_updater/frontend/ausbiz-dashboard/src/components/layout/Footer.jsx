export default function Footer({ label, universe }) {
  return (
    <footer className="border-t border-slate-800/60 mt-8 py-6">
      <div className="max-w-screen-2xl mx-auto px-6 flex items-center justify-between">
        <p className="text-slate-600 text-xs">
          AusBiz Portfolio Engine · {label} Strategy · {universe}
        </p>
        <p className="text-slate-700 text-xs">Not financial advice. For internal use only.</p>
      </div>
    </footer>
  )
}
