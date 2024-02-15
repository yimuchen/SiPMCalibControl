import { TempMonitorStatus, VoltMonitorStatus } from './components/TelemetryData';
import VisualSystem from './components/VisualSystem';
import GantryStatus from './components/GantryStatus';
import ActionStatusDisplay from './components/ActionStatus';
import HardwareStatus from './components/HardwareStatus';

const SystemStatus = () => {
  return (
    <div>
      <h2>System status</h2>
      <div className='tablediv'>
        <div className='tbrowdiv'>
          <div className='tbcelldiv statusHeaderOuter'>
            <div className='statusHeaderMid'>
              <div className='statusHeader'>Hardware status</div>
            </div>
          </div>
          <div className='tbcelldiv'>
            <HardwareStatus />
          </div>
        </div>
        <div className='tbrowdiv'>
          <div className='tbcelldiv statusHeaderOuter'>
            <div className='statusHeaderMid'>
              <div className='statusHeader'>Actions</div>
            </div>
          </div>
          <div className='tbcelldiv'>
            <ActionStatusDisplay />
          </div>
        </div>
        <div className='tbrowdiv'>
          <div className='tbcelldiv statusHeaderOuter'>
            <div className='statusHeaderMid'>
              <div className='statusHeader'>Gantry</div>
            </div>
          </div>
          <div className='tbcelldiv'>
            <GantryStatus />
          </div>
        </div>
        <div className='tbrowdiv'>
          <div className='tbcelldiv statusHeaderOuter'>
            <div className='statusHeaderMid'>
              <div className='statusHeader'>Temperature</div>
            </div>
          </div>
          <div className='tbcelldiv'>
            <TempMonitorStatus />
          </div>
        </div>
        <div className='tbrowdiv'>
          <div className='tbcelldiv statusHeaderOuter'>
            <div className='statusHeaderMid'>
              <div className='statusHeader'>Voltages</div>
            </div>
          </div>
          <div className='tbcelldiv'>
            <VoltMonitorStatus />
          </div>
        </div>
        <div className='tbrowdiv'>
          <div className='tbcelldiv statusHeaderOuter'>
            <div className='statusHeaderMid'>
              <div className='statusHeader'>Visual</div>
            </div>
          </div>
          <div className='tbcelldiv'>
            <VisualSystem />
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemStatus;
