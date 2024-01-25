import { useState, useEffect } from 'react';
import { useGlobalSession } from '../../session';

import Detector from './components/Detector';
import Actions from "./components/Actions";


type Props = {};

const Board = (props: Props) => {
  const { socketInstance } = useGlobalSession();
  const [board, setBoard] = [null, null] //useState<Types.Board | null>(null);

  /**
   * Getting the latest board.
   */
  useEffect(() => {
    if (socketInstance) {
      socketInstance.on('board-update', (data /*Types.Board*/) => {
        // convert data JSON string to object, then set board state
        // setBoard(JSON.parse(data.board));
      });

      return function cleanup() {
        // set some random data
        // setBoard(null);
        socketInstance.off('board-update');
      };
    }
  }, [socketInstance]);

  const mytest = (evt: any) => {
    console.log("client side action test")
  }

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
