// Importing external requirements
import { useEffect, useState } from 'react';
import { io } from 'socket.io-client';
import type { Socket } from 'socket.io-client';

// Inporting the styling
import '../app.css';

// Importing the global session context and the associated custom types
import { ActionStatus, ActionEntry, TelemetryEntry, Board, GlobalSessionContext } from '../session';

// Importing display sections
import Monitoring from './monitoring/Monitoring';
import Calibration from './callibration/Calibration';
import Tileboard from './tileboard/Tileboard';

// Importing the various data typesi
//
// Here we will also handle the server-side update signals to update the
// variables that will be passed to the global context. Parsing of the data to
// be presentation ready in the GUI elements will be handled by the various
// components.

const App = () => {
  // Creating the various objects required to use the global session 
  const [socketInstance, setSocketInstance] = useState<Socket | null>(null);
  const [telemetryLogs, setTelemetryLogs] = useState<TelemetryEntry[]>([]);
  const [actionLogs, setActionLogs] = useState<ActionEntry[]>([]);
  const [sessionBoard, setSessionBoard] = useState<Board | null>(null);
  const [actionAllowed, setActionAllowed] = useState<boolean>(false);

  // Adidtional entities to be used to initate the socket on first start up.
  const [buttonStatus, setButtonStatus] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  // For the connect button
  const handleClick = () => { setButtonStatus((currStatus) => !currStatus); };

  useEffect(() => {
    if (buttonStatus === true) {
      const socket = io('localhost:9100/', { transports: ['websocket'] });
      console.log("connecting to socket!!", socket);
      setSocketInstance(socket);
      // Start up and disconnect function. 
      socket.on('connect', () => { console.log('Connected'); });
      socket.on('disconnect', (data) => { console.log(data); });
      // Signals events with corresponding server side entries in the
      // sync_socket.py file. The various update function will need to be
      // defined outside this methods
      setLoading(false);

      return function cleanup() {
        socket.disconnect();
      };
    }
  }, [buttonStatus]);

  // Update function split to another instance. Corresponding methods should be
  // found in the sync_sockets.py file in the gui_server side code.
  useEffect(() => {
    if (socketInstance) {
      socketInstance.on('update-session-telemetry-full', updateTelemetryFull);
      socketInstance.on('update-session-telemetry-append', updateTelemetryAppend);
      socketInstance.on('update-session-action-full', updateActionFull);
      socketInstance.on('update-session-action-append', updateActionAppend);
      socketInstance.on('update-session-action-status', updateActionStatus);
      socketInstance.on("update-session-action-progress", updateActionProgress);
      socketInstance.on("sync-board", updateBoard);
      return function cleanup() {
        socketInstance.off("update-session-telementry-full");
        socketInstance.off("update-session-telementry-append");
        socketInstance.off("update-session-action-full");
        socketInstance.off("update-session-action-append");
        socketInstance.off("update-session-action-status");
        socketInstance.off("update-session-action-progress");
      }
    }
  }, [socketInstance, telemetryLogs, actionLogs, sessionBoard])

  // Implementation of the settings methods
  const updateTelemetryFull = (msg: TelemetryEntry[]) => { setTelemetryLogs(msg); }
  const updateTelemetryAppend = (msg: TelemetryEntry) => { setTelemetryLogs([...telemetryLogs, msg]) }
  const updateActionFull = (msg: ActionEntry[]) => { setActionLogs(msg); }
  const updateActionAppend = (msg: ActionEntry) => { setActionLogs([...actionLogs, msg]); }
  const updateActionStatus = (msg: ActionStatus) => {
    var lastAction = actionLogs.slice(-1)[0];
    lastAction.log.push(msg);
    setActionLogs([...actionLogs.slice(0, -1), lastAction]);
  };
  const updateActionProgress = (msg: any) => {
    var lastAction = actionLogs.slice(-1)[0];
    lastAction.progress = msg;
    setActionLogs([...actionLogs.slice(0, -1), lastAction]);
  }
  const updateBoard = (msg: Board | null) => { console.log(msg); setSessionBoard(msg); }

  // Nontrivial Common/Global state parsing
  useEffect(() => {
    if (actionLogs.length === 0) {
      setActionAllowed(false); // Something is wrong 
    } else {
      const finalAction = actionLogs.slice(-1)[0]
      const finalStatus = finalAction.log.slice(-1)[0].status;
      setActionAllowed(finalStatus === 0 || finalStatus === 2 || finalStatus === 4);
    }
  }, [actionLogs])


  // Using the global context to handle the various display elements

  return (
    <GlobalSessionContext.Provider
      value={{
        socketInstance,
        setSocketInstance,
        telemetryLogs,
        setTelemetryLogs,
        actionLogs,
        setActionLogs,
        sessionBoard,
        setSessionBoard,
        actionAllowed,
        setActionAllowed
      }}
    >
      <div>
        {buttonStatus && socketInstance ? (
          <>
            <button onClick={handleClick}>Disconnect from session</button>
            <div>
              {!loading && (
                <div className='bodyContainer'>
                  <div className='monitorContainer'>
                    <Monitoring />
                  </div>
                  <div className='boardviewContainer'>
                    <Tileboard />
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

