import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useGlobalSession } from '../../../../session';
import { ActionSubmit, SubmitActionRequest } from '../../../../utils/common';

export const BoardActions = () => {
  return (
    <>
      <h3>Board wide calibrations</h3>
      <div className='tablediv'>
        <TestSingleShotAction />
        <TestAJAXAction />
        <PedestalNormalizeAction />
        <OnboardSPSAction />
      </div>
    </>
  );
};

const TestAJAXAction = () => {
  const { register, handleSubmit } = useForm();
  const onSubmit = (data: any) => {
    fetch(`test/${data.plotFile}`)
      .then((res) => res.json())
      .then(
        (result) => {
          console.log(result);
        },
        (error) => {
          // What to do if this is wrong!!
          console.log('Recieved ERROR!!');
          console.log(error);
        },
      );
  };

  return (
    <div className='tbrowdiv'>
      <div className='tbcelldiv'>AJAX request test field</div>
      <div className='tbcelldiv'>
        <form onSubmit={handleSubmit(onSubmit)}>
          <input {...register('plotFile')} />
          <input type='submit' value='Get AJAX request' />
        </form>
      </div>
    </div>
  );
};

const TestSingleShotAction = () => {
  const { socketInstance } = useGlobalSession();
  const { register, handleSubmit } = useForm();
  const onSubmit = (data: any) => {
    SubmitActionRequest(socketInstance, 'single-shot-test', data);
  };

  return (
    <div className='tbrowdiv'>
      <div className='tbcelldiv'>
        <b>Single shot action test</b>
      </div>
      <div className='tbcelldiv'>
        <form onSubmit={handleSubmit(onSubmit)}>
          <input {...register('line')} />
          <ActionSubmit value='Run single shot command' />
        </form>
      </div>
    </div>
  );
};

const PedestalNormalizeAction = () => {
  const { socketInstance, sessionBoard } = useGlobalSession();
  const [currentStatus, setCurrentStatus] = useState<string>('(Not done)');
  const [configList, setConfigList] = useState<string[]>([]);
  const { register, handleSubmit } = useForm();

  useEffect(() => {
    // Getting the template
    fetch(`/config/templateYAMLs`)
      .then((res) => res.json())
      .then(
        (result) => {
          setConfigList(result);
        },
        (error) => {
          // What to do if this is wrong!!
          console.log('Recieved ERROR!!');
          console.log(error);
        },
      );

    if (sessionBoard) {
      const process = sessionBoard.board_routines.filter((x) => x.process == 'pedestal');
      if (process.length > 0) {
        setCurrentStatus(process[0].board_summary);
      }
    }
  }, [sessionBoard]);

  const submitRunRequest = (data: any) => {
    SubmitActionRequest(socketInstance, 'run-pedestal', data);
  };

  return (
    <div className='tbrowdiv'>
      <div className='tbcelldiv'>
        <b>Normalized Pedestal</b>
        <br />
        {currentStatus}
      </div>
      <div className='tbcelldiv' style={{ display: 'flex' }}>
        <form onSubmit={handleSubmit(submitRunRequest)}>
          <select {...register('baseconfig')}>
            <option value='' selected disabled hidden>
              -- Base configuration --
            </option>
            {configList.map((x: string) => (
              <option value={x}>{x}</option>
            ))}
          </select>
          <ActionSubmit value='Run' />
        </form>
      </div>
    </div>
  );
};
const OnboardSPSAction = () => {
  const { socketInstance, sessionBoard } = useGlobalSession();
  const [currentStatus, setCurrentStatus] = useState<string>('(Not done)');
  const [configList, setConfigList] = useState<string[]>([]);
  const { register, handleSubmit } = useForm();

  const submitRunRequest = (data: any) => {
    SubmitActionRequest(socketInstance, 'run-sps', data);
  };

  return (
    <div className='tbrowdiv'>
      <div className='tbcelldiv'>
        <b>SPS scan (on-board LED)</b>
        <br />
        {currentStatus}
      </div>
      <div className='tbcelldiv' style={{ display: 'flex' }}>
        <form onSubmit={handleSubmit(submitRunRequest)}>
          <select {...register('baseconfig')}>
            <option value='' selected disabled hidden>
              -- Base configuration --
            </option>
            {configList.map((x: string) => (
              <option value={x}>{x}</option>
            ))}
          </select>
          <ActionSubmit value='Run' />
        </form>
      </div>
    </div>
  );
};

export default BoardActions;
