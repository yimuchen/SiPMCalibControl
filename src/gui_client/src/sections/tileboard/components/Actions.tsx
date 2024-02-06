import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useGlobalSession } from '../../../session';

const TestAJAXAction = () => {
  const { register, handleSubmit } = useForm();
  const onSubmit = (data: any) => {
    fetch(`test/${data.plotFile}`).then(res => res.json())
      .then(
        (result) => {
          console.log(result)
        },
        (error) => { // What to do if this is wrong!!
          console.log("Recieved ERROR!!");
          console.log(error);
        }
      )
  };

  return (
    <>
      <span>AJAX request test field</span>
      <form onSubmit={handleSubmit(onSubmit)}>
        <input {...register("plotFile")} />
        <input type="submit" value="Get AJAX request" />
      </form>
    </>
  );
};


type ActionSubmitProp = {
  value: string
}

const ActionSubmit = (prop: ActionSubmitProp) => {
  const { actionAllowed } = useGlobalSession();
  return <input disabled={!actionAllowed} type="submit" value={prop.value} />
}

type ActionRequest = {
  name: string;
  args: any;
}

const TestSingleShotAction = () => {
  const { socketInstance } = useGlobalSession();
  const { register, handleSubmit } = useForm();
  const onSubmit = (data: any) => {
    if (socketInstance) {
      const request: ActionRequest = { name: 'single-shot-test', args: data };
      socketInstance.emit("run-action", request);
    }
  }

  return (
    <span>
      <h2>Single shot action test</h2>
      <form onSubmit={handleSubmit(onSubmit)}>
        <input {...register("line")} />
        <ActionSubmit value="Run single shot command" />
      </form>
    </span>
  );
}

const ActionInterupt = () => {
  const { socketInstance } = useGlobalSession();
  const { handleSubmit } = useForm();
  const onSubmit = (data: any) => {
    if (socketInstance) { socketInstance.emit("user-interupt"); }

  }
  return (
    <span>
      <form onSubmit={handleSubmit(onSubmit)}>
        <input type="submit" value="!!!!" />
      </form>
    </span >)
}


const Actions = () => {
  return (<div>
    <TestAJAXAction /><br />
    <TestSingleShotAction />
    <ActionInterupt />
  </div >
  );
};

export default Actions;
