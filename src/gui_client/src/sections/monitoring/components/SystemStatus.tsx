import React from 'react';
import { useGlobalSession } from '../../../session';

type Props = {};

const SystemStatus = (props: Props) => {
  const { sessionState } = useGlobalSession();

  return (
    <div>
      <h3>System Status</h3>
      <span>System Status: {sessionState || 'System status cannot be determined.'}</span>
    </div>
  );
};

export default SystemStatus;
