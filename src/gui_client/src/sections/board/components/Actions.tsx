import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useGlobalSession } from '../../../session';

const TestAction = () => {
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
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register("plotFile")} />
      <input type="submit" value="This is a test!!" />
    </form>
  );
};


const Actions = () => {

  return (<div>
    <TestAction />
  </div>
  );
};

export default Actions;
