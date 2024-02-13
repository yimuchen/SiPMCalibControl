import { useState, useEffect } from 'react';
import { useGlobalSession } from '../../session';

//import Detector from './components/Detector';
import Actions from './components/Actions';

type Props = {};

const Board = (props: Props) => {
  const { sessionBoard } = useGlobalSession();

  /**
   * Getting the latest board.
   */
  useEffect(() => {
    console.log('board changed!!', sessionBoard);
  }, [sessionBoard]);

  return (
    <section>
      <h2>Tileboard</h2>
      <Actions />
      <div>
        {/*board?.detectors.map((detector: Types.BoardDetector) => (
          <Detector key={detector.id} detector={detector} />
        ))*/}
      </div>
    </section>
  );
};

export default Board;
