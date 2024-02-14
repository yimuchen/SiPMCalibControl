import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useGlobalSession } from '../../..//session';

type DetectorViewProp = {
  showDetector: number | null;
  setShowDetector: (c: number | null) => void;
};

export const DetectorView = ({ showDetector, setShowDetector }: DetectorViewProp) => {
  const { sessionBoard } = useGlobalSession();

  if (showDetector === null) {
    // Early exist if display is not requested
    return <></>;
  }

  return (
    <div style={{ marginTop: '10px' }}>
      <h4>Per-detector details and results</h4>
    </div>
  );
};

export default DetectorView;
