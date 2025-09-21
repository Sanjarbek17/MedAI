# Ambulance Dispatch System API

## Overview
This API provides endpoints for managing an ambulance dispatch system with real-time WebSocket communication between patients and drivers.

## Base URL
```
http://localhost:8080
```

## WebSocket URL
```
ws://localhost:8080
```

## API Endpoints

### System Status
```bash
GET /api/system/status
```
Returns overall system status and statistics.

### Patient APIs

#### 1. Get Patient Interface Configuration
```bash
GET /api/patient
```

#### 2. Register Patient
```bash
POST /api/patient/register
Content-Type: application/json

{
  "patient_id": "optional-custom-id",
  "location": {
    "lat": 40.7128,
    "lng": -74.0060
  }
}
```

#### 3. Create Emergency Request
```bash
POST /api/patient/emergency
Content-Type: application/json

{
  "patient_id": "77578e58-5378-4466-82e7-97d80fd5a804",
  "location": {
    "lat": 40.7128,
    "lng": -74.0060
  },
  "emergency_type": "cardiac"
}
```

#### 4. Get Patient Status
```bash
GET /api/patient/status/{patient_id}
```

### Driver APIs

#### 1. Get Driver Interface Configuration
```bash
GET /api/driver
```

#### 2. Register Driver
```bash
POST /api/driver/register
Content-Type: application/json

{
  "driver_id": "optional-custom-id",
  "location": {
    "lat": 40.7589,
    "lng": -73.9851
  }
}
```

#### 3. Get Pending Requests
```bash
GET /api/driver/requests
```

#### 4. Get Driver Status
```bash
GET /api/driver/status/{driver_id}
```

## WebSocket Events

### Client to Server Events

#### Register Patient
```javascript
socket.emit('register_patient', {
  patient_id: 'your-patient-id',
  location: { lat: 40.7128, lng: -74.0060 }
});
```

#### Register Driver
```javascript
socket.emit('register_driver', {
  driver_id: 'your-driver-id',
  location: { lat: 40.7589, lng: -73.9851 }
});
```

#### Emergency Request
```javascript
socket.emit('emergency_request', {
  patient_id: 'your-patient-id',
  location: { lat: 40.7128, lng: -74.0060 },
  emergency_type: 'cardiac'
});
```

#### Accept Request (Driver)
```javascript
socket.emit('accept_request', {
  driver_id: 'your-driver-id',
  request_id: 'emergency-request-id'
});
```

#### Update Location
```javascript
socket.emit('update_location', {
  user_id: 'your-user-id',
  location: { lat: 40.7128, lng: -74.0060 },
  user_type: 'patient' // or 'driver'
});
```

### Server to Client Events

#### Driver Assigned (Patient receives)
```javascript
socket.on('driver_assigned', (data) => {
  console.log('Driver assigned:', data);
  // data contains driver_id, driver_location, estimated_arrival
});
```

#### Emergency Alert (Driver receives)
```javascript
socket.on('emergency_alert', (data) => {
  console.log('Emergency alert:', data);
  // data contains request_id, patient_location, emergency_type, distance
});
```

#### Location Updates
```javascript
// Patient receives driver location updates
socket.on('driver_location_update', (data) => {
  console.log('Driver location:', data.driver_location);
});

// Driver receives patient location updates
socket.on('patient_location_update', (data) => {
  console.log('Patient location:', data.patient_location);
});
```

## Example Usage

### Complete Patient Flow
```bash
# 1. Register patient
curl -X POST http://localhost:8080/api/patient/register \
  -H "Content-Type: application/json" \
  -d '{"location": {"lat": 40.7128, "lng": -74.0060}}'

# Response: {"patient_id": "abc123", "success": true, ...}

# 2. Create emergency request
curl -X POST http://localhost:8080/api/patient/emergency \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "abc123",
    "location": {"lat": 40.7128, "lng": -74.0060},
    "emergency_type": "cardiac"
  }'

# 3. Connect to WebSocket for real-time updates
# 4. Listen for driver_assigned, driver_location_update, ambulance_arrived events
```

### Complete Driver Flow
```bash
# 1. Register driver
curl -X POST http://localhost:8080/api/driver/register \
  -H "Content-Type: application/json" \
  -d '{"location": {"lat": 40.7589, "lng": -73.9851}}'

# Response: {"driver_id": "xyz789", "success": true, ...}

# 2. Get pending requests
curl http://localhost:8080/api/driver/requests

# 3. Connect to WebSocket
# 4. Listen for emergency_alert events
# 5. Send accept_request or decline_request events
```

## Testing the System

### Start the Server
```bash
python app.py
```

### Test API Endpoints
```bash
# Get API documentation
curl http://localhost:8080/api

# Check system status
curl http://localhost:8080/api/system/status

# Register a patient
curl -X POST http://localhost:8080/api/patient/register \
  -H "Content-Type: application/json" \
  -d '{"location": {"lat": 40.7128, "lng": -74.0060}}'

# Register a driver
curl -X POST http://localhost:8080/api/driver/register \
  -H "Content-Type: application/json" \
  -d '{"location": {"lat": 40.7589, "lng": -73.9851}}'
```

### Test Web Interfaces
- Patient: http://localhost:8080/patient
- Driver: http://localhost:8080/driver
- Main: http://localhost:8080

## Error Handling

All API endpoints return JSON responses with consistent error formatting:

```json
{
  "error": "Error description",
  "success": false
}
```

Common HTTP status codes:
- 200: Success
- 400: Bad Request (missing/invalid parameters)
- 404: Not Found (patient/driver not found)
- 503: Service Unavailable (X-ray classification not available)

## Real-time Features

The system provides real-time communication through WebSocket events:

1. **Automatic Driver Matching**: Finds nearest available driver
2. **Live Location Tracking**: Real-time GPS updates
3. **Status Updates**: Instant notifications for all status changes
4. **Distance Calculation**: Accurate distance calculations using geopy
5. **Request Queue Management**: Handles multiple concurrent requests

## Integration Notes

- Use HTTPS in production
- Implement authentication/authorization
- Add rate limiting
- Use Redis for session storage in production
- Integrate with real mapping services (Google Maps, MapBox)
- Add push notifications for mobile apps
- Implement proper error logging and monitoring