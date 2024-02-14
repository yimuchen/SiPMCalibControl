import { useState, useEffect } from 'react';
import { useGlobalSession } from '../../session';

//import Detector from './components/Detector';
import TileboardView from './components/TileboardView';
import DetectorView from './components/DetectorView';
import LoadTileBoard from './components/TileboardLoad';

const TileBoardContainer = () => {
  const { sessionBoard } = useGlobalSession();
  const [showDetector, setShowDetector] = useState<number | null>(null);

  useEffect(() => {
    console.log('board changed!!', sessionBoard);
  }, [sessionBoard]);

  return (
    <section>
      <h2>Tileboard</h2>
      <LoadTileBoard />
      <div style={{ display: 'flex' }}>
        <TileboardView showDetector={showDetector} setShowDetector={setShowDetector} />
        <DetectorView showDetector={showDetector} setShowDetector={setShowDetector} />
      </div>
    </section>
  );
};

export default TileBoardContainer;
