// Importing external requirements
import { useEffect, useState } from 'react';
import { io } from 'socket.io-client';
import type { Socket } from 'socket.io-client';

// Inporting the styling
import '../app.css';

// Importing the global session context and the associated custom types
import { TelemetryEntry, GlobalSessionContext } from '../session';

// Importing display sections
import Monitoring from './monitoring/Monitoring';
import CommandLine from './command_line/CommandLine';
import Calibration from './callibration/Calibration';
import Board from './board/Board';

// Importing the various data types

const App = () => {
  // Creating the various objects required to use the global session 
  const [socketInstance, setSocketInstance] = useState<Socket | null>(null);
  const [sessionState, setSessionState] = useState<string | null>(null);
  const [telemetryLogs, setTelemetryLogs] = useState<TelemetryEntry[]>([]);

  // Adidtional entities to be used to initate the socket on first start up.
  const [buttonStatus, setButtonStatus] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  // For the connect button
  const handleClick = () => {
    console.log("Button press!!")
    setButtonStatus((currStatus) => !currStatus);
  };

  useEffect(() => {
    if (buttonStatus === true) {
      const socket = io('localhost:9100/', { transports: ['websocket'] });
      console.log("connecting to socket!!", socket);

      setSocketInstance(socket);
      // Start up and disconnect function. Other socket interactions will be
      // defined in the various files where it makes sense
      socket.on('connect', () => { console.log('Connected'); });
      socket.on('disconnect', (data) => { console.log(data); });
      setLoading(false);

      return function cleanup() {
        socket.disconnect();
      };
    }
  }, [buttonStatus]);

  // update last_cmd when sessionLog changes
  // 
  /*
  useEffect(() => {
    const target = 5;

    const lastIndex = sessionLogs.reverse().findIndex((entry) => entry.levelno === target);
    const result =
      lastIndex !== -1 ? sessionLogs[sessionLogs.length - lastIndex - 1] : sessionLogs[-1];

    setLastCmd(result);
  }, [sessionLogs]);
  */

  // Using the global context to handle the various display elements

  return (
    <GlobalSessionContext.Provider
      value={{
        socketInstance,
        setSocketInstance,
        sessionState,
        setSessionState,
        telemetryLogs,
        setTelemetryLogs
      }}
    >
      <div>
        {buttonStatus && socketInstance ? (
          <>
            <button onClick={handleClick}>Disconnect from session</button>
            <div>
              {!loading && (
                <div className='mainContainer'>
                  <div className='monitoring'>
                    <Monitoring />
                  </div>
                  <div className='centerContainer'>
                    <Board />
                  </div>
                  <div className='calibration'>
                    <Calibration />
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          <>
            <button onClick={handleClick}>Reconnect to GUI session</button>
          </>
        )}
      </div>
    </GlobalSessionContext.Provider>
  );
};

export default App;

