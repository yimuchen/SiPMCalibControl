import { useEffect, useState } from 'react';
import { ActionEntry, ActionStatus, useGlobalSession } from '../../../session';

import { statusIntToString, timestampString, statusIntToShortString } from '../../../utils/format';

//** Main container objects
const SystemStatus = () => {
  // Main data container
  const { actionLogs } = useGlobalSession();

  // Extended data for display purposes
  const [sessionState, setSessionState] = useState<string>("");
  const [sessionAction, setSessionAction] = useState<string>("");
  const [updateTime, setUpdateTime] = useState<string>("");
  const [progNum, setProgNum] = useState<number | null>(null);
  const [progTot, setProgTot] = useState<number | null>(null);
  const [fullLogShow, setFullLogShow] = useState<boolean>(false);

  useEffect(() => {
    if (actionLogs.length > 0) {
      const lastAction = actionLogs.slice(-1)[0];
      setSessionState(statusIntToString(lastAction.log.slice(-1)[0].status));
      setSessionAction(lastAction.name);
      setUpdateTime(timestampString(lastAction.log.slice(-1)[0].timestamp));
      setProgNum(lastAction.progress[0]);
      setProgTot(lastAction.progress[1]);
    } else {
      setSessionState("System status cannot be determined");
      setProgNum(null);
      setProgTot(null);
    }
  }, [actionLogs])

  const showFullActionLog = () => { setFullLogShow(true); }


  return (
    <div>
      <h3>System Status</h3>
      <table>
        <tr>
          <td>Current status</td> <td>{sessionState}</td>
        </tr>
        <tr>
          <td>Last action</td> <td>{sessionAction}</td>
        </tr>
        <tr>
          <td>Last update</td> <td>{updateTime}</td>
        </tr>
        {
          (progNum != null && progTot != null)
            ? <tr>
              <td>Progress</td>
              <td><ProgressBar num={progNum} total={progTot} /></td>
            </tr>
            : <tr />
        }
      </table>
      <button onClick={showFullActionLog}>Show full log</button>
      <FullActionLog show={fullLogShow} setShow={setFullLogShow} />
    </div>
  );
};

export default SystemStatus;


/**
 * Commonly used progress bars!
 **/
type PBarProp = {
  num: number,
  total: number,
};
const ProgressBar = ({ num, total }: PBarProp) => {
  const completed = 100 * num / total;
  const containerStyles = {
    height: '20px',
    width: '100%',
    backgroundColor: "#e0e0de",
    borderRadius: 50,
  }

  const fillerStyles = {
    height: '100%',
    width: `${completed}%`,
    backgroundColor: '#00EE00',
    //borderRadius: 'inherit',
    //textAlign: 'right'
  }

  const labelStyles = {
    padding: 5,
    color: 'black',
    fontWeight: 'bold'
  }
  return <span>
    <div style={containerStyles}>
      <div style={fillerStyles} />
      <span style={labelStyles}>{`${completed.toFixed(1)}% (${num}/${total})`}</span>
    </div>
  </span>
}

//
type FullActionLogProp = {
  show: boolean;
  setShow: (c: boolean) => void;
};
const FullActionLog = ({ show, setShow }: FullActionLogProp) => {
  const { actionLogs } = useGlobalSession();

  if (!show) return (<></>);// Empty is property is set to false

  const createRow = (entry: ActionEntry) => {
    const createStatusRow = (status: ActionStatus, index: number) => {
      const tab_sty = { padding: '10px 3px' }
      if (index === 0) {
        return (
          <tr>
            <td style={tab_sty} rowSpan={entry.log.length}>{entry.name}</td>
            <td style={tab_sty} rowSpan={entry.log.length}>{JSON.stringify(entry.args)}</td>
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

    return (<>
      {entry.log.map(createStatusRow)}
    </>);
  };

  const cont_sty = { backgroundColor: '#CCCCCC' }
  const closeFloat = () => { setShow(false); }

  return (<div style={cont_sty} className='overlayFloat'>
    <h3 className='header'>Full action Log</h3>
    <button className='floatClose' onClick={closeFloat}>x</button>
    <a href='download/json/actionLog' download>Download JSON</a>
    <div className='floatContent'>
      <table className='hcentering'>
        <tr>
          <th>Action name</th>
          <th>arguments</th>
          <th>status</th>
          <th>status timestamp</th>
        </tr>
        {
          actionLogs.map(createRow)
        }
      </table>
    </div>
  </div>);
}

