import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default marker icons in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

const MapView = ({ gapAreas = [], providers = [], center = [36.7783, -119.4179], zoom = 6 }) => {
  const getSeverityColor = (severity) => {
    const colors = {
      'Critical': '#dc2626',
      'High': '#ea580c',
      'Medium': '#eab308',
      'Low': '#16a34a',
    };
    return colors[severity] || '#0284c7';
  };

  const getSeverityRadius = (severity) => {
    const radii = {
      'Critical': 50000,
      'High': 35000,
      'Medium': 25000,
      'Low': 15000,
    };
    return radii[severity] || 20000;
  };

  // Ensure valid coordinates
  const mapCenter = (center && center[0] && center[1]) ? center : [36.7783, -119.4179];

  return (
    <div style={{ height: '600px', width: '100%', borderRadius: '8px', overflow: 'hidden', border: '1px solid var(--border)' }}>
      <MapContainer
        center={mapCenter}
        zoom={zoom}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {/* Gap Areas as Circles */}
        {gapAreas && gapAreas.length > 0 && gapAreas.map((area) => (
          area.lat && area.lng && (
            <Circle
              key={area.id}
              center={[area.lat, area.lng]}
              radius={getSeverityRadius(area.severity)}
              pathOptions={{
                color: getSeverityColor(area.severity),
                fillColor: getSeverityColor(area.severity),
                fillOpacity: 0.2,
                weight: 2,
              }}
            >
              <Popup>
                <div style={{ padding: '8px', minWidth: '200px' }}>
                  <h4 style={{ margin: '0 0 8px 0', color: '#1e293b', fontSize: '14px', fontWeight: '600' }}>
                    {area.county}, {area.state}
                  </h4>
                  <p style={{ margin: '4px 0', fontSize: '13px', color: '#64748b' }}>
                    <strong>Specialty:</strong> {area.specialty}
                  </p>
                  <p style={{ margin: '4px 0', fontSize: '13px', color: '#64748b' }}>
                    <strong>Gap Score:</strong> {area.gapScore}
                  </p>
                  <p style={{ margin: '4px 0', fontSize: '13px', color: '#64748b' }}>
                    <strong>Severity:</strong> <span style={{ color: getSeverityColor(area.severity), fontWeight: '600' }}>{area.severity}</span>
                  </p>
                  <p style={{ margin: '4px 0', fontSize: '13px', color: '#64748b' }}>
                    <strong>Provider Deficit:</strong> {area.deficit}
                  </p>
                </div>
              </Popup>
            </Circle>
          )
        ))}
        
        {/* Provider Locations as Markers */}
        {providers && providers.length > 0 && providers.map((provider) => (
          provider.lat && provider.lng && (
            <Marker key={provider.id} position={[provider.lat, provider.lng]}>
              <Popup>
                <div style={{ padding: '8px' }}>
                  <h4 style={{ margin: '0 0 8px 0' }}>{provider.name}</h4>
                  <p style={{ margin: '4px 0', fontSize: '0.9rem' }}>
                    <strong>Specialty:</strong> {provider.specialty}
                  </p>
                  <p style={{ margin: '4px 0', fontSize: '0.9rem' }}>
                    <strong>Location:</strong> {provider.location}
                  </p>
                  <p style={{ margin: '4px 0', fontSize: '0.9rem' }}>
                    <strong>Patients:</strong> {provider.patients}
                  </p>
                </div>
              </Popup>
            </Marker>
          )
        ))}
      </MapContainer>
    </div>
  );
};

export default MapView;
