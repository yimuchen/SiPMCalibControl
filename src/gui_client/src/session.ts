/*
 * This is the master client session state variable. The contents of this item
 * should directly mirror what is implemented in the python server GUISession
 * item. With roughtly matching data types. The Python will implement JS data
 * types as dictionaries of various plain types.
 */
// External requirements
import { createContext, useContext } from 'react';
import type { Socket } from 'socket.io-client';

/** Compare with gantry_control/cli/board.py */
export type CalibrationResult = {
  process: string;
  filename: string;
  timestamp: string;
  data: number[];
};

export type Detector = {
  readout: number[];
  default_coords: [number, number];
  calibrated: CalibrationResult[];
};

export type BoardCalibSingleResults = {
  status: number;
  message: string;
};

export type BoardCalib = {
  process: string;
  datafile: string;
  board_summary: string;
  detector_summary: BoardCalibSingleResults[];
};

export type Condition = {}; // TODO!!
export type Board = {
  filename: string;
  board_type: string;
  description: string;
  id_unique: number;
  detectors: Detector[];
  board_routines: BoardCalib[];
}; // TODO!!

/** Additional entries for maintingly GUI client interaction */
export type TelemetryEntry = {
  timestamp: string;
  tb_sipm_bias: number;
  tb_led_bias: number;
  tb_temp: number;
  gmq_pulser_temp: number;
  gmq_pulser_lv: number;
  gmq_pulser_hv: number;
  gantry_coord: [number, number, number];
};

export type ActionStatus = {
  timestamp: string;
  message: string;
  status: number;
};

export type ActionEntry = {
  name: string;
  args: any;
  progress: [number, number];
  log: ActionStatus[];
};

/** Message logging entries - defined in cli/format.py */
export type MessageLog = {
  time: string;
  name: string;
  level: string;
  msg: string;
  args: string;
};

export type HardwareStatus = {
  gantryHW: string | null;
  tileboardHW: string | null;
};

// The type and the corresponding setting methods for React Hooks
export type SessionType = {
  // Socket instance required for the main session
  socketInstance: Socket | null;
  setSocketInstance: (c: Socket | null) => void;

  // Main items to be store the information passed from the server side
  telemetryLogs: TelemetryEntry[];
  setTelemetryLogs: (c: TelemetryEntry[]) => void;
  actionLogs: ActionEntry[];
  setActionLogs: (c: ActionEntry[]) => void;
  messageLogs: MessageLog[];
  setMessageLogs: (c: MessageLog[]) => void;

  hardwareStatus: HardwareStatus;
  setHardwareStatus: (c: HardwareStatus) => void;
  // Session board
  sessionBoard: Board | null; // A board can be unloaded!!
  setSessionBoard: (c: Board | null) => void;

  // Helper item to help with commonly/global status parsing
  actionAllowed: boolean;
  setActionAllowed: (c: boolean) => void;
};

export const GlobalSessionContext = createContext<SessionType>({
  socketInstance: null,
  setSocketInstance: () => {},
  telemetryLogs: [],
  setTelemetryLogs: () => {},
  actionLogs: [],
  setActionLogs: () => {},
  messageLogs: [],
  setMessageLogs: () => {},
  hardwareStatus: { gantryHW: null, tileboardHW: null },
  setHardwareStatus: () => {},

  sessionBoard: null,
  setSessionBoard: () => {},

  actionAllowed: false,
  setActionAllowed: () => {},
});

export const useGlobalSession = () => useContext(GlobalSessionContext);
