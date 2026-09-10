// ECharts 主题：与设计令牌保持一致（藏青 / 琥珀 / 青灰）
import * as echarts from "echarts";

echarts.registerTheme("ebtcm", {
  color: ["#2a6094", "#e0a83f", "#5b9a8b", "#c8403e", "#7b8cae", "#a67c52", "#4f77a0", "#d9b26f"],
  backgroundColor: "transparent",
  textStyle: { fontFamily: "-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif", color: "#4d5c70" },
  title: { textStyle: { color: "#1a2433", fontWeight: 600 } },
  legend: { textStyle: { color: "#4d5c70" }, itemWidth: 12, itemHeight: 12, icon: "roundRect" },
  tooltip: {
    backgroundColor: "rgba(26, 36, 51, 0.92)", borderWidth: 0, textStyle: { color: "#fff", fontSize: 12 },
    padding: [8, 12], extraCssText: "border-radius: 8px; box-shadow: 0 4px 16px rgba(16,32,56,.18);",
  },
  categoryAxis: {
    axisLine: { lineStyle: { color: "#e3e8ef" } }, axisTick: { show: false },
    axisLabel: { color: "#8492a6", fontSize: 11 }, splitLine: { show: false },
  },
  valueAxis: {
    axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: "#8492a6", fontSize: 11 },
    splitLine: { lineStyle: { color: "#eef1f5" } },
  },
  line: { smooth: true, symbol: "circle", symbolSize: 5, lineStyle: { width: 2.5 }, itemStyle: { borderWidth: 2, borderColor: "#fff" } },
  bar: { itemStyle: { borderRadius: [0, 4, 4, 0] }, barMaxWidth: 22 },
  pie: { itemStyle: { borderColor: "#fff", borderWidth: 2 }, label: { color: "#4d5c70", fontSize: 11 } },
});

export default echarts;
