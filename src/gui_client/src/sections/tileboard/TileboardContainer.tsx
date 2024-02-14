import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useGlobalSession } from '../../session';
import { SubmitActionRequest, ActionSubmit } from '../../utils/common';

//import Detector from './components/Detector';
import Actions from './components/Actions';
import TileboardView from './components/TileboardView';
import DetectorView from './components/DetectorView';
type Props = {};

const LoadNewSession = () => {
  const { socketInstance, sessionBoard } = useGlobalSession();
  const { register, handleSubmit } = useForm();
  const [boardTypeList, setBoardTypes] = useState<string[]>([]);
  const submitNewSession = (data: any) => {
    console.log();
    SubmitActionRequest(socketInstance, 'start-new-session', data);
  };

  useEffect(() => {
    fetch(`/boardtypes`)
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
    <form onSubmit={handleSubmit(submitNewSession)}>
      Board type:
      <select {...register('board_type')}>{boardTypeList.map(makeOption)}</select>
      ID: <input {...register('board_id')} />
      <ActionSubmit value='Start new session' />
    </form>
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
    fetch(`/existingsessions`)
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
    <form onSubmit={handleSubmit(submitLoadSession)}>
      <select {...register('session_id')}>{existingSessionList.map(makeOption)}</select>
      <ActionSubmit value='Load existing session' />
    </form>
  );
};

const SessionStatus = () => {
  const { sessionBoard } = useGlobalSession();
  const [summary, setSummary] = useState<string>('');

  useEffect(() => {
    if (sessionBoard === null || sessionBoard === undefined) {
      setSummary('Not set');
    } else {
      console.log(sessionBoard);
      setSummary('XXXX');
    }
  }, [sessionBoard]);

  return (
    <tr>
      <td>
        Session <br />
        {summary}
      </td>
      <td>
        <LoadNewSession />
        <LoadExistingSession />
      </td>
    </tr>
  );
};

const TileBoardContainer = (props: Props) => {
  const { sessionBoard } = useGlobalSession();

  const [showDetector, setShowDetector] = useState<number | null>(null);

  useEffect(() => {
    console.log('board changed!!', sessionBoard);
  }, [sessionBoard]);

  return (
    <section>
      <h2>Tileboard</h2>
      <div style={{ display: 'flex' }}>
        <div style={{ display: 'grid', margin: '10px' }}>
          <TileboardView showDetector={showDetector} setShowDetector={setShowDetector} />
          <DetectorView showDetector={showDetector} setShowDetector={setShowDetector} />
        </div>
        <div style={{ display: 'grid', margin: '10px' }}>
          <SessionStatus />
          <Actions />
        </div>
      </div>
      <div>
        {/*board?.detectors.map((detector: Types.BoardDetector) => (
          <Detector key={detector.id} detector={detector} />
        ))*/}
      </div>
    </section>
  );
};

export default TileBoardContainer;
