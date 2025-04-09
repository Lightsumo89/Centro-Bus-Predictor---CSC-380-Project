document.addEventListener('DOMContentLoaded', function() {
  const map = L.map('map').setView([43.455, -76.532], 13);
  
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19
  }).addTo(map);
  
  const routeColors = {
    'Walmart Via 104': '#e74c3c',
    'Price Chopper': '#3498db',
    'Blue Route': '#2980b9',
    'Green Route': '#27ae60',
    'Oswego - Syracuse': '#f39c12',
    'SY76': '#8e44ad'
  };
  
  const routeLayers = {};

  function fetchStops(route = 'all') {
    fetch(`/api/stops/${route}`)
      .then(response => response.json())
      .then(data => {
        console.log('Fetched stops data:', data);  
        plotStopsOnMap(data);  
      })
      .catch(error => console.error('Error fetching stops:', error));
  }

  function plotStopsOnMap(stops) {
    stops.forEach(stop => {
      const marker = L.circleMarker([stop.stop_lat, stop.stop_lon], {
        radius: 6,
        fillColor: '#3498db',  
        color: '#fff',
        weight: 1,
        opacity: 1,
        fillOpacity: 0.8
      });

      marker.bindPopup(`
        <strong>Stop ID: ${stop.stop_id}</strong><br>
        Route: ${stop.Route}<br>
        <button class="show-times-btn" data-stop="${stop.stop_id}" data-route="${stop.Route}">
          Show Bus Times
        </button>
      `);

      marker.addTo(map);
    });
  }
  
  function fetchPredictions(stopId) {
    fetch(`/api/prediction/${stopId}`)
      .then(response => response.json())
      .then(data => {
        const predictionInfo = document.getElementById('prediction-info');
        const predictionContent = document.getElementById('prediction-content');
        
        predictionInfo.style.display = 'block';
        
        let html = `<h4>Stop ID: ${stopId}</h4>`;
        if (data.predictions) {
          html += '<p>Upcoming buses:</p><ul>';
          data.predictions.forEach(pred => {
            const statusClass = pred.on_time ? 'on-time' : 'delayed';
            html += `<li class="${statusClass}">
              Arrives in ${pred.minutes_away} minutes (${pred.arrival_time})
              - Bus ${pred.bus_id} ${pred.on_time ? '(On time)' : '(Delayed)'}</li>`;
          });
          html += '</ul>';
        } else {
          html += '<p>No predictions available for this stop.</p>';
        }
        
        html += `<p><small>Last updated: ${data.predictions[0]?.last_updated || 'N/A'}</small></p>`;
        
        predictionContent.innerHTML = html;
      })
      .catch(error => console.error('Error fetching predictions:', error));
  }

  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(function(position) {
      const userLat = position.coords.latitude;
      const userLon = position.coords.longitude;
      map.setView([userLat, userLon], 15);
    }, function(error) {
      console.error("Geolocation error: ", error);
      fetchStops();
    });
  } else {
    fetchStops();
  }

  document.getElementById('route-selector').addEventListener('change', function() {
    const selectedRoute = this.value;
    fetchStops(selectedRoute);
  });
  
  fetchStops();  
});
