import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useGlobalSession } from '../../../session';
import { SubmitActionRequest, ActionSubmit } from '../../../utils/common';

const LoadTileBoard = () => {
  const { sessionBoard } = useGlobalSession();
  const [summary, setSummary] = useState<string>('');

  useEffect(() => {
    if (sessionBoard === null || sessionBoard === undefined) {
      setSummary('Not set');
    } else {
      console.log(sessionBoard);
      setSummary(`${sessionBoard.board_type}@${sessionBoard.id_unique}`);
    }
  }, [sessionBoard]);

  return (
    <div className='tablediv'>
      <div className='tbrowdiv'>
        <div className='tbcelldiv'>
          <span style={{ paddingRight: '20px' }}>
            <b>Session</b> <br />
            {summary}
          </span>
        </div>
        <div className='tbcelldiv'>
          <div className='tablediv'>
            <LoadNewSession />
            <LoadExistingSession />
          </div>
        </div>
      </div>
    </div>
  );
};

const LoadNewSession = () => {
  const { socketInstance, sessionBoard } = useGlobalSession();
  const { register, handleSubmit } = useForm();
  const [boardTypeList, setBoardTypes] = useState<string[]>([]);
  const submitNewSession = (data: any) => {
    console.log();
    SubmitActionRequest(socketInstance, 'start-new-session', data);
  };

  useEffect(() => {
    fetch(`/config/boardTypes`)
      .then((res) => res.json())
      .then(
        (result) => {
          setBoardTypes(result);
        },
        (error) => {
          // What to do if this is wrong!!
          console.log('Recieved ERROR!!');
          console.log(error);
        },
      );
  }, [sessionBoard]);

  const makeOption = (x: string) => {
    return <option value={x}>{x}</option>;
  };

  return (
    <div className='tbrowdiv'>
      <form onSubmit={handleSubmit(submitNewSession)}>
        <div className='tbcelldiv'>
          <select {...register('board_type')}>
            <option value='' selected disabled hidden>
              -- Available board types --
            </option>
            {boardTypeList.map(makeOption)}
          </select>
          ID: <input {...register('board_id')} />
        </div>
        <div className='tbcelldiv'>
          <ActionSubmit value='Start new session' />
        </div>
      </form>
    </div>
  );
};

const LoadExistingSession = () => {
  const { socketInstance, sessionBoard } = useGlobalSession();
  const { register, handleSubmit } = useForm();
  const [existingSessionList, setSessionList] = useState<string[]>([]);

  const submitLoadSession = (data: any) => {
    SubmitActionRequest(socketInstance, 'load-session', data);
  };

  useEffect(() => {
    fetch(`/config/savedSessions`)
      .then((res) => res.json())
      .then(
        (result) => {
          setSessionList(result);
        },
        (error) => {
          // What to do if this is wrong!!
          console.log('Recieved ERROR!!');
          console.log(error);
        },
      );
  }, [sessionBoard]);

  const makeOption = (x: string) => {
    return <option value={x}>{x}</option>;
  };

  return (
    <div className='tbrowdiv'>
      <form onSubmit={handleSubmit(submitLoadSession)}>
        <div className='tbcelldiv'>
          <select {...register('session_id')}>
            <option value='' selected disabled hidden>
              -- Saved sessions --
            </option>
            {existingSessionList.map(makeOption)}
          </select>
        </div>
        <div className='tbcelldiv'>
          <ActionSubmit value='Load existing session' />
        </div>
      </form>
    </div>
  );
};

export default LoadTileBoard;
