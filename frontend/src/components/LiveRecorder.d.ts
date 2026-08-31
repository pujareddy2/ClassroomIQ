import React from 'react'

export interface LiveRecorderProps {
  onSessionCreated?: (sessionData: Record<string, unknown>) => void
}

declare const LiveRecorder: React.FC<LiveRecorderProps>
export default LiveRecorder
