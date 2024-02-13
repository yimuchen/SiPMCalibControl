// React implemented modules
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';

// Custom modules
import { ActionEntry, ActionStatus, useGlobalSession } from '../../../session';
import { ActionSubmit, SubmitActionRequest } from '../../../utils/common';
import { statusIntToString, timestampString, statusIntToShortString } from '../../../utils/format';

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
    <tr>
      <td>
        <b>System Interupt</b>
      </td>
      <td>
        <form onSubmit={handleSubmit(onSubmit)}>
          <input disabled={disabled} style={{ width: '80%' }} type='submit' value='  🗲  ' />
        </form>
      </td>
    </tr>
  );
};

const GMQStatus = () => {
  const { hardwareStatus } = useGlobalSession();
  return (
    <tr>
      <td>
        <b>GMQ status</b>
        <br />
        {hardwareStatus.gantryHW === null ? 'Not available' : '🌐' + hardwareStatus.gantryHW}
        <br />
        {hardwareStatus.gantryHW === null ? <></> : <GMQDisconnect />}
      </td>
      <td>
        <GMQMakeConnection />
      </td>
    </tr>
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
      <table>
        <tr>
          <td>Host:</td>
          <td>
            <input {...register('host')} />
          </td>
        </tr>
        <tr>
          <td>Port</td>
          <td>
            <input {...register('port')} />
          </td>
        </tr>
        <tr>
          <td></td>
          <td>
            <ActionSubmit value='Connect to GMQ' />
          </td>
        </tr>
      </table>
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
    <tr>
      <td>
        <b>Tileboard tester</b>
        <br />
        {hardwareStatus.tileboardHW === null ? 'Not available' : '🌐' + hardwareStatus.gantryHW}
        <br />
        {hardwareStatus.tileboardHW === null ? <></> : <TBTesterDisconnect />}
      </td>
      <td>
        <TBTesterMakeConnection />
      </td>
    </tr>
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
      <table>
        <tr>
          <td>Data port</td>
          <td>
            <input {...register('dataport')} />
          </td>
        </tr>
        <tr>
          <td>TBTester IP</td>
          <td>
            <input {...register('tbtester_ip')} />
          </td>
        </tr>
        <tr>
          <td>Fast control port</td>
          <td>
            <input {...register('fastport')} />
          </td>
        </tr>
        <tr>
          <td>I2C control port</td>
          <td>
            <input {...register('i2cport')} />
          </td>
        </tr>
        <tr>
          <td></td>
          <td>
            <ActionSubmit value='Connect to tester' key='tbtester_connect' />
          </td>
        </tr>
      </table>
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

type FullShowProp = {
  showFull: boolean;
  setShowFull: (c: boolean) => void;
};
const ActionSummary = ({ showFull, setShowFull }: FullShowProp) => {
  const { actionLogs } = useGlobalSession();
  // Extended data for display purposes
  const [sessionState, setSessionState] = useState<string>('');
  const [sessionAction, setSessionAction] = useState<string>('');
  const [updateTime, setUpdateTime] = useState<string>('');
  const [progNum, setProgNum] = useState<number | null>(null);
  const [progTot, setProgTot] = useState<number | null>(null);

  useEffect(() => {
    if (actionLogs.length > 0) {
      const lastAction = actionLogs.slice(-1)[0];
      setSessionState(statusIntToString(lastAction.log.slice(-1)[0].status));
      setSessionAction(lastAction.name);
      setUpdateTime(timestampString(lastAction.log.slice(-1)[0].timestamp));
      setProgNum(lastAction.progress[0]);
      setProgTot(lastAction.progress[1]);
    } else {
      setSessionState('System status cannot be determined');
      setProgNum(null);
      setProgTot(null);
    }
  }, [actionLogs]);

  const showLog = () => {
    setShowFull(true);
  };
  return (
    <>
      <tr>
        <td>
          <b>Action status</b>
        </td>{' '}
        <td>{sessionState}</td>
      </tr>
      <tr>
        <td>
          <b>Last action</b>
        </td>{' '}
        <td>{sessionAction}</td>
      </tr>
      <tr>
        <td>
          <b>Last update</b>
        </td>{' '}
        <td>{updateTime}</td>
      </tr>
      {progNum != null && progTot != null ? (
        <tr>
          <td>
            <b>Progress</b>
          </td>
          <td>
            <ProgressBar num={progNum} total={progTot} />
          </td>
        </tr>
      ) : (
        <tr />
      )}
      <tr>
        <td></td>
        <td>
          <button onClick={showLog}>Show action log</button>
        </td>
      </tr>
    </>
  );
};

/**
 * Commonly used progress bars!
 **/
type PBarProp = {
  num: number;
  total: number;
};
const ProgressBar = ({ num, total }: PBarProp) => {
  const completed = (100 * num) / total;
  const containerStyles = {
    height: '20px',
    width: '100%',
    backgroundColor: '#e0e0de',
    borderRadius: 50,
  };

  const fillerStyles = {
    height: '100%',
    width: `${completed}%`,
    backgroundColor: '#00EE00',
    //borderRadius: 'inherit',
    //textAlign: 'right'
  };

  const labelStyles = {
    padding: 5,
    color: 'black',
    fontWeight: 'bold',
  };
  return (
    <span>
      <div style={containerStyles}>
        <div style={fillerStyles} />
        <span style={labelStyles}>{`${completed.toFixed(1)}% (${num}/${total})`}</span>
      </div>
    </span>
  );
};

//

const FullActionLog = ({ showFull, setShowFull }: FullShowProp) => {
  const { actionLogs } = useGlobalSession();

  if (!showFull) return <></>; // Empty is property is set to false

  const createRow = (entry: ActionEntry) => {
    const createStatusRow = (status: ActionStatus, index: number) => {
      const tab_sty = { padding: '10px 3px' };
      if (index === 0) {
        return (
          <tr>
            <td style={tab_sty} rowSpan={entry.log.length}>
              {entry.name}
            </td>
            <td style={tab_sty} rowSpan={entry.log.length}>
              {JSON.stringify(entry.args)}
            </td>
            <td style={tab_sty}>{statusIntToShortString(status.status)}</td>
            <td style={tab_sty}>{timestampString(status.timestamp)}</td>
          </tr>
        );
      } else {
        return (
          <tr>
            <td style={tab_sty}>{statusIntToShortString(status.status)}</td>
            <td style={tab_sty}>{timestampString(status.timestamp)}</td>
          </tr>
        );
      }
    };

    return <>{entry.log.map(createStatusRow)}</>;
  };

  const cont_sty = { backgroundColor: '#CCCCCC' };
  const closeFloat = () => {
    setShowFull(false);
  };

  return (
    <div style={cont_sty} className='overlayFloat'>
      <h3 className='header'>Full action Log</h3>
      <button className='floatClose' onClick={closeFloat}>
        x
      </button>
      <a href='download/json/actionLog' download>
        Download JSON
      </a>
      <div className='floatContent'>
        <table className='hcentering'>
          <tr>
            <th>Action name</th>
            <th>arguments</th>
            <th>status</th>
            <th>status timestamp</th>
          </tr>
          {actionLogs.map(createRow)}
        </table>
      </div>
    </div>
  );
};

//** Main container objects
const SystemStatus = () => {
  // Main data container
  const [showFull, setShowFull] = useState<boolean>(false);

  return (
    <div>
      <h3>Main System Status</h3>
      <table>
        <ActionInterupt />
        <GMQStatus />
        <TBTesterStatus />
        <ActionSummary showFull={showFull} setShowFull={setShowFull} />
        <FullActionLog showFull={showFull} setShowFull={setShowFull} />
      </table>
    </div>
  );
};

export default SystemStatus;
