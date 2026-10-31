import os
import json
import time
import threading
from queue import Queue, Empty
from decimal import Decimal
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, Response
from flask.json.provider import DefaultJSONProvider
from config import Config
import db

class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

base_dir = os.path.dirname(os.path.abspath(__file__))

def resolve_folder(folder_name):
    candidates = [
        os.path.join(base_dir, folder_name),
        os.path.join(os.getcwd(), folder_name),
        os.path.join(base_dir, 'api', folder_name),
        os.path.join('/var/task', folder_name)
    ]
    for c in candidates:
        if os.path.isdir(c):
            return c
    return os.path.join(base_dir, folder_name)

app = Flask(
    __name__,
    template_folder=resolve_folder('templates'),
    static_folder=resolve_folder('static')
)
app.config.from_object(Config)
app.json = CustomJSONProvider(app)

# -------------------------------------------------------------
# Real-Time Event Broadcasting & Synchronization
# -------------------------------------------------------------
sse_subscribers = []
sse_lock = threading.Lock()
db_version = 1

def broadcast_db_event(event_type, details=None):
    """
    Broadcasts a real-time event to all connected dashboard users via SSE.
    Increments global db_version to trigger instant UI refresh across all tabs/devices.
    """
    global db_version
    with sse_lock:
        db_version += 1
        payload = {
            "version": db_version,
            "event": event_type,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        msg = f"data: {json.dumps(payload)}\n\n"
        dead_subs = []
        for q in sse_subscribers:
            try:
                q.put_nowait(msg)
            except Exception:
                dead_subs.append(q)
        for d in dead_subs:
            if d in sse_subscribers:
                sse_subscribers.remove(d)

# Ensure database is initialized on startup
with app.app_context():
    try:
        db.init_db()
    except Exception as e:
        print(f"[Warning] Failed to initialize DB on startup: {e}")

# -------------------------------------------------------------
# Web Page Route
# -------------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

# -------------------------------------------------------------
# REST API: Real-Time Synchronization & SSE Live Stream
# -------------------------------------------------------------
@app.route('/api/live-stream')
def live_stream():
    """
    Server-Sent Events (SSE) stream for real-time notifications to all connected clients.
    Whenever any client or administrator enters or alters data, an instant event is streamed.
    """
    if os.environ.get('VERCEL'):
        def vercel_generator():
            init_payload = {
                "version": db_version,
                "event": "CONNECTED",
                "details": {"message": "Vercel Serverless Sync Active"},
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(init_payload)}\n\n"
        return Response(
            vercel_generator(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*'
            }
        )
    def event_generator():
        q = Queue(maxsize=100)
        with sse_lock:
            sse_subscribers.append(q)
        try:
            # Send initial connection handshake
            init_payload = {
                "version": db_version,
                "event": "CONNECTED",
                "details": {"message": "Real-time sync established with MySQL 8.0"},
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(init_payload)}\n\n"

            while True:
                try:
                    # Wait up to 15 seconds for an event; if timeout, send a keep-alive ping
                    msg = q.get(timeout=15.0)
                    yield msg
                except Empty:
                    # Keep-alive heartbeat comment
                    yield f": heartbeat {datetime.now().isoformat()}\n\n"
        except GeneratorExit:
            pass
        finally:
            with sse_lock:
                if q in sse_subscribers:
                    sse_subscribers.remove(q)

    return Response(
        event_generator(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*'
        }
    )

@app.route('/api/sync/version', methods=['GET'])
def get_sync_version():
    """
    Heartbeat endpoint to verify database fingerprint.
    Detects changes made both through the web app and directly via raw MySQL queries.
    """
    try:
        fp = db.get_database_fingerprint()
        return jsonify({
            "success": True,
            "version": db_version,
            "fingerprint": fp,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# -------------------------------------------------------------
# REST API: Dashboard Stats
# -------------------------------------------------------------
@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        stats = db.get_dashboard_stats()
        return jsonify({"success": True, "data": stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# -------------------------------------------------------------
# REST API: Farmers
# -------------------------------------------------------------
@app.route('/api/farmers', methods=['GET'])
def list_farmers():
    district = request.args.get('district')
    status = request.args.get('status')
    search = request.args.get('search')
    try:
        farmers = db.get_farmers(district=district, status=status, search=search)
        return jsonify({"success": True, "count": len(farmers), "data": farmers})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/farmers/<int:farmer_id>', methods=['GET'])
def get_farmer(farmer_id):
    try:
        farmer = db.get_farmer_by_id(farmer_id)
        if not farmer:
            return jsonify({"success": False, "error": "Farmer not found"}), 404
        return jsonify({"success": True, "data": farmer})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/farmers', methods=['POST'])
def add_farmer():
    data = request.get_json() or {}
    required = ['full_name', 'phone', 'district', 'village', 'latitude', 'longitude']
    for req in required:
        if not data.get(req):
            return jsonify({"success": False, "error": f"Field '{req}' is required"}), 400

    try:
        farmer = db.create_farmer(data)
        # Broadcast real-time event to all connected dashboard users
        broadcast_db_event("FARMER_REGISTERED", {
            "farmer_id": farmer['id'],
            "name": farmer['full_name'],
            "district": farmer['district'],
            "village": farmer['village']
        })
        return jsonify({"success": True, "message": "Farmer registered successfully", "data": farmer}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/farmers/<int:farmer_id>', methods=['PUT'])
def edit_farmer(farmer_id):
    data = request.get_json() or {}
    try:
        farmer = db.update_farmer(farmer_id, data)
        # Broadcast real-time update event
        broadcast_db_event("FARMER_UPDATED", {
            "farmer_id": farmer_id,
            "name": farmer['full_name']
        })
        return jsonify({"success": True, "message": "Farmer updated successfully", "data": farmer})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/farmers/<int:farmer_id>', methods=['DELETE'])
def remove_farmer(farmer_id):
    try:
        success = db.delete_farmer(farmer_id)
        if success:
            broadcast_db_event("FARMER_DELETED", {"farmer_id": farmer_id})
            return jsonify({"success": True, "message": "Farmer deleted successfully"})
        return jsonify({"success": False, "error": "Farmer not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/farmers/<int:farmer_id>/status', methods=['PATCH'])
def update_farmer_status(farmer_id):
    data = request.get_json() or {}
    status = data.get('status')
    if status not in ['Safe', 'In Field', 'At Risk', 'Evacuating', 'SOS_Distress']:
        return jsonify({"success": False, "error": "Invalid safety status"}), 400

    try:
        db.update_farmer_status(farmer_id, status)
        broadcast_db_event("FARMER_STATUS_CHANGED", {
            "farmer_id": farmer_id,
            "status": status
        })
        return jsonify({"success": True, "message": f"Farmer status updated to {status}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# -------------------------------------------------------------
# REST API: Weather Alerts & Broadcasting
# -------------------------------------------------------------
@app.route('/api/alerts', methods=['GET'])
def list_alerts():
    active_only = request.args.get('active_only', 'false').lower() == 'true'
    try:
        alerts = db.get_alerts(active_only=active_only)
        return jsonify({"success": True, "data": alerts})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/alerts', methods=['POST'])
def create_weather_alert():
    data = request.get_json() or {}
    required = ['hazard_type', 'title', 'district', 'epicenter_lat', 'epicenter_lon', 'instruction_text']
    for req in required:
        if not data.get(req):
            return jsonify({"success": False, "error": f"Field '{req}' is required"}), 400

    try:
        alert = db.create_alert(data)
        # Auto-broadcast if requested
        if data.get('auto_broadcast', True):
            broadcast_result = db.broadcast_alert_to_farmers(alert['id'])
            broadcast_db_event("ALERT_BROADCASTED", {
                "alert_id": alert['id'],
                "title": alert['title'],
                "hazard_type": alert['hazard_type'],
                "district": alert['district'],
                "impacted": broadcast_result.get('impacted_count', 0),
                "dispatches": broadcast_result.get('dispatched_count', 0)
            })
            return jsonify({
                "success": True,
                "message": "Alert created and broadcasted to farmers in hazard zone",
                "data": alert,
                "broadcast": broadcast_result
            }), 201

        broadcast_db_event("ALERT_CREATED", {
            "alert_id": alert['id'],
            "title": alert['title'],
            "hazard_type": alert['hazard_type']
        })
        return jsonify({"success": True, "message": "Alert created successfully", "data": alert}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/alerts/<int:alert_id>/broadcast', methods=['POST'])
def trigger_broadcast(alert_id):
    try:
        result = db.broadcast_alert_to_farmers(alert_id)
        broadcast_db_event("ALERT_BROADCASTED", {
            "alert_id": alert_id,
            "impacted": result.get('impacted_count', 0),
            "dispatches": result.get('dispatched_count', 0)
        })
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/alerts/<int:alert_id>/deactivate', methods=['POST'])
def deactivate_alert(alert_id):
    try:
        db.deactivate_alert(alert_id)
        broadcast_db_event("ALERT_DEACTIVATED", {"alert_id": alert_id})
        return jsonify({"success": True, "message": "Alert deactivated successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# -------------------------------------------------------------
# REST API: Sensor Stations
# -------------------------------------------------------------
@app.route('/api/sensors', methods=['GET'])
def list_sensors():
    try:
        sensors = db.get_sensor_stations()
        return jsonify({"success": True, "data": sensors})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/sensors/<int:station_id>/reading', methods=['POST'])
def update_sensor(station_id):
    data = request.get_json() or {}
    try:
        updated = db.update_sensor_reading(station_id, data)
        broadcast_db_event("SENSOR_UPDATED", {
            "station_id": station_id,
            "station_code": updated.get('station_code') if updated else None,
            "status": updated.get('status') if updated else 'Updated'
        })
        return jsonify({"success": True, "message": "Sensor reading updated", "data": updated})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# -------------------------------------------------------------
# REST API: Shelters, Dispatches, SOS
# -------------------------------------------------------------
@app.route('/api/shelters', methods=['GET'])
def list_shelters():
    try:
        shelters = db.get_shelters()
        return jsonify({"success": True, "data": shelters})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/dispatches', methods=['GET'])
def list_dispatches():
    limit = int(request.args.get('limit', 50))
    try:
        dispatches = db.get_dispatches(limit=limit)
        return jsonify({"success": True, "data": dispatches})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/sos', methods=['GET'])
def list_sos():
    try:
        sos_list = db.get_sos_requests()
        return jsonify({"success": True, "data": sos_list})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/sos', methods=['POST'])
def submit_sos():
    data = request.get_json() or {}
    if not data.get('farmer_id'):
        return jsonify({"success": False, "error": "farmer_id is required"}), 400

    try:
        sos_id = db.create_sos_request(data)
        broadcast_db_event("SOS_TRIGGERED", {
            "sos_id": sos_id,
            "farmer_id": data.get('farmer_id'),
            "distress_type": data.get('distress_type', 'Trapped_In_Field')
        })
        return jsonify({"success": True, "message": "Emergency SOS beacon activated!", "sos_id": sos_id}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/sos/<int:sos_id>/status', methods=['PATCH'])
def update_sos(sos_id):
    data = request.get_json() or {}
    status = data.get('rescue_status')
    team = data.get('assigned_team')
    if not status:
        return jsonify({"success": False, "error": "rescue_status is required"}), 400

    try:
        db.update_sos_status(sos_id, status, assigned_team=team)
        broadcast_db_event("SOS_STATUS_UPDATED", {
            "sos_id": sos_id,
            "status": status,
            "assigned_team": team
        })
        return jsonify({"success": True, "message": f"SOS status updated to {status}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# -------------------------------------------------------------
# REST API: Threat Simulation Engine
# -------------------------------------------------------------
@app.route('/api/simulate-threat', methods=['POST'])
def simulate_threat():
    """
    Simulates a sudden lightning storm or flash flood surge event.
    Creates an alert and broadcasts to registered farmers in the target zone.
    """
    data = request.get_json() or {}
    threat_type = data.get('type', 'Lightning')
    district = data.get('district', 'Varanasi')

    # Default coordinates based on district (UP, Bihar, West Bengal)
    district_coords = {
        'Varanasi': (25.4215, 82.8423),
        'Gorakhpur': (26.7451, 83.2145),
        'Prayagraj': (25.5120, 81.8540),
        'Patna': (25.6412, 85.0425),
        'Ayodhya': (26.7725, 81.8964),
        'Malda': (25.0108, 88.1411),
        'Murshidabad': (24.1850, 88.2700),
        'Purba Bardhaman': (23.2324, 87.8615),
        'South 24 Parganas': (22.1648, 88.8021),
        'Nadia': (23.4013, 88.4952),
        'Bankura': (23.2321, 87.0716),
        'Paschim Medinipur': (22.6710, 87.7215),
        'Hooghly': (22.8845, 87.7812),
        'Jalpaiguri': (26.5405, 88.7196),
        'North 24 Parganas': (22.6540, 88.8920),
        'Cooch Behar': (26.1340, 89.4670),
    }

    lat, lon = district_coords.get(district, (25.4215, 82.8423))

    if threat_type == 'Lightning':
        alert_payload = {
            "hazard_type": "Lightning",
            "severity_level": "Severe_Emergency",
            "title": f"🚨 SIMULATION: High-Density Lightning Cluster in {district}",
            "district": district,
            "epicenter_lat": lat,
            "epicenter_lon": lon,
            "radius_km": 15.0,
            "instruction_text": "CRITICAL: Multiple Cloud-to-Ground lightning strikes detected. Clear open fields immediately! Disconnect electric pumps.",
            "instruction_text_hindi": "अति आवश्यक: आकाशीय बिजली गिरने का भारी खतरा! खुले खेतों से तुरंत सुरक्षित स्थानों पर जाएं। ट्यूबवेल और बिजली उपकरण बंद करें।"
        }
    else:
        alert_payload = {
            "hazard_type": "Flash_Flood",
            "severity_level": "Warning",
            "title": f"🌊 SIMULATION: Flash Flood Water Surge in {district} River Basin",
            "district": district,
            "epicenter_lat": lat,
            "epicenter_lon": lon,
            "radius_km": 20.0,
            "instruction_text": "FLOOD WARNING: Rapid water runoff approaching agricultural lowlands. Move livestock and harvest to designated elevated shelters.",
            "instruction_text_hindi": "बाढ़ चेतावनी: निचले कृषि क्षेत्रों में तेजी से जलभराव की आशंका। मवेशियों और अनाज को तुरंत ऊंचे सुरक्षित स्थानों पर पहुंचाएं।"
        }

    try:
        new_alert = db.create_alert(alert_payload)
        broadcast_res = db.broadcast_alert_to_farmers(new_alert['id'])
        broadcast_db_event("SIMULATION_TRIGGERED", {
            "type": threat_type,
            "district": district,
            "alert_id": new_alert['id'],
            "impacted": broadcast_res.get('impacted_count', 0)
        })
        return jsonify({
            "success": True,
            "message": f"Simulation executed: {threat_type} alert triggered in {district}",
            "alert": new_alert,
            "broadcast": broadcast_res
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

import sys
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

if __name__ == '__main__':
    print("=" * 60)
    print("LIGHTNING & FLOOD ALERT REGISTRY FOR FARMERS")
    print(f"Backend Server running at: http://127.0.0.1:{Config.PORT}")
    print(f"Connected to MySQL on port: {Config.MYSQL_PORT}")
    print(f"Real-Time Multi-User Synchronization: ACTIVE (SSE + Polling)")
    print("=" * 60)
    app.run(host='0.0.0.0', port=Config.PORT, debug=Config.DEBUG, threaded=True)
