import { useGlobalSession } from '../session';
import { Socket } from 'socket.io-client';

export type ActionSubmitProp = {
  value: string;
};

export const ActionSubmit = (prop: ActionSubmitProp) => {
  const { actionAllowed } = useGlobalSession();
  return <input disabled={!actionAllowed} type='submit' value={prop.value} />;
};

export type ActionRequest = {
  name: string;
  args: any;
};

export const SubmitActionRequest = (
  socketInstance: Socket | null,
  actionName: string,
  actionArgs: any,
) => {
  if (socketInstance) {
    const request: ActionRequest = { name: actionName, args: actionArgs };
    socketInstance.emit('run-action', request);
  }
};
