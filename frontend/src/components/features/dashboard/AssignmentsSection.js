import React from 'react';

const AssignmentsSection = ({ assignments = [] }) => {
  return (
    <div className="assignments-section card">
      <h3>Assignments</h3>
      {assignments.length === 0 ? (
        <p className="empty-state">No assignments found</p>
      ) : (
        <div className="assignments-list">
          {assignments.map((assignment, index) => (
            <div key={index} className="assignment-item">
              {assignment.title}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AssignmentsSection;
