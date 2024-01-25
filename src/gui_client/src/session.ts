/*
* This is the master client session state variable. The contents of this item
* should directly mirror what is implemented in the python server GUISession
* item. With roughtly matching data types. The Python will implement JS data
* types as dictionaries of various plain types.
*/
// External requirements
import { createContext, useContext } from 'react';
import type { Socket } from 'socket.io-client';

export type Board = {}; // TODO!!
export type Condition = {}; // TODO!!

export type TelemetryEntry = {
  timestamp: string;
  sipm_bias: number;
  sipm_temp: number;
  gantry_coord: [number, number, number]
};


// The type  and the corresponding construction (for React Hooks)
export type SessionType = {
  socketInstance: Socket | null;
  setSocketInstance: (c: Socket | null) => void;
  sessionState: string | null;
  setSessionState: (c: string | null) => void;

  // Common items
  telemetryLogs: TelemetryEntry[];
  setTelemetryLogs: (c: TelemetryEntry[]) => void;
};

export const GlobalSessionContext = createContext<SessionType>({
  socketInstance: null,
  setSocketInstance: () => { },
  sessionState: null,
  setSessionState: () => { },
  telemetryLogs: [],
  setTelemetryLogs: () => { },
});

export const useGlobalSession = () => useContext(GlobalSessionContext);

