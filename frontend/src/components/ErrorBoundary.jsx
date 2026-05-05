import { Component } from 'react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, info) {
    console.error('[ErrorBoundary]', error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-[60vh] items-center justify-center px-4">
          <div className="text-center">
            <div className="text-3xl mb-3">⚠️</div>
            <div className="text-sm font-semibold text-slate-700 mb-2">页面加载异常</div>
            <div className="text-xs text-slate-400 mb-4">{this.state.error?.message || '未知错误'}</div>
            <button
              onClick={() => { this.setState({ hasError: false }); window.location.reload() }}
              className="rounded-lg bg-blue-600 text-white text-sm font-semibold px-5 py-2">
              点击重试
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
