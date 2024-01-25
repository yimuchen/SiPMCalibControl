import { useGlobalSession, TelemetryEntry } from '../../session';

import TelemetryData from './components/TelemetryData';
import VisualSystem from './components/VisualSystem';
import GantryStatus from './components/GantryStatus';
import SystemStatus from './components/SystemStatus';
import { useEffect } from 'react';


const Monitoring = () => {
  const { socketInstance, telemetryLogs, setTelemetryLogs } = useGlobalSession();

  // Defining all the client-server interaction commont to the monitoring status here
  useEffect(() => {
    if (socketInstance) {
      socketInstance.on('update-session-telemetry', update_telemetry_entry);
    }
  }, [socketInstance, telemetryLogs]);

  // Update function needs to be declared separately
  const update_telemetry_entry = (data: TelemetryEntry[]) => { setTelemetryLogs(data); }

  return (
    <div>
      <h2>Monitoring</h2>
      <SystemStatus />
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
