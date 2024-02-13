import { useEffect, useState } from 'react';
import { TelemetryEntry, useGlobalSession } from '../../../session';
import { makeTimeString, timestampToDate } from '../../../utils/format';

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

// Formatting helpers
const tooltipFormatter = (value: number) => `${Number(value).toFixed(1)}`;
const dateTickFormatter = (value: Date) => makeTimeString(value);
const yLabelCommon = { angle: -90, dx: -20 };
const xAxisCommon = {
  dataKey: 'time',
  tickFormatter: dateTickFormatter,
  label: {
    value: 'Time',
    dy: 20,
  },
};

const outerLayout = { margin: { top: 5, right: 5, bottom: 15, left: 5 } };

type TelemetryDataProps = {
  telemetryLogs: TelemetryEntry[];
};

type TempDataEntry = {
  time: Date;
  tb_temp: number;
  pulser_temp: number;
};

export const TempMonitorStatus = () => {
  const { telemetryLogs } = useGlobalSession();
  const [plotData, setPlotData] = useState<TempDataEntry[]>([]);
  const [showFull, setShowFull] = useState<boolean>(false);

  const showFullData = () => {
    setShowFull(true);
  };

  useEffect(() => {
    setPlotData((old_data: TempDataEntry[]): TempDataEntry[] => {
      return telemetryLogs.map((x) => {
        return {
          time: timestampToDate(x.timestamp),
          tb_temp: x.tb_temp,
          pulser_temp: x.gmq_pulser_temp,
        };
      });
    });
  }, [telemetryLogs]);

  return (
    <div>
      <h3>Subsystem - Temperature monitoring</h3>
      <ResponsiveContainer width='100%' height={200} key={`rc_${plotData.slice(-100).length}`}>
        <LineChart {...outerLayout} data={plotData.slice(-100)}>
          <CartesianGrid strokeDasharray='3 3' />
          <XAxis {...xAxisCommon} />
          <YAxis label={{ value: 'Temperature [°C]', ...yLabelCommon }} />
          <Tooltip formatter={tooltipFormatter} />
          <Legend verticalAlign='top' align='center' />
          <Line
            type='monotone'
            isAnimationActive={false}
            dataKey='tb_temp'
            name='Tileboard'
            stroke='red'
          />
          <Line
            type='monotone'
            isAnimationActive={false}
            dataKey='pulser_temp'
            name='Pulser'
            stroke='blue'
          />
        </LineChart>
      </ResponsiveContainer>
      <button onClick={showFullData}>Show stored log</button>
      <TempFullPlot plotData={plotData} show={showFull} setShow={setShowFull} />
    </div>
  );
};

type TempFullPlotProp = {
  plotData: TempDataEntry[];
  show: boolean;
  setShow: (c: boolean) => void;
};
const TempFullPlot = ({ plotData, show, setShow }: TempFullPlotProp) => {
  if (!show) return <></>;

  const closeFloat = () => {
    setShow(false);
  };

  const cont_sty = { backgroundColor: '#FFCCCC' };
  return (
    <div style={cont_sty} className='overlayFloat'>
      <h2>Temperature Log</h2>
      <a href='/download/json/monitorLog' download>
        Download monitor log
      </a>
      <button className='floatClose' onClick={closeFloat}>
        x
      </button>
      <ResponsiveContainer width='100%' height={800} key={`full_temp_${plotData.length}`}>
        <LineChart {...outerLayout} data={plotData}>
          <CartesianGrid strokeDasharray='3 3' />
          <XAxis {...xAxisCommon} />
          <YAxis label={{ value: 'Temperature [°C]', ...yLabelCommon }} />
          <Tooltip formatter={tooltipFormatter} />
          <Legend verticalAlign='top' align='center' />
          <Line
            type='monotone'
            isAnimationActive={false}
            dataKey='tb_temp'
            name='Tileboard'
            stroke='red'
          />
          <Line
            type='monotone'
            isAnimationActive={false}
            dataKey='pulser_temp'
            name='Pulser'
            stroke='blue'
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

type VoltDataEntry = {
  time: Date;
  pulser_lv: number;
  pulser_hv: number;
  tb_sipm_bias: number;
  tb_led_bias: number;
};

export const VoltMonitorStatus = () => {
  const { telemetryLogs } = useGlobalSession();
  const [plotData, setPlotData] = useState<VoltDataEntry[]>([]);
  const [showFull, setShowFull] = useState<boolean>(false);

  useEffect(() => {
    setPlotData((old_data: VoltDataEntry[]): VoltDataEntry[] => {
      return telemetryLogs.map((x) => {
        return {
          time: timestampToDate(x.timestamp),
          pulser_lv: x.gmq_pulser_lv,
          pulser_hv: x.gmq_pulser_hv / 100,
          tb_sipm_bias: x.tb_sipm_bias,
          tb_led_bias: x.tb_led_bias,
        };
      });
    });
  }, [telemetryLogs]);

  const toggleShowFull = () => {
    setShowFull(true);
  };

  // Creating the plotting scripts using the data set
  return (
    <div>
      <h3>Subsystem - Voltage monitor</h3>
      <ResponsiveContainer
        width='100%'
        height={200}
        key={`volt_brief_${plotData.slice(-100).length}`}
      >
        <LineChart {...outerLayout} data={plotData.slice(-100)}>
          <CartesianGrid strokeDasharray='3 3' />
          <XAxis {...xAxisCommon} />
          <YAxis label={{ value: 'Voltage [mV]', ...yLabelCommon }} />
          <Tooltip formatter={tooltipFormatter} />
          <Legend verticalAlign='top' align='center' />
          <Line
            type='monotone'
            isAnimationActive={false}
            dataKey='pulser_lv'
            name='Pulser board low voltage'
            stroke='green'
          />
          <Line
            type='monotone'
            isAnimationActive={false}
            dataKey='pulser_hv'
            name='Pulser board high voltage (/100)'
            stroke='blue'
          />
        </LineChart>
      </ResponsiveContainer>
      <button onClick={toggleShowFull}>Show stored log</button>
      <VoltFullPlot plotData={plotData} show={showFull} setShow={setShowFull} />
    </div>
  );
};

type VoltFullPlotProp = {
  plotData: VoltDataEntry[];
  show: boolean;
  setShow: (c: boolean) => void;
};
const VoltFullPlot = ({ plotData, show, setShow }: VoltFullPlotProp) => {
  if (!show) return <></>;

  const closeFloat = () => {
    setShow(false);
  };
  const cont_sty = { backgroundColor: '#CCCCFF' };

  return (
    <div style={cont_sty} className='overlayFloat'>
      <h2>Temperature Log</h2>
      <a href='/download/json/monitorLog' download>
        Download monitor log
      </a>
      <button className='floatClose' onClick={closeFloat}>
        x
      </button>
      <ResponsiveContainer width='100%' height={800} key={`full_temp_${plotData.length}`}>
        <LineChart {...outerLayout} data={plotData}>
          <XAxis {...xAxisCommon} />
          <YAxis label={{ value: 'Voltage [mV]', ...yLabelCommon }} />
          <Tooltip formatter={tooltipFormatter} />
          <Legend verticalAlign='top' align='center' />
          <Line
            type='monotone'
            isAnimationActive={false}
            dataKey='pulser_lv'
            name='Pulser board low voltage'
            stroke='green'
          />
          <Line
            type='monotone'
            isAnimationActive={false}
            dataKey='pulser_hv'
            name='Pulser board high voltage (/100)'
            stroke='blue'
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
