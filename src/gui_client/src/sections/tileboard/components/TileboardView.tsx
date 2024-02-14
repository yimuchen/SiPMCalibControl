import { useState, useEffect } from 'react';
import { useGlobalSession } from '../../../session';

type TileboardViewProp = {
  showDetector: number | null;
  setShowDetector: (c: number | null) => void;
};
export const TileboardView = ({ showDetector, setShowDetector }: TileboardViewProp) => {
  const { sessionBoard } = useGlobalSession();
  const canvasWidth = 600;
  const canvasHeight = 600;

  // For a global board view, the detector elements will be represented simply
  // as their default (x,y) coordinates, a summary string, and a status color.
  // For drawing, a list of simple detectors will be used.
  type SimpleDetector = {
    pos: [number, number];
    summary: string;
    color: string;
  };
  const [detectorList, setDetectorList] = useState<SimpleDetector[]>([]);

  useEffect(() => {
    if (sessionBoard != null && sessionBoard != undefined) {
      setDetectorList(
        sessionBoard.detectors.map((x) => {
          // TODO: properly implement summary and color parsing
          return {
            pos: x.default_coords,
            summary: 'GOOD',
            color: '#00FF00',
          };
        }),
      );
    }
  }, [sessionBoard]);

  // Early exit if board doesn't exist
  if (sessionBoard === null || sessionBoard === undefined) {
    return (
      <div style={{ height: canvasHeight, width: canvasWidth, border: 'orange 5px solid' }}>
        Board is not loaded
      </div>
    );
  }

  const requestShow = (e: any) => {
    const clickId = e.target.id.replace('tbview_detector_', '');
    setShowDetector(Number(clickId));
  };

  const detectorSVG = (d: SimpleDetector, idx: number) => {
    const detWidth = 40;
    const detHeight = 40;

    const detX = d.pos[0] - detWidth / 2;
    const detY = canvasHeight - d.pos[1] - detHeight / 2;

    return (
      <>
        <rect
          width={detWidth}
          height={detHeight}
          x={detX}
          y={detY}
          fill={d.color}
          id={`tbview_detector_${idx}`}
          onClick={requestShow}
        >
          <title>{d.summary}</title>
        </rect>
        <text
          x={detX + detWidth / 2}
          y={detY + detHeight / 2}
          dominant-baseline='middle'
          text-anchor='middle'
        >
          {idx}
        </text>
      </>
    );
  };

  return (
    <>
      <h4>Board overview</h4>
      <span>Board type: {sessionBoard.board_type}</span>
      <span>Board ID: {sessionBoard.id_unique}</span>
      <div style={{ height: canvasHeight, width: canvasWidth, border: 'orange 5px solid' }}>
        <g>
          <svg xmlns='http://www.w3.org/2000/svg' width={canvasWidth} height={canvasHeight}>
            {detectorList.map(detectorSVG)}
          </svg>
        </g>
      </div>
    </>
  );
};

export default TileboardView;
