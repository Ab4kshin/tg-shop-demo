import { Component } from "react"
import type { CSSProperties, ErrorInfo, ReactNode } from "react"

interface Props {
  children: ReactNode
}

interface State {
  error: Error | null
}

const wrapStyle: CSSProperties = {
  padding: 16,
  fontFamily: "system-ui, -apple-system, sans-serif",
}
const titleStyle: CSSProperties = { color: "#e5484d", margin: "0 0 8px" }
const hintStyle: CSSProperties = { color: "#8e8e93", fontSize: 14, margin: "0 0 8px" }
const preStyle: CSSProperties = {
  whiteSpace: "pre-wrap",
  wordBreak: "break-word",
  fontSize: 12,
  background: "rgba(127,127,127,0.15)",
  padding: 12,
  borderRadius: 8,
}

// Ловит ошибки рендера и показывает текст вместо пустой страницы.
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("Mini App crashed:", error, info)
  }

  render(): ReactNode {
    const err = this.state.error
    if (err) {
      return (
        <div style={wrapStyle}>
          <h2 style={titleStyle}>Мини-аппка не загрузилась</h2>
          <p style={hintStyle}>Покажите этот текст разработчику:</p>
          <pre style={preStyle}>{String(err.stack || err.message || err)}</pre>
        </div>
      )
    }
    return this.props.children
  }
}
