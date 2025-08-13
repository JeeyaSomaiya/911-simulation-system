import React, { useRef, useEffect } from 'react';

const TranscriptDisplay = ({ conversation, isLive }) => {
  const transcriptRef = useRef(null);

  useEffect(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [conversation]);

  return (
    <div className="transcript-display">
      <div className="transcript-header">
        <h3>Live Transcript</h3>
        {isLive && <span className="live-indicator">🔴 LIVE</span>}
      </div>
      
      <div className="transcript-content" ref={transcriptRef}>
        {conversation.map((message, index) => (
          <div key={index} className={`message ${message.role}`}>
            <span className="role">
              {message.role === 'call_taker' ? 'Call Taker:' : 'Caller:'}
            </span>
            <span className="content">{message.content}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TranscriptDisplay;
