// React implemented modules
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';

// Custom modules
import { useGlobalSession } from '../../../session';
import { ActionSubmit, SubmitActionRequest } from '../../../utils/common';

const HardwareStatus = () => {
  return (
    <div className='tablediv'>
      <ActionInterupt />
      <GMQStatus />
      <TBTesterStatus />
    </div>
  );
};

const ActionInterupt = () => {
  const { actionLogs, socketInstance } = useGlobalSession();
  const [disabled, setDisabled] = useState<boolean>(true);
  const { handleSubmit } = useForm();

  const onSubmit = (data: any) => {
    if (socketInstance) {
      socketInstance.emit('user-interupt');
    }
  };

  useEffect(() => {
    if (actionLogs.length === 0) {
      return;
    }
    const lastAction = actionLogs.slice(-1)[0];
    if (lastAction.log.length === 0) {
      return;
    }
    const lastStatus = lastAction.log.slice(-1)[0].status;
    console.log(lastStatus);
    setDisabled(!(lastStatus === 1 || lastStatus === 3));
  }, [actionLogs]);

  return (
    <div className='tbrowdiv statusSubRow'>
      <div className='tbcelldiv statusSubHeader'>
        <b>System Interupt</b>
      </div>
      <div className='tbcelldiv'>
        <form onSubmit={handleSubmit(onSubmit)}>
          <input disabled={disabled} style={{ width: '100%' }} type='submit' value='  🗲  ' />
        </form>
      </div>
    </div>
  );
};

const GMQStatus = () => {
  const { hardwareStatus } = useGlobalSession();
  return (
    <div className='tbrowdiv statusSubRow'>
      <div className='tbcelldiv statusSubHeader'>
        <b>GMQ status</b>
        <br />
        {hardwareStatus.gantryHW === null ? 'Not available' : '🌐' + hardwareStatus.gantryHW}
        <br />
        {hardwareStatus.gantryHW === null ? <></> : <GMQDisconnect />}
      </div>
      <div className='tbcelldiv'>
        <GMQMakeConnection />
      </div>
    </div>
  );
};

const GMQMakeConnection = () => {
  const { socketInstance } = useGlobalSession();
  const { register, handleSubmit } = useForm();

  const submitConnection = (data: any) => {
    SubmitActionRequest(socketInstance, 'gmq_connect', data);
  };
  return (
    <form onSubmit={handleSubmit(submitConnection)}>
      <div className='tablediv'>
        <div className='tbrowdiv'>
          <div className='tbcelldiv'>Host:</div>
          <div className='tbcelldiv'>
            <input {...register('host')} />
          </div>
        </div>
        <div className='tbrowdiv'>
          <div className='tbcelldiv'>Port:</div>
          <div className='tbcelldiv'>
            <input {...register('port')} />
          </div>
        </div>
        <div className='tbrowdiv'>
          <div className='tbcelldiv'></div>
          <div className='tbcelldiv'>
            <ActionSubmit value='Connect to GMQ' />
          </div>
        </div>
      </div>
    </form>
  );
};

const GMQDisconnect = () => {
  const { socketInstance } = useGlobalSession();
  const { handleSubmit } = useForm();
  const submitDisconnect = (data: any) => {
    SubmitActionRequest(socketInstance, 'gmq_disconnect', data);
  };
  return (
    <form onSubmit={handleSubmit(submitDisconnect)}>
      <ActionSubmit value='Disconnect from GMQ' key='disconnect' />
    </form>
  );
};

const TBTesterStatus = () => {
  const { hardwareStatus } = useGlobalSession();
  return (
    <div className='tbrowdiv statusSubRow'>
      <div className='tbcelldiv statusSubHeader'>
        <b>Tileboard tester</b>
        <br />
        {hardwareStatus.tileboardHW === null ? 'Not available' : '🌐' + hardwareStatus.gantryHW}
        <br />
        {hardwareStatus.tileboardHW === null ? <></> : <TBTesterDisconnect />}
      </div>
      <div className='tbcelldiv'>
        <TBTesterMakeConnection />
      </div>
    </div>
  );
};

const TBTesterMakeConnection = () => {
  const { socketInstance } = useGlobalSession();
  const { register, handleSubmit } = useForm();

  const submitConnection = (data: any) => {
    SubmitActionRequest(socketInstance, 'tbtester_connect', data);
  };

  return (
    <form onSubmit={handleSubmit(submitConnection)}>
      <div className='tablediv'>
        <div className='tbrowdiv'>
          <div className='tbcelldiv textRight'>Data port:</div>
          <div className='tbcelldiv textLeft'>
            <input {...register('dataport')} />
          </div>
        </div>
        <div className='tbrowdiv'>
          <div className='tbcelldiv textRight'>TBTester IP:</div>
          <div className='tbcelldiv textLeft'>
            <input {...register('tbtester_ip')} />
          </div>
        </div>
        <div className='tbrowdiv'>
          <div className='tbcelldiv textRight'>Fast control port:</div>
          <div className='tbcelldiv textLeft'>
            <input {...register('fastport')} />
          </div>
        </div>
        <div className='tbrowdiv'>
          <div className='tbcelldiv textRight'>I2C control port:</div>
          <div className='tbcelldiv textLeft'>
            <input {...register('i2cport')} />
          </div>
        </div>
        <div className='tbrowdiv'>
          <div className='tbcelldiv' />
          <div className='tbcelldiv'>
            <ActionSubmit value='Connect to tester' key='tbtester_connect' />
          </div>
        </div>
      </div>
    </form>
  );
};

const TBTesterDisconnect = () => {
  const { socketInstance } = useGlobalSession();
  const { handleSubmit } = useForm();
  const submitDisconnect = (data: any) => {
    SubmitActionRequest(socketInstance, 'tbtester_disconnect', data);
  };
  return (
    <form onSubmit={handleSubmit(submitDisconnect)}>
      <ActionSubmit value='Disconnect tester' key='tbtester_disconnect' />
    </form>
  );
};

export default HardwareStatus;
