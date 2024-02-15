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
  }, [telemetryLogs]);

  const moveGantry = (data: any) => {
    SubmitActionRequest(socketInstance, 'gantry_move_to', {
      x: Number(data.x),
      y: Number(data.y),
      z: Number(data.z),
    });
  };

  return (
    <div className='tablediv'>
      <div className='tbrowdiv'>
        <div className='tbcelldiv' style={{ maxWidth: '200px' }}>
          <b>Coordinate</b>
          <br />
          {statusString}
        </div>
        <div className='tbcelldiv'>
          {gantryAvailable ? (
            <div>
              <form onSubmit={handleSubmit(moveGantry)}>
                x:
                <input {...register('x')} style={{ width: '5em' }} />
                y:
                <input {...register('y')} style={{ width: '5em' }} />
                z:
                <input {...register('z')} style={{ width: '5em' }} />
                <br />
                <ActionSubmit value='move gantry' key='move-gantry' />
              </form>
            </div>
          ) : (
            <></>
          )}
        </div>
      </div>
    </div>
  );
};

export default GantryStatus;
