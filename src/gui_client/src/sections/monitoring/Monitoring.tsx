import { useGlobalSession } from '../../session';

import { TempMonitorStatus, VoltMonitorStatus } from './components/TelemetryData';
import VisualSystem from './components/VisualSystem';
import GantryStatus from './components/GantryStatus';
import ActionStatus from './components/ActionStatus';
import MessageStatus from './components/MessageStatus';

const Monitoring = () => {
  return (
    <div>
      <h2>Monitoring</h2>
      <ActionStatus />
      <GantryStatus />
      <TempMonitorStatus />
      <VoltMonitorStatus />
      <VisualSystem />
      <MessageStatus />
    </div>
  );
};

export default Monitoring;
