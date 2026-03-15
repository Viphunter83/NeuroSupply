"use client"

import * as React from "react"

export function useToast() {
  const [toasts, setToasts] = React.useState([])

  const toast = React.useCallback(({ title, description, variant }: { title?: string, description?: string, variant?: string }) => {
    console.log(`[Toast] ${variant}: ${title} - ${description}`)
    // Simplified implementation for the build
  }, [])

  return {
    toast,
    toasts
  }
}
