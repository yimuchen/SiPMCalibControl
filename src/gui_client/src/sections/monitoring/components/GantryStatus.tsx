import React, { useEffect } from 'react';

// import relevant types from utils/types.ts
import { TelemetryEntry } from '../../../session';

type Props = { telemetryLogs: TelemetryEntry[] };

const GantryStatus = ({ telemetryLogs }: Props) => {
  const [lastEntry, setLastEntry] = React.useState<TelemetryEntry | null>(null);

  useEffect(() => {
    if (telemetryLogs.length === 0) {
      setLastEntry(null);
    } else {
      setLastEntry(telemetryLogs[telemetryLogs.length - 1]);
    }
  }, [telemetryLogs]);

  return (
    <div>
      <h3>Gantry Status</h3>
      <div>
        {lastEntry ? (
          <span>
            Gantry Coordinates: ({lastEntry.gantry_coord[0].toFixed(1) || 'unknown'},
            {lastEntry.gantry_coord[1].toFixed(1) || 'unknown'},
            {lastEntry.gantry_coord[2].toFixed(1) || 'unknown'})
          </span>
        ) : (
          <p>Cannot be determined. Please check system status or try re-connecting.</p>
        )}
      </div>
    </div>
  );
};

export default GantryStatus;
