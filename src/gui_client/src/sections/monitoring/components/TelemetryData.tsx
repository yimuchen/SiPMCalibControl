import { useEffect, useState } from 'react';
import { TelemetryEntry, useGlobalSession } from '../../../session';
import { timestampToDate } from '../../../utils/format'

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

type TelemetryDataProps = {
  telemetryLogs: TelemetryEntry[];
};

type PlotDataEntry = {
  time: Date;
  sipm_bias: number
  sipm_temp: number
};

const TelemetryData = ({ telemetryLogs }: TelemetryDataProps) => {
  const [plotsData, setPlotsData] = useState<PlotDataEntry[]>([]);

  useEffect(() => {
    setPlotsData((old_data: PlotDataEntry[]): PlotDataEntry[] => {
      return telemetryLogs.map((x) => {
        return {
          time: timestampToDate(x.timestamp),
          sipm_bias: x.sipm_bias,
          sipm_temp: x.sipm_temp,
        }
      })
    });
  }, [telemetryLogs]);

  // Some additional formatting helpers 
  const tooltipFormatter = (value: number) => `${value.toFixed(1)}`;
  const yLabelCommon = { angle: -90, position: 'outerLeft', dy: -10, }
  const outerLayout = { margin: { top: 10, right: 5, bottom: 40, left: 60 }, };

  // Creating the plotting scripts using the data set
  return (
    <div>
      <div>
        <h3>Temperatures</h3>
        <ResponsiveContainer width='100%' height={300} key={`rc_${plotsData.length}`}>
          <LineChart {...outerLayout} data={plotsData}>
            <CartesianGrid strokeDasharray='3 3' />
            <XAxis dataKey='time' />
            <YAxis><Label value="Temperature [C]" angle={-90} /></YAxis>
            <Tooltip formatter={tooltipFormatter} />
            <Legend verticalAlign='top' align='center' />
            <Line type='monotone' isAnimationActive={false} dataKey='sipm_temp' name='Pulser' stroke='blue' />
            /*<Line type='monotone' isAnimationActive={false} dataKey='sipmTemp' name='Tileboard' stroke='red' />*/
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div>
        <h3>Voltages</h3>
        <ResponsiveContainer width='100%' height={300} key={`rc_${plotsData.length}`}>
          <LineChart {...outerLayout} data={plotsData}>
            <CartesianGrid strokeDasharray='3 3' />
            <XAxis dataKey='time' />
            <YAxis label={{ value: 'Voltage [mV]', ...yLabelCommon }} />
            <Tooltip formatter={tooltipFormatter} />
            <Legend verticalAlign='top' align='center' />
            <Line type='monotone' isAnimationActive={false} dataKey='sipm_bias' name='Pulser board Bias' stroke='green' />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default TelemetryData;
