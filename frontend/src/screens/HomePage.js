import React from 'react';
import { useNavigate } from 'react-router-dom';
import StatsCard from '../components/features/dashboard/StatsCard';
import AssignmentsSection from '../components/features/dashboard/AssignmentsSection';
import HistorySection from '../components/features/dashboard/HistorySection';
import CallButton from '../components/features/call/CallButton';
import { useCallHistory } from '../hooks/useCallHistory';

const HomePage = () => {
  const navigate = useNavigate();
  const { callHistory, assignments } = useCallHistory();

  const handleSimulateCall = () => {
    navigate('/new-call');
  };

  return (
    <div className="homepage">
      <div className="stats-container">
        <StatsCard
          title="Calls"
          value={callHistory.length}
          subtitle="Complete"
        />
        <StatsCard
          title="Complete Assignments"
          value={assignments.length}
          subtitle=""
        />
      </div>

      <div className="cta-section">
        <CallButton
          onClick={handleSimulateCall}
          text="Simulate Call"
          variant="primary"
        />
      </div>

      <div className="sections-container">
        <AssignmentsSection assignments={assignments} />
        <HistorySection history={callHistory} />
      </div>
    </div>
  );
};

export default HomePage;
