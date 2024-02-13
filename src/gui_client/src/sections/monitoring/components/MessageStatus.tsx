import { useGlobalSession, MessageLog } from '../../../session';
import { timestampString } from '../../../utils/format';

const MessageStatus = () => {
  // Main data container
  const { messageLogs } = useGlobalSession();

  const recordRow = (rec: MessageLog) => {
    return (
      <tr>
        <td>{timestampString(rec.time)}</td>
        <td>{rec.level}</td>
        <td>{rec.msg}</td>
      </tr>
    );
  };

  return (
    <>
      <h3>Messages</h3>
      <a href='/download/text/messageLog' download>Download text</a>
      <a href='/download/json/messageLog' download>Download JSON</a>
      <table>
        <tr>
          <th>Timestamp</th>
          <th>Level</th>
          <th>Message</th>
        </tr>
        {messageLogs.slice(-10).reverse().map(recordRow)}
      </table>
    </>
  );
};

export default MessageStatus;
