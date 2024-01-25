import React from 'react';
import { useGlobalSession } from '../../../session';

type Props = {};

const VisualSystem = (props: Props) => {
  const { socketInstance } = useGlobalSession();

  return <h3>Visual System</h3>;
};

export default VisualSystem;
