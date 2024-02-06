import { useGlobalSession, TelemetryEntry } from '../../session';

import TelemetryData from './components/TelemetryData';
import VisualSystem from './components/VisualSystem';
import GantryStatus from './components/GantryStatus';
import ActionStatus from './components/ActionStatus';
import { useEffect } from 'react';


const Monitoring = () => {
  const { telemetryLogs } = useGlobalSession();


  return (
    <div>
      <h2>Monitoring</h2>
      <ActionStatus />
      <GantryStatus telemetryLogs={telemetryLogs} />
      <TelemetryData
        telemetryLogs={telemetryLogs}
      // telemetry_max_length={telemetry_max_length}
      />
      <VisualSystem />
    </div>
  );
};

export default Monitoring;
