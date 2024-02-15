// React implemented modules
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';

// Custom modules
import { ActionEntry, ActionStatus, useGlobalSession } from '../../../session';
import { ActionSubmit, SubmitActionRequest } from '../../../utils/common';
import { statusIntToString, timestampString, statusIntToShortString } from '../../../utils/format';

const ActionStatusDisplay = () => {
  // Main data container
  const [showFull, setShowFull] = useState<boolean>(false);

  return (
    <>
      <ActionSummary showFull={showFull} setShowFull={setShowFull} />
      <FullActionLog showFull={showFull} setShowFull={setShowFull} />
    </>
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
    <div className='tablediv'>
      <div className='tbrowdiv'>
        <div className='tbcelldiv'>
          <b>Current status</b>
        </div>
        <div className='tbcelldiv'>{sessionState}</div>
      </div>
      <div className='tbrowdiv'>
        <div className='tbcelldiv'>
          <b>Last action</b>
        </div>
        <div className='tbcelldiv'>{sessionAction}</div>
      </div>
      <div className='tbrowdiv'>
        <div className='tbcelldiv'>
          <b>Last update </b>
        </div>
        <div className='tbcelldiv'>{updateTime}</div>
      </div>
      {progNum != null && progTot != null ? (
        <div className='tbrowdiv'>
          <div className='tbcelldiv'>
            <b>Progress </b>
          </div>
          <div className='tbcelldiv'>
            <ProgressBar num={progNum} total={progTot} />
          </div>
        </div>
      ) : (
        <> </>
      )}
      <div className='tbrowdiv'>
        <div className='tbcelldiv' />
        <div className='tbcelldiv'>
          <button onClick={showLog}>Show full log</button>
        </div>
      </div>
    </div>
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

export default ActionStatusDisplay;
