export default function LoadingSpinner({ text = 'AI 正在分析中...' }) {
  return (
    <div className="wechat-card mb-3 p-8 text-center">
      <div className="mb-4 flex justify-center gap-2">
        <div className="pulse-dot h-3 w-3 rounded-full bg-blue-600" />
        <div className="pulse-dot h-3 w-3 rounded-full bg-blue-600" />
        <div className="pulse-dot h-3 w-3 rounded-full bg-blue-600" />
      </div>
      <p className="text-sm text-slate-500">{text}</p>
    </div>
  )
}
