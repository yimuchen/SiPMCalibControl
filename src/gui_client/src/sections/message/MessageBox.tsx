import { useState } from 'react';
import { MessageLog, useGlobalSession } from '../../session';
import { timestampString } from '../../utils/format';

type FullDisplyProp = {
  show: boolean;
  setShow: (c: boolean) => void;
};
export const MessageFullDisplay = ({ show, setShow }: FullDisplyProp) => {
  const { messageLogs } = useGlobalSession();
  if (!show) return <></>;
  const closeFloat = () => {
    setShow(false);
  };

  const makeDetailedRow = (rec: MessageLog) => {
    return (
      <tr>
        <td>{timestampString(rec.time)}</td>
        <td>{rec.level}</td>
        <td>{rec.msg}</td>
      </tr>
    );
  };

  const cont_sty = { backgroundColor: '#FFEFEF' };
  return (
    <div style={cont_sty} className='overlayFloat'>
      <h2>Full message log</h2>
      <a href='/download/json/messageLog' download>
        Download monitor log
      </a>
      <button className='floatClose' onClick={closeFloat}>
        x
      </button>
      <table>
        <tr>
          <th>Timestamp</th>
          <th>Level</th>
          <th>Message</th>
        </tr>
        {messageLogs.map(makeDetailedRow)}
      </table>
    </div>
  );
};

const MessageBox = () => {
  const { messageLogs } = useGlobalSession();
  const [showFull, setShowFull] = useState<boolean>(false);

  const toggleShowFull = () => {
    setShowFull(true);
  };
  return (
    <div style={{ display: 'flex' }}>
      <div style={{ display: 'flow', marginLeft: '10px', marginRight: '10px' }}>
        <h2 style={{ margin: '3px' }}>System messages</h2>
        <div style={{ fontSizeAdjust: 0.4 }}>
          <button onClick={toggleShowFull} style={{ fontSize: '8pt' }}>
            Show full message log
          </button>
          <br />
          <a href='/download/json/messageLog' download style={{ fontSize: '8pt' }}>
            Download monitor log
          </a>
        </div>
      </div>
      <div style={{ textAlign: 'center', maxWidth: '900px', height: '100%', overflow: 'scroll' }}>
        <table style={{ fontSize: '10pt' }}>
          {messageLogs
            .slice(-5)
            .reverse()
            .map((rec: MessageLog) => {
              return (
                <tr>
                  <td className='textCenter'>{timestampString(rec.time)}</td>
                  <td className='textCenter'>{rec.level}</td>
                  <td className='textLeft'>{rec.msg}</td>
                </tr>
              );
            })}
          <tr>
            <td>{messageLogs.length > 5 ? '...' : ''}</td>
            <td />
            <td />
          </tr>
        </table>
      </div>
      <MessageFullDisplay show={showFull} setShow={setShowFull} />
    </div>
  );
};

export default MessageBox;
