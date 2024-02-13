/**
 * Sending action request to the backend. Notice the forms should be made to
 * matche the function methods defined in the action_socket.py corresponding
 * backend methods.
 */
import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useGlobalSession } from '../../../session';
import { ActionSubmit, SubmitActionRequest } from '../../../utils/common';

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
    <>
      <span>AJAX request test field</span>
      <form onSubmit={handleSubmit(onSubmit)}>
        <input {...register('plotFile')} />
        <input type='submit' value='Get AJAX request' />
      </form>
    </>
  );
};

const GMQMakeConnection = () => {
  const { socketInstance } = useGlobalSession();
  const { register, handleSubmit } = useForm();

  const submitConnection = (data: any) => {
    SubmitActionRequest(socketInstance, 'gmq_connect', data);
  };
  return (
    <form onSubmit={handleSubmit(submitConnection)}>
      Host: <input {...register('host')} />
      Port: <input {...register('port')} />
      <ActionSubmit value='Connect' />
    </form>
  );
};

const TestSingleShotAction = () => {
  const { socketInstance } = useGlobalSession();
  const { register, handleSubmit } = useForm();
  const onSubmit = (data: any) => {
    SubmitActionRequest(socketInstance, 'single-shot-test', data);
  };

  return (
    <tr>
      <td>
        <b>Single shot action test</b>
      </td>
      <td>
        <form onSubmit={handleSubmit(onSubmit)}>
          <input {...register('line')} />
          <ActionSubmit value='Run single shot command' />
        </form>
      </td>
    </tr>
  );
};

const Actions = () => {
  return (
    <div>
      <table></table>
      <TestSingleShotAction />
      <TestAJAXAction />
      <br />
    </div>
  );
};

export default Actions;
