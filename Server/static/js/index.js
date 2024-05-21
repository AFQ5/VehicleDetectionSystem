document.addEventListener("DOMContentLoaded", function () {
  // Positioning Spots and Adding Numbers
  positionSpots("#section-A", 197.5, 50);
  positionSpots("#section-B1", 137, 139);
  positionSpots("#section-B2", 137, 163);
  positionSpots("#section-C1", 137, 253);
  positionSpots("#section-C2", 137, 228);
  positionSpots("#section-D", 292, 323);
  positionSpots("#section-E", 63, 86.5, true);

  // Fetch and Update Spot Colors initially and then every 5 seconds
  fetchSpotsData();
  setInterval(fetchSpotsData, 5000);
});

/**
 * Fetches spot data from the server and updates the spot colors and paths.
 */
function fetchSpotsData() {
  fetch("/spots")
    .then((response) => response.json())
    .then((data) => {
      console.log("Fetched data:", data);
      updateSpotColors(data);
      updatePathForOccupiedSpots(data);
    })
    .catch((error) => console.error("Error fetching spots data:", error));
}

/**
 * Positions spots within a section and optionally rotates them.
 *
 * @param {string} sectionSelector - The CSS selector for the section.
 * @param {number} initialX - The initial X position for the spots.
 * @param {number} initialY - The initial Y position for the spots.
 * @param {boolean} [rotate=false] - Whether to rotate the spots.
 */
function positionSpots(sectionSelector, initialX, initialY, rotate = false) {
  const spots = document.querySelectorAll(sectionSelector + " .spot");
  spots.forEach((spot, index) => {
    let x = initialX;
    let y = initialY;

    if (sectionSelector === "#section-E") {
      y += 11.4 * index;
    } else if (sectionSelector === "#section-A") {
      x += 11 * index;
    } else {
      x += 11.1 * index;
    }

    spot.setAttribute("x", x);
    spot.setAttribute("y", y);
    spot.setAttribute("data-spot-number", index + 1); // Adding data attribute

    if (rotate && sectionSelector === "#section-E") {
      const rotationAngle = -90;
      spot.setAttribute("transform", `rotate(${rotationAngle} ${x} ${y})`);
    }
  });
}

/**
 * Updates the colors of spots based on their status.
 *
 * @param {Array} data - The array of spot data from the server.
 */
function updateSpotColors(data) {
  const svg = document.querySelector("svg");
  const spots = svg.querySelectorAll(".spot");

  // Reset all spots to gray before updating
  spots.forEach((spot) => {
    spot.style.fill = "darkgray";
  });

  data.forEach((spot) => {
    const section = spot.section.replace("_", "-"); // Replace underscore with hyphen
    const spotNumber = spot.spot_number;
    const status = spot.status;

    const spotElement = document.querySelector(
      `#${section} [data-spot-number="${spotNumber}"]`
    );

    if (spotElement) {
      if (status === "occupied") {
        spotElement.style.fill = "red";
      } else if (status === "available") {
        spotElement.style.fill = "cyan";
      } else {
        spotElement.style.fill = "gray";
      }
    } else {
      console.log(
        `Spot element not found for Section ${section}, Spot ${spotNumber}`
      ); // Debugging statement
    }
  });
}

/**
 * Updates the paths for occupied spots.
 *
 * @param {Array} data - The array of spot data from the server.
 */
function updatePathForOccupiedSpots(data) {
  data.forEach((spot) => {
    const section = spot.section.replace("_", "-"); // Replace underscore with hyphen
    const spotNumber = spot.spot_number;
    const status = spot.status;

    if (status === "occupied") {
      // Remove the path for the occupied spot
      removePathForSpot(section, spotNumber);

      // Find the nearest free spot and update the path
      const nearestFreeSpot = findNearestFreeSpot(data, section, spotNumber);
      if (nearestFreeSpot) {
        drawPathToSpot(
          section,
          spotNumber,
          nearestFreeSpot.section,
          nearestFreeSpot.spot_number
        );
      }
    }
  });
}

/**
 * Removes the path for a specific spot.
 *
 * @param {string} section - The section ID.
 * @param {number} spotNumber - The spot number.
 */
function removePathForSpot(section, spotNumber) {
  const svg = document.querySelector("svg");
  const pathId = `path-${section}-${spotNumber}`;
  const pathElement = document.getElementById(pathId);
  if (pathElement) {
    svg.removeChild(pathElement);
  }
}

/**
 * Finds the nearest free spot to a given spot by checking adjacent spots in the same section.
 *
 * @param {Array} data - The array of spot data.
 * @param {string} section - The section ID of the current spot.
 * @param {number} spotNumber - The spot number of the current spot.
 * @returns {Object|null} - The nearest free spot data or null if no free spot found.
 */
function findNearestFreeSpot(data, section, spotNumber) {
  let nearestSpot = null;

  // Check adjacent spots in the same section, increasing the distance incrementally
  for (let offset = 1; offset < data.length; offset++) {
    const candidateBefore = data.find(
      (spot) =>
        spot.section === section &&
        spot.spot_number === spotNumber - offset &&
        spot.status === "available"
    );
    const candidateAfter = data.find(
      (spot) =>
        spot.section === section &&
        spot.spot_number === spotNumber + offset &&
        spot.status === "available"
    );

    if (candidateBefore) {
      return candidateBefore;
    }

    if (candidateAfter) {
      return candidateAfter;
    }
  }

  return nearestSpot;
}

/**
 * Draws a path to a specific spot.
 *
 * @param {string} fromSection - The section ID of the starting spot.
 * @param {number} fromSpotNumber - The spot number of the starting spot.
 * @param {string} toSection - The section ID of the destination spot.
 * @param {number} toSpotNumber - The spot number of the destination spot.
 */
function drawPathToSpot(fromSection, fromSpotNumber, toSection, toSpotNumber) {
  const svg = document.querySelector("svg");
  const fromSpot = document.querySelector(
    `#${fromSection} [data-spot-number="${fromSpotNumber}"]`
  );
  const toSpot = document.querySelector(
    `#${toSection} [data-spot-number="${toSpotNumber}"]`
  );

  if (fromSpot && toSpot) {
    const fromX = parseFloat(fromSpot.getAttribute("x"));
    const fromY = parseFloat(fromSpot.getAttribute("y"));
    const toX = parseFloat(toSpot.getAttribute("x"));
    const toY = parseFloat(toSpot.getAttribute("y"));

    // Example: Three segments for the path
    drawPath(svg, 421, 134, fromX, fromY); // From entry/exit to the occupied spot
    drawPath(svg, fromX, fromY, fromX, toY); // From occupied spot to the same X as free spot
    drawPath(svg, fromX, toY, toX, toY); // From the same X as free spot to the free spot
  }
}

/**
 * Draws a path between two points in the SVG.
 *
 * @param {SVGElement} svg - The SVG element.
 * @param {number} startX - The starting X coordinate.
 * @param {number} startY - The starting Y coordinate.
 * @param {number} endX - The ending X coordinate.
 * @param {number} endY - The ending Y coordinate.
 */
function drawPath(svg, startX, startY, endX, endY) {
  let pathD = `M ${startX} ${startY} `;
  pathD += `L ${endX} ${endY}`;

  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", pathD);
  path.setAttribute("stroke", "red");
  path.setAttribute("stroke-linecap", "round"); // Cap the lines to prevent sharp corners
  path.setAttribute("stroke-linejoin", "round"); // Smooth corners
  svg.appendChild(path);
}

function addNumberToSpot(svg, index, x, y, width) {
  const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
  text.setAttribute("class", "spot-text");
  text.setAttribute("x", x + width / 2);
  text.setAttribute("y", y + 10);
  text.setAttribute("fill", "black");
  text.setAttribute("font-family", "Arial");
  text.setAttribute("font-size", "8");
  text.setAttribute("text-anchor", "middle");
  text.setAttribute("dominant-baseline", "middle");
  text.setAttribute("style", "pointer-events: none; user-select: none;");
  text.textContent = index + 1;
  svg.appendChild(text);
  return text;
}

document.addEventListener("DOMContentLoaded", function () {
  const svg = document.querySelector("svg");
  const sections = [
    "#section-A .spot",
    "#section-B1 .spot",
    "#section-B2 .spot",
    "#section-C1 .spot",
    "#section-C2 .spot",
    "#section-D .spot",
    "#section-E .spot",
  ];

  sections.forEach((section) => {
    const spots = document.querySelectorAll(section);
    spots.forEach((spot, index) => {
      const x = parseFloat(spot.getAttribute("x"));
      const y = parseFloat(spot.getAttribute("y"));
      const width = parseFloat(window.getComputedStyle(spot).width);
      let offsetX = 0,
        offsetY = 0;

      if (section.includes("#section-E")) {
        offsetX = 4;
        offsetY = -14;
      } else {
        offsetX = -0.5;
      }

      const text = addNumberToSpot(svg, index, x + offsetX, y + offsetY, width);

      spot.addEventListener("mouseover", function () {
        text.setAttribute("fill", "white");
      });
      spot.addEventListener("mouseout", function () {
        text.setAttribute("fill", "black");
      });
    });
  });
});

// Adding Entry/Exit Points:
document.addEventListener("DOMContentLoaded", function () {
  const points = document.querySelectorAll("#entry-exit");
  points.forEach((point) => {
    const x = 421;
    const y = 134;

    point.setAttribute("x", x);
    point.setAttribute("y", y);

    const xt = x + 10.5;
    const yt = y + 25;

    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("x", xt);
    text.setAttribute("y", yt);
    text.setAttribute("fill", "white");
    text.setAttribute("font-family", "Arial");
    text.setAttribute("font-size", "8");
    text.setAttribute("text-anchor", "middle");
    text.setAttribute("dominant-baseline", "central");
    text.setAttribute("style", "user-select: none;");

    const tspan1 = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "tspan"
    );
    tspan1.innerHTML = "entry";
    tspan1.setAttribute("x", xt);
    tspan1.setAttribute("dy", "-10");
    text.appendChild(tspan1);

    const tspan2 = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "tspan"
    );
    tspan2.innerHTML = "/";
    tspan2.setAttribute("x", xt);
    tspan2.setAttribute("dy", "10");
    text.appendChild(tspan2);

    const tspan3 = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "tspan"
    );
    tspan3.innerHTML = "exit";
    tspan3.setAttribute("x", xt);
    tspan3.setAttribute("dy", "10");
    text.appendChild(tspan3);

    point.addEventListener("mouseover", function () {
      text.setAttribute("fill", "black");
    });

    point.addEventListener("mouseout", function () {
      text.setAttribute("fill", "white");
    });

    point.parentNode.insertBefore(text, point.nextSibling);
  });
});

/**
 * Adds click event listener to spots for routing paths.
 */
document.addEventListener("DOMContentLoaded", function () {
  const svg = document.getElementById("parkingMap");
  const waypoints = [
    { id: 1, x: 430, y: 132 },
    { id: 2, x: 430, y: 110 },
    { id: 3, x: 380, y: 110 },
    { id: 4, x: 102, y: 110 },
    { id: 5, x: 380, y: 202 },
    { id: 6, x: 380, y: 297 },
  ];

  const routingPaths = {
    A: [1, 2, 3],
    B1: [1, 2, 3],
    E: [1, 2, 3, 4],
    B2: [1, 2, 3, 5],
    C2: [1, 2, 3, 5],
    C1: [1, 2, 3, 5, 6],
    D: [1, 2, 3, 5, 6],
  };

  // Set initial colors to gray if no info available
  setGrayForMissingInfo(routingPaths);

  let lastClickedSpot = null; // Variable to keep track of the last clicked spot

  svg.addEventListener("click", function (event) {
    const spot = event.target;
    const section = spot.parentNode.id.replace("section-", "");
    const pathIds = routingPaths[section];

    if (spot.classList.contains("spot")) {
      const spotColor = spot.style.fill;

      console.log("Clicked spot color:", spotColor); // Log the spot color for debugging

      if (
        spotColor.toLowerCase() === "red" ||
        spotColor.toLowerCase() === "darkred"
      ) {
        alert("This spot is occupied and cannot be routed.");
        event.preventDefault(); // Prevent default click behavior if spot color is red
        return; // Exit the event listener early if the spot is red
      } else {
        console.log("Spot clicked successfully.");
        // Add your click handling logic here
      }

      if (lastClickedSpot === spot) {
        // If the same spot is clicked, remove all paths
        while (svg.lastChild.tagName === "path") {
          svg.removeChild(svg.lastChild);
        }
        lastClickedSpot = null; // Reset the last clicked spot
        return;
      }

      lastClickedSpot = spot; // Update the last clicked spot

      if (!pathIds) return;

      while (svg.lastChild.tagName === "path") {
        svg.removeChild(svg.lastChild);
      }

      let lastX = waypoints[pathIds[0] - 1].x;
      let lastY = waypoints[pathIds[0] - 1].y;

      pathIds.slice(1).forEach((id) => {
        const waypoint = waypoints[id - 1];
        drawPath(svg, lastX, lastY, waypoint.x, waypoint.y);
        lastX = waypoint.x;
        lastY = waypoint.y;
      });

      const spotX = parseFloat(spot.getAttribute("x"));
      const spotY = parseFloat(spot.getAttribute("y"));

      if (section === "E") {
        drawPath(svg, lastX, lastY, lastX, spotY - 5);
        drawPath(svg, lastX, spotY - 5, spotX + 19, spotY - 5);
      } else if (section === "A" || section === "B2" || section === "C1") {
        drawPath(svg, lastX, lastY, spotX + 5, lastY);
        drawPath(svg, spotX + 5, lastY, spotX + 5, spotY + 19);
      } else {
        // Handle other sections similarly if needed
        drawPath(svg, lastX, lastY, spotX + 5, lastY);
        drawPath(svg, spotX + 5, lastY, spotX + 5, spotY);
      }
    }
  });

  /**
   * Draws a path between two points in the SVG.
   *
   * @param {SVGElement} svg - The SVG element.
   * @param {number} startX - The starting X coordinate.
   * @param {number} startY - The starting Y coordinate.
   * @param {number} endX - The ending X coordinate.
   * @param {number} endY - The ending Y coordinate.
   */
  function drawPath(svg, startX, startY, endX, endY) {
    let pathD = `M ${startX} ${startY} `;
    pathD += `L ${endX} ${endY}`;

    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", pathD);
    path.setAttribute("stroke", "red");
    path.setAttribute("stroke-linecap", "round"); // Cap the lines to prevent sharp corners
    path.setAttribute("stroke-linejoin", "round"); // Smooth corners
    svg.appendChild(path);
  }

  /**
   * Changes the fill color of a specific spot.
   *
   * @param {string} sectionId - The section ID.
   * @param {number} spotIndex - The index of the spot.
   * @param {number} colorCode - The color code (1 for red, 0 for cyan, default for darkgray).
   */
  function changeSpotFillColor(sectionId, spotIndex, colorCode) {
    const section = document.getElementById(`section-${sectionId}`);

    if (!section) {
      console.error(`Section '${sectionId}' not found.`);
      return;
    }

    const spots = section.querySelectorAll(".spot");

    if (spotIndex < 0 || spotIndex >= spots.length) {
      console.error(`Invalid spot index ${spotIndex} for section ${sectionId}`);
      return;
    }

    const color =
      colorCode === 1 ? "red" : colorCode === 0 ? "cyan" : "darkgray"; // Change the color code as needed

    const spot = spots[spotIndex - 1];
    spot.style.fill = color;
  }

  /**
   * Sets the fill color to gray for spots without information.
   *
   * @param {Object} routingPaths - The routing paths for each section.
   */
  function setGrayForMissingInfo(routingPaths) {
    Object.keys(routingPaths).forEach((sectionId) => {
      const section = document.getElementById(`section-${sectionId}`);
      if (section) {
        const spots = section.querySelectorAll(".spot");
        spots.forEach((spot) => {
          if (!spot.style.fill) {
            spot.style.fill = "darkgray"; // Set to gray if no color information is available
          }
          spot.addEventListener("mouseover", function () {
            if (spot.style.fill === "darkgray") {
              spot.style.fill = "gray"; // Change to a darker gray on hover
            } else if (spot.style.fill === "red") {
              spot.style.fill = "darkred"; // Change to a darker red on hover
            } else if (spot.style.fill === "cyan") {
              spot.style.fill = "darkcyan"; // Change to a darker cyan on hover
            }
          });
          spot.addEventListener("mouseout", function () {
            if (spot.style.fill === "gray") {
              spot.style.fill = "darkgray"; // Revert back to gray when not hovering
            } else if (spot.style.fill === "darkred") {
              spot.style.fill = "red"; // Revert back to red when not hovering
            } else if (spot.style.fill === "darkcyan") {
              spot.style.fill = "cyan"; // Revert back to cyan when not hovering
            }
          });
        });
      }
    });
  }
});
