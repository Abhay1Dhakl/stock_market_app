type PriceTrendPoint = {
  trading_date: string;
  close_price: number;
  volume: number;
};

type PriceTrendChartProps = {
  points: PriceTrendPoint[];
};

export function PriceTrendChart({ points }: PriceTrendChartProps) {
  if (points.length === 0) {
    return <p className="muted">No recent price rows are available for charting.</p>;
  }

  const width = 720;
  const height = 280;
  const left = 18;
  const right = 18;
  const top = 20;
  const bottom = 42;
  const innerWidth = width - left - right;
  const innerHeight = height - top - bottom;

  const closes = points.map((point) => point.close_price);
  const volumes = points.map((point) => point.volume);
  const minClose = Math.min(...closes);
  const maxClose = Math.max(...closes);
  const maxVolume = Math.max(...volumes, 1);
  const closeRange = maxClose - minClose || 1;
  const stepX = points.length > 1 ? innerWidth / (points.length - 1) : innerWidth;

  const path = points
    .map((point, index) => {
      const x = left + index * stepX;
      const y = top + innerHeight * (1 - (point.close_price - minClose) / closeRange);
      return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(" ");

  const areaPath = `${path} L ${(left + innerWidth).toFixed(2)} ${(top + innerHeight).toFixed(2)} L ${left.toFixed(2)} ${(top + innerHeight).toFixed(2)} Z`;

  return (
    <div className="trend-chart">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        aria-label="Thirty day close price trend"
        className="trend-chart__svg"
        role="img"
      >
        <defs>
          <linearGradient id="price-area" x1="0%" x2="0%" y1="0%" y2="100%">
            <stop offset="0%" stopColor="rgba(15, 98, 254, 0.28)" />
            <stop offset="100%" stopColor="rgba(15, 98, 254, 0.02)" />
          </linearGradient>
        </defs>

        {[0, 1, 2, 3].map((gridLine) => {
          const y = top + (innerHeight / 3) * gridLine;
          return <line key={gridLine} className="trend-chart__grid" x1={left} x2={left + innerWidth} y1={y} y2={y} />;
        })}

        {points.map((point, index) => {
          const x = left + index * stepX;
          const barHeight = (point.volume / maxVolume) * 54;
          return (
            <g key={point.trading_date}>
              <line
                className="trend-chart__bar"
                x1={x}
                x2={x}
                y1={top + innerHeight}
                y2={top + innerHeight - barHeight}
              />
              {index === 0 || index === points.length - 1 || index % 6 === 0 ? (
                <text className="trend-chart__label" x={x} y={height - 12}>
                  {formatTickDate(point.trading_date)}
                </text>
              ) : null}
            </g>
          );
        })}

        <path d={areaPath} fill="url(#price-area)" />
        <path className="trend-chart__line" d={path} />

        {points.map((point, index) => {
          const x = left + index * stepX;
          const y = top + innerHeight * (1 - (point.close_price - minClose) / closeRange);
          return <circle key={`${point.trading_date}-close`} className="trend-chart__dot" cx={x} cy={y} r={3.5} />;
        })}

        <text className="trend-chart__axis-value" x={left} y={top - 2}>
          Rs. {maxClose.toFixed(2)}
        </text>
        <text className="trend-chart__axis-value" x={left} y={top + innerHeight + 18}>
          Rs. {minClose.toFixed(2)}
        </text>
      </svg>
    </div>
  );
}

function formatTickDate(value: string): string {
  const date = new Date(value);
  return `${date.getMonth() + 1}/${date.getDate()}`;
}
