import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';

// import relevant types from utils/types.ts
import { useGlobalSession } from '../../../session';
import { ActionSubmit, SubmitActionRequest } from '../../../utils/common';

const GantryStatus = () => {
  const { socketInstance, telemetryLogs } = useGlobalSession();
  const { register, handleSubmit } = useForm();
  const [statusString, setStatusString] = useState<string>('');
  const [gantryAvailable, setAvailable] = useState<boolean>(false);

  useEffect(() => {
    if (telemetryLogs.length === 0) {
      setStatusString('Cannot determined (cannot connect to session)');
      setAvailable(false);
    } else {
      const lastRecord = telemetryLogs[telemetryLogs.length - 1].gantry_coord.map((x) => Number(x));
      if (lastRecord.includes(Number.NaN)) {
        setStatusString('Gantry is not available. Make sure the GantryMQ is connect if needed.');
        setAvailable(false);
      } else {
        setAvailable(true);
        setStatusString(
          '(' +
            Number(lastRecord[0]).toFixed(1) +
            ', ' +
            Number(lastRecord[1]).toFixed(1) +
            ', ' +
            Number(lastRecord[2]).toFixed(1) +
            ')',
        );
      }
    }
    console.log('Gantry available', gantryAvailable);
  }, [telemetryLogs]);

  const moveGantry = (data: any) => {
    SubmitActionRequest(socketInstance, 'gantry_move_to', {
      x: Number(data.x),
      y: Number(data.y),
      z: Number(data.z),
    });
  };

  return (
    <div>
      <h3>Subsystem - Gantry Status</h3>
      <div>
        <table>
          <tr>
            <td>Gantry coordinate</td>
            <td>{statusString}</td>
          </tr>
          {gantryAvailable ? (
            <tr>
              <td></td>
              <td>
                <form onSubmit={handleSubmit(moveGantry)}>
                  <table>
                    <tr>
                      <td>x:</td>
                      <input {...register('x')} />
                    </tr>
                    <tr>
                      <td>y:</td>
                      <td>
                        <input {...register('y')} />
                      </td>
                    </tr>
                    <tr>
                      <td>z:</td>
                      <td>
                        <input {...register('z')} />
                      </td>
                    </tr>
                    <tr>
                      <td></td>
                      <td>
                        <ActionSubmit value='move gantry' key='move-gantry' />
                      </td>
                    </tr>
                  </table>
                </form>
              </td>
            </tr>
          ) : (
            <></>
          )}
        </table>
      </div>
    </div>
  );
};

export default GantryStatus;
