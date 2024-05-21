document.addEventListener("DOMContentLoaded", function () {
  // Fetch analysis data initially
  fetchAnalysisData();

  // Set interval to refresh the analysis data every 5 seconds
  setInterval(fetchAnalysisData, 5000);
});

/**
 * Fetches analysis data from the server and updates the web page with the results.
 */
async function fetchAnalysisData() {
  try {
    const response = await fetch("/analysis");
    const data = await response.json();

    if (data.message) {
      document.getElementById("stats").innerHTML = `<p>${data.message}</p>`;
      return;
    }

    document.getElementById("totalSpots").innerText = data.total_spots;
    document.getElementById("occupiedSpots").innerText = data.occupied_spots;
    document.getElementById("freeSpots").innerText = data.free_spots;

    // Format and display occupancy rate
    const occupancyRate = data.occupancy_rate;
    const formattedOccupancyRate = `
    available: ${occupancyRate.available.toFixed(2)}% 
    occupied: ${occupancyRate.occupied.toFixed(2)}%`;
    document.getElementById(
      "occupancyRate"
    ).innerText = `Occupancy Rate: ${formattedOccupancyRate}`;

    // Display charts
    document.getElementById(
      "occupancyOverTimeChart"
    ).src = `data:image/png;base64,${data.occupancy_over_time_chart}`;
    document.getElementById(
      "sectionOccupancyChart"
    ).src = `data:image/png;base64,${data.section_occupancy_chart}`;
    document.getElementById(
      "durationHistogramChart"
    ).src = `data:image/png;base64,${data.duration_histogram_chart}`;
    document.getElementById(
      "dayOfWeekChart"
    ).src = `data:image/png;base64,${data.day_of_week_chart}`;
    document.getElementById(
      "occupancyRateChart"
    ).src = `data:image/png;base64,${data.occupancy_rate_chart}`;
  } catch (error) {
    console.error("Error fetching analysis data:", error);
    document.getElementById(
      "stats"
    ).innerHTML = `<p>Error fetching analysis data</p>`;
  }
}
