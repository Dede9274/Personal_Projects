const berlinChartTimeFormatter = new Intl.DateTimeFormat("en-GB", {
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
  timeZone: "Europe/Berlin",
});

export function formatBerlinChartTime(timestamp: number): string {
  return berlinChartTimeFormatter.format(timestamp);
}
