import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Detector, useGlobalSession } from '../../../session';
import {
  LineChart,
  Line,
  Label,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
} from 'recharts';

type DetectorViewProp = {
  showDetector: number;
  setShowDetector: (c: number) => void;
};

export const DetectorView = ({ showDetector, setShowDetector }: DetectorViewProp) => {
  const { sessionBoard } = useGlobalSession();
  const [displayDet, setDisplayDet] = useState<Detector | null>(null);

  useEffect(() => {
    if (sessionBoard === null || sessionBoard === undefined) {
      setDisplayDet(null);
    } else {
      setDisplayDet(sessionBoard.detectors[showDetector]);
    }
  }, [sessionBoard, showDetector]);

  return (
    <div style={{ marginLeft: '20px' }}>
      <h4>Per-detector details and results</h4>
      <div className='tablediv'>
        <div className='tbrowdiv'>
          <div className='tbcelldiv'>
            <b>Detector Index</b>
          </div>
          <div className='tbcelldiv'>{showDetector}</div>
        </div>
        <div className='tbrowdiv'>
          <div className='tbcelldiv'>
            <b>Default position</b>
          </div>
          <div className='tbcelldiv'>
            {displayDet
              ? `(${displayDet.default_coords[0].toFixed(1)}, ${displayDet.default_coords[1].toFixed(1)})`
              : 'Not loaded'}
          </div>
        </div>
        <div className='tbrowdiv'>
          <div className='tbcelldiv'>
            <b>Readout</b>
          </div>
          <div className='tbcelldiv'>
            {displayDet
              ? displayDet.readout[0] === 2
                ? `Tileboard (channel ${displayDet.readout[1]})`
                : displayDet.readout[0] === -1
                  ? `Dummy (channel ${displayDet.readout[1]})`
                  : 'Not set'
              : 'Not set'}
          </div>
        </div>
        <div className='tbrowdiv'>
          <div className='tbcelldiv'>
            <b>Calibration results</b>
          </div>
          <div className='tbcelldiv'>
            <div className='tablediv'>
              <PedestalResults detid={showDetector} />
              <SPSResults detid={showDetector} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

type PedestalResultsProp = {
  detid: number;
};
const PedestalResults = ({ detid }: PedestalResultsProp) => {
  const { sessionBoard } = useGlobalSession();
  const [status, setStatus] = useState<string>('(not done)');

  type PlotDataEntry = {
    adc: number;
    entry: number;
  };

  const [plotData, setPlotData] = useState<PlotDataEntry[]>([]);

  useEffect(() => {
    if (sessionBoard) {
      const process = sessionBoard.board_routines.filter((x) => x.process == 'pedestal');
      if (process.length > 0) {
        setStatus(process[0].detector_summary[detid].message);
        fetch(`/plotdet/pedestal/${detid}`)
          .then((res) => res.json())
          .then(
            (result: [number[], number[]]) => {
              const [adcs, entries] = result;
              entries.push(entries[entries.length - 1]);
              const newPlotData: PlotDataEntry[] = [];
              adcs.forEach((adc, idx) => {
                const entry = entries[idx];
                newPlotData.push({ adc: adc, entry: entry });
              });

              setPlotData(newPlotData);
              console.log(plotData);
            },
            (error) => {
              // What to do if this is wrong!!
              console.log('Recieved ERROR!!');
              console.log(error);
            },
          );
      }
    }
  }, [sessionBoard, detid]);

  return (
    <div className='tbrowdiv'>
      <div className='tbcelldiv'>
        Pesdestal
        <br />
        {status}
      </div>
      <div className='tbcelldiv'>
        <ResponsiveContainer width={300} height={200} key={`rc_pedestal_${detid}`}>
          <LineChart data={plotData}>
            <CartesianGrid strokeDasharray='3 3' />
            <XAxis label={{ value: 'ADC', dataKey: 'adc' }} />
            <YAxis label={{ value: 'Events' }} />
            <Legend verticalAlign='top' align='center' />
            <Line
              type='monotone'
              isAnimationActive={false}
              dataKey='entry'
              name='Readout'
              stroke='red'
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

type SPSResultsProp = {
  detid: number;
};
const SPSResults = ({ detid }: PedestalResultsProp) => {
  const [status, setStatus] = useState<string>('(not done)');
  return (
    <div className='tbrowdiv'>
      <div className='tbcelldiv'>
        SPS (on-board LED)
        <br />
        {status}
      </div>
      <div className='tbcelldiv'>
        <button>show Data</button>
      </div>
    </div>
  );
};

export default DetectorView;
