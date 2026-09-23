/*
Software License Agreement (BSD)

@author    Salman Omar Sohail <support@mybotshop.de>
@copyright (c) 2025, MYBOTSHOP GmbH, Inc., All rights reserved.
*/

// Default coordinates (NRW, Germany)
var defaultLat = 50.95358;
var defaultLon = 6.60168;
var defaultZoom = 16;
var mission_counter = 0;
var coordinatesList = [];
var markers = [];
var lines = [];
var robotMarker;
var map;
var robotIcon;
var locationIcon;
var polylineDecoratorReady = false;
var arrowAnimationInterval;
var arrowPattern;


// Ensure map container has valid size
var mapContainer = document.getElementById("map");
if (!mapContainer) {
    console.error("Map container is missing");
}

document.addEventListener("DOMContentLoaded", function () {

    function loadOpenStreetMap() {
        console.log("Loading OpenStreetMap...");

        // Load Leaflet CSS
        var leafletCSS = document.createElement("link");
        leafletCSS.rel = "stylesheet";
        leafletCSS.href = "https://unpkg.com/leaflet@1.7.1/dist/leaflet.css";
        document.head.appendChild(leafletCSS);

        // Load Leaflet JS
        var leafletJS = document.createElement("script");
        leafletJS.src = "https://unpkg.com/leaflet@1.7.1/dist/leaflet.js";

        leafletJS.onload = function () {
            console.log("Leaflet loaded");

            // Load PolylineDecorator
            var decoratorScript = document.createElement("script");
            decoratorScript.src = "https://cdnjs.cloudflare.com/ajax/libs/leaflet-polylinedecorator/1.1.0/leaflet.polylineDecorator.min.js";

            decoratorScript.onload = function () {
                console.log("PolylineDecorator loaded");
                polylineDecoratorReady = true;
                initMap();
            };

            decoratorScript.onerror = function () {
                console.error("Failed to load PolylineDecorator");
                initMap();  // fallback: initialize map without arrows
            };

            document.body.appendChild(decoratorScript);
        };

        leafletJS.onerror = function () {
            console.error("Failed to load Leaflet");
            loadFallbackMap();
        };

        document.body.appendChild(leafletJS);
    }

    function loadFallbackMap() {
        console.warn("No internet! Loading fallback.");
        mapContainer.innerHTML = "<p>Offline mode: No map available.</p>";
    }

    function initMap() {
        console.log("OpenStreetMap loaded successfully.");
        map = L.map('map').setView([defaultLat, defaultLon], defaultZoom);

        // OpenStreetMap tile layer
        // L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        //     attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        //     maxZoom: 22
        // }).addTo(map);

        // Carto light tile layer
        // L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        //     attribution: '&copy; <a href="https://carto.com/">CARTO</a>',
        //     subdomains: 'abcd',
        //     maxZoom: 22
        // }).addTo(map);

        // Esri World Imagery tile layer
        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            attribution: 'Tiles &copy; Esri',
            maxZoom: 22
        }).addTo(map);

        // Show GPS coordinates on hover
        const coordsDisplay = L.control();

        coordsDisplay.onAdd = function (map) {
            this._div = L.DomUtil.create('div', 'coords-display');
            this.update();
            return this._div;
        };

        coordsDisplay.update = function (latlng) {
            this._div.innerHTML = latlng
                ? `Lat: ${latlng.lat.toFixed(5)}<br>Lon: ${latlng.lng.toFixed(5)}`
                : 'Hover over map';
        };

        coordsDisplay.addTo(map);

        map.on('mousemove', function (e) {
            coordsDisplay.update(e.latlng);
        });

        // Define icons after Leaflet is loaded
        robotIcon = L.icon({
            iconUrl: '/static/media/gps/robot.webp',
            iconSize: [42, 42],
            iconAnchor: [16, 32],
            popupAnchor: [0, -32]
        });

        locationIcon = L.icon({
            iconUrl: '/static/media/gps/location.png',
            iconSize: [20, 20],
            iconAnchor: [10, 20],
            popupAnchor: [0, -20]
        });

        // Add waypoint on click
        map.on('click', function (e) {
            addWaypoint(e.latlng);
        });

        // Prevent clicks on UI from adding waypoints
        L.DomEvent.disableClickPropagation(document.querySelector('.map-controls'));

        // Start fetching robot position
        setInterval(fetchRobotPosition, 1000);
    }

    if (navigator.onLine) {
        loadOpenStreetMap();
    } else {
        loadFallbackMap();
    }

    window.addEventListener("online", () => location.reload());
    window.addEventListener("offline", loadFallbackMap);
});

function updateRobotPosition(lat, lon) {
    if (!map) {
        console.error("Map is not initialized yet.");
        return;
    }

    if (!isNaN(lat) && !isNaN(lon)) {
        if (robotMarker) {
            robotMarker.setLatLng([lat, lon]);
        } else {
            robotMarker = L.marker([lat, lon], { icon: robotIcon }).addTo(map);
        }
        // Set map view to robot position
        // map.setView([lat, lon]);
    } else {
        console.error("Invalid position data received", lat, lon);
    }
}

function fetchRobotPosition() {
    if (!map) {
        console.error("Map is not initialized yet.");
        return;
    }

    fetch('/update_gps_position', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lat: null, lon: null }) // Request for latest position
    })
        .then(response => response.json())
        .then(data => {
            const { lat, lon } = data;
            console.log(`Fetched Position: lat: ${lat}, lon: ${lon}`);
            if (lat && lon) {
                updateRobotPosition(lat, lon);
                setTimeout(() => {
                    map.invalidateSize();
                }, 100);
            } else {
                console.error('Invalid data: Missing lat or lon');
            }
        })
        .catch(error => console.error("Error fetching robot position:", error));
}

// ✅ Add a waypoint marker (NOT draggable anymore)
function addWaypoint(latlng) {
    var marker = L.marker(latlng, {
        icon: locationIcon,
        draggable: false // ⛔ drag removed
    }).addTo(map);

    markers.push(marker);
    updateCoordinatesList();
}

// ✅ Save waypoints (send to backend)
function saveWaypoints() {
    const coords = coordinatesList.map(p => ({ lat: p.lat, lon: p.lng }));
    fetch('/save_waypoints', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(coords)
    })
        .then(response => response.text())
        .then(msg => alert("Waypoints saved successfully!"))
        .catch(err => console.error("Failed to save waypoints", err));
}

// ✅ Load waypoints (request from backend)
function loadWaypoints() {
    fetch('/load_waypoints')
        .then(response => response.json())
        .then(waypoints => {
            clearWaypoints();
            waypoints.forEach(coord => {
                addWaypoint(L.latLng(coord.lat, coord.lon));
            });
        })
        .catch(err => console.error("Failed to load waypoints", err));
}

// ✅ Maintain coordinates list and draw lines
function updateCoordinatesList() {
    coordinatesList = markers.map(marker => marker.getLatLng());
    drawLine();
}

// ✅ Draw lines between waypoints
function drawLine() {
    if (!map) {
        console.error("Map is not initialized yet.");
        return;
    }

    // Clear previous lines and animation
    lines.forEach(item => map.removeLayer(item));
    lines = [];

    if (arrowAnimationInterval) {
        clearInterval(arrowAnimationInterval);
        arrowAnimationInterval = null;
    }

    if (coordinatesList.length > 1) {
        const polyline = L.polyline(coordinatesList, {
            color: 'var(--project-light-color)',
            weight: 15,
            opacity: 0.3
        }).addTo(map);
        lines.push(polyline);

        if (polylineDecoratorReady && typeof L.Symbol !== 'undefined' && typeof L.Symbol.arrowHead === 'function') {
            // Fixed-pixel animation
            let offsetPx = 0;
            const repeatPx = 30; // Spacing between arrows in pixels

            const decorator = L.polylineDecorator(polyline, {
                patterns: [
                    {
                        offset: offsetPx + 'px',
                        repeat: repeatPx + 'px',
                        symbol: L.Symbol.arrowHead({
                            pixelSize: 10,
                            polygon: false,
                            pathOptions: { stroke: true, color: 'red', weight: 2 }
                        })
                    }
                ]
            }).addTo(map);

            lines.push(decorator);

            // Animate by shifting the offset in pixels
            arrowAnimationInterval = setInterval(() => {
                offsetPx = (offsetPx + 1) % repeatPx;
                decorator.setPatterns([
                    {
                        offset: offsetPx + 'px',
                        repeat: repeatPx + 'px',
                        symbol: L.Symbol.arrowHead({
                            pixelSize: 10,
                            polygon: false,
                            pathOptions: { stroke: true, color: 'var(--project-light-color)', weight: 2 }
                        })
                    }
                ]);
            }, 60); // Controls animation speed
        } else {
            console.warn("Arrow heads skipped: plugin not ready.");
        }
    }
}



// 🧹 Optional: Clear waypoints
function clearWaypoints() {
    markers.forEach(marker => map.removeLayer(marker));
    lines.forEach(line => map.removeLayer(line));
    if (arrowAnimationInterval) {
        clearInterval(arrowAnimationInterval);
        arrowAnimationInterval = null;
    }
    markers = [];
    lines = [];
    coordinatesList = [];
}


