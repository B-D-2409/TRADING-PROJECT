export default function MainLayout({ children }) {
  return (
    <div
      className="min-h-screen bg-slate-950 text-white"
      style={{ background: 'radial-gradient(ellipse at top, #0f172a 0%, #020617 60%)' }}
    >
      {children}
    </div>
  )
}
