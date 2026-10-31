import math
import os
import pymysql
import pymysql.cursors
from config import Config

def get_db_connection(use_database=True):
    """
    Establish a connection to MySQL server.
    Tries configured port first; if failed, attempts alternative standard ports (3306, 3307).
    """
    candidate_ports = [Config.MYSQL_PORT]
    if 3307 not in candidate_ports:
        candidate_ports.append(3307)
    if 3306 not in candidate_ports:
        candidate_ports.append(3306)

    last_error = None
    for port in candidate_ports:
        try:
            conn = pymysql.connect(
                host=Config.MYSQL_HOST,
                port=port,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DB if use_database else None,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True
            )
            return conn
        except Exception as e:
            last_error = e
            continue

    raise ConnectionError(f"Could not connect to MySQL on ports {candidate_ports}. Error: {last_error}")

def execute_sql_file(file_path):
    """
    Executes an SQL file containing multiple statements.
    """
    if not os.path.exists(file_path):
        return

    conn = get_db_connection(use_database=False)
    cursor = conn.cursor()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_text = f.read()

        statements = sql_text.split(';')
        for stmt in statements:
            stmt = stmt.strip()
            if stmt:
                cursor.execute(stmt)
    finally:
        cursor.close()
        conn.close()

def init_db():
    """
    Initializes database schema and seed data if not already present.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(base_dir, 'schema.sql')
    seed_path = os.path.join(base_dir, 'seed_data.sql')

    print("[Database] Checking MySQL database initialization...")
    # Execute schema
    execute_sql_file(schema_path)

    # Check if farmers table has rows; if not, seed data
    conn = get_db_connection(use_database=True)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) AS total FROM farmers")
        result = cursor.fetchone()
        if result['total'] == 0:
            print("[Database] Seeding initial mock data...")
            execute_sql_file(seed_path)
        print("[Database] Database initialized and ready.")
    finally:
        cursor.close()
        conn.close()

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points on the earth in km.
    """
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# -------------------------------------------------------------
# Farmers CRUD
# -------------------------------------------------------------
def get_farmers(district=None, status=None, search=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = "SELECT * FROM farmers WHERE 1=1"
        params = []
        if district:
            query += " AND district = %s"
            params.append(district)
        if status:
            query += " AND safety_status = %s"
            params.append(status)
        if search:
            query += " AND (full_name LIKE %s OR phone LIKE %s OR village LIKE %s OR farmer_code LIKE %s)"
            wildcard = f"%{search}%"
            params.extend([wildcard, wildcard, wildcard, wildcard])

        query += " ORDER BY id DESC"
        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def get_farmer_by_id(farmer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM farmers WHERE id = %s", (farmer_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

def create_farmer(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Generate farmer code like FMR-xxxx
        cursor.execute("SELECT MAX(id) as max_id FROM farmers")
        max_id = (cursor.fetchone()['max_id'] or 1000) + 1
        farmer_code = f"FMR-{max_id:04d}"

        sql = """
            INSERT INTO farmers 
            (farmer_code, full_name, phone, alternate_phone, state, district, sub_district, village,
             latitude, longitude, farm_size_acres, crops_grown, preferred_language, alert_sms, alert_whatsapp, alert_ivr, safety_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            farmer_code,
            data.get('full_name'),
            data.get('phone'),
            data.get('alternate_phone') or None,
            data.get('state', 'Uttar Pradesh'),
            data.get('district'),
            data.get('sub_district'),
            data.get('village'),
            float(data.get('latitude', 25.4215)),
            float(data.get('longitude', 82.8423)),
            float(data.get('farm_size_acres', 2.5)),
            data.get('crops_grown', 'Paddy'),
            data.get('preferred_language', 'English'),
            bool(data.get('alert_sms', True)),
            bool(data.get('alert_whatsapp', True)),
            bool(data.get('alert_ivr', False)),
            data.get('safety_status', 'Safe')
        ))
        new_id = cursor.lastrowid
        return get_farmer_by_id(new_id)
    finally:
        cursor.close()
        conn.close()

def update_farmer(farmer_id, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = """
            UPDATE farmers SET
            full_name = %s, phone = %s, alternate_phone = %s, state = %s,
            district = %s, sub_district = %s, village = %s, latitude = %s, longitude = %s,
            farm_size_acres = %s, crops_grown = %s, preferred_language = %s,
            alert_sms = %s, alert_whatsapp = %s, alert_ivr = %s, safety_status = %s
            WHERE id = %s
        """
        cursor.execute(sql, (
            data.get('full_name'),
            data.get('phone'),
            data.get('alternate_phone') or None,
            data.get('state', 'Uttar Pradesh'),
            data.get('district'),
            data.get('sub_district'),
            data.get('village'),
            float(data.get('latitude')),
            float(data.get('longitude')),
            float(data.get('farm_size_acres', 2.5)),
            data.get('crops_grown'),
            data.get('preferred_language', 'English'),
            bool(data.get('alert_sms', True)),
            bool(data.get('alert_whatsapp', True)),
            bool(data.get('alert_ivr', False)),
            data.get('safety_status', 'Safe'),
            farmer_id
        ))
        return get_farmer_by_id(farmer_id)
    finally:
        cursor.close()
        conn.close()

def delete_farmer(farmer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM farmers WHERE id = %s", (farmer_id,))
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conn.close()

def update_farmer_status(farmer_id, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE farmers SET safety_status = %s WHERE id = %s", (status, farmer_id))
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conn.close()

# -------------------------------------------------------------
# Weather Alerts & Emergency Broadcasting
# -------------------------------------------------------------
def get_alerts(active_only=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = "SELECT * FROM weather_alerts"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY id DESC"
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def get_alert_by_id(alert_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM weather_alerts WHERE id = %s", (alert_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

def create_alert(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT MAX(id) as max_id FROM weather_alerts")
        max_id = (cursor.fetchone()['max_id'] or 0) + 1
        hazard_prefix = "LGT" if data.get('hazard_type') == 'Lightning' else "FLD"
        alert_code = f"ALT-2026-{hazard_prefix}-{max_id:03d}"

        sql = """
            INSERT INTO weather_alerts
            (alert_code, hazard_type, severity_level, title, district,
             epicenter_lat, epicenter_lon, radius_km, instruction_text, instruction_text_hindi, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
        """
        cursor.execute(sql, (
            alert_code,
            data.get('hazard_type'),
            data.get('severity_level', 'Warning'),
            data.get('title'),
            data.get('district'),
            float(data.get('epicenter_lat')),
            float(data.get('epicenter_lon')),
            float(data.get('radius_km', 10.0)),
            data.get('instruction_text'),
            data.get('instruction_text_hindi', '')
        ))
        alert_id = cursor.lastrowid
        return get_alert_by_id(alert_id)
    finally:
        cursor.close()
        conn.close()

def broadcast_alert_to_farmers(alert_id):
    """
    Finds all registered farmers whose farm coordinates lie within the alert radius.
    Dispatches multi-channel alerts (SMS, WhatsApp), marks farmers as 'At Risk' if 'In Field',
    and generates dispatches log.
    """
    alert = get_alert_by_id(alert_id)
    if not alert:
        return {"error": "Alert not found", "impacted_count": 0}

    epicenter_lat = float(alert['epicenter_lat'])
    epicenter_lon = float(alert['epicenter_lon'])
    radius_km = float(alert['radius_km'])

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Fetch all farmers in the district or nearby
        cursor.execute("SELECT * FROM farmers")
        all_farmers = cursor.fetchall()

        impacted_farmers = []
        for f in all_farmers:
            dist = haversine_distance(epicenter_lat, epicenter_lon, float(f['latitude']), float(f['longitude']))
            if dist <= radius_km:
                impacted_farmers.append((f, dist))

        # Generate dispatches
        dispatched_count = 0
        for f, dist in impacted_farmers:
            lang = f.get('preferred_language', 'English')
            if lang == 'Hindi':
                msg = f"🚨 आपातकालीन चेतावनी [{alert['hazard_type']}]: {alert['title']}. आप आपदा क्षेत्र से {dist:.1f} किमी दूरी पर हैं। तुरंत पक्के मकान में सुरक्षित जाएं।"
            else:
                msg = f"🚨 EMERGENCY ALERT [{alert['hazard_type']}]: {alert['title']}. You are {dist:.1f}km from hazard epicenter. Seek pucca shelter immediately!"

            # SMS dispatch
            if f['alert_sms']:
                cursor.execute("""
                    INSERT INTO alert_dispatches 
                    (alert_id, farmer_id, delivery_channel, message_content, language_used, status, farmer_ack)
                    VALUES (%s, %s, 'SMS', %s, %s, 'Delivered', 'Pending')
                """, (alert_id, f['id'], msg, lang))
                dispatched_count += 1

            # WhatsApp dispatch
            if f['alert_whatsapp']:
                wa_msg = f"📢 *KISAN EMERGENCY ALERT*\n*{alert['title']}*\nDistance to danger zone: {dist:.1f} km\nSafety instructions: {alert['instruction_text']}\nNearest Safe Haven: Contact local Panchayat immediately."
                cursor.execute("""
                    INSERT INTO alert_dispatches 
                    (alert_id, farmer_id, delivery_channel, message_content, language_used, status, farmer_ack)
                    VALUES (%s, %s, 'WhatsApp', %s, %s, 'Delivered', 'Pending')
                """, (alert_id, f['id'], wa_msg, lang))
                dispatched_count += 1

            # Update farmer safety status to 'At Risk' if they were 'In Field' or 'Safe'
            if f['safety_status'] in ('Safe', 'In Field'):
                cursor.execute("UPDATE farmers SET safety_status = 'At Risk' WHERE id = %s", (f['id'],))

        # Update alert totals
        cursor.execute("""
            UPDATE weather_alerts 
            SET farmers_impacted = %s, dispatched_count = %s
            WHERE id = %s
        """, (len(impacted_farmers), dispatched_count, alert_id))

        return {
            "success": True,
            "alert": alert,
            "impacted_count": len(impacted_farmers),
            "dispatched_count": dispatched_count
        }
    finally:
        cursor.close()
        conn.close()

def deactivate_alert(alert_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE weather_alerts SET is_active = 0 WHERE id = %s", (alert_id,))
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conn.close()

# -------------------------------------------------------------
# Sensor Telemetry & Simulators
# -------------------------------------------------------------
def get_sensor_stations():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM sensor_stations ORDER BY id ASC")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def update_sensor_reading(station_id, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = """
            UPDATE sensor_stations SET
            current_rainfall_mm = %s,
            river_water_level_m = %s,
            lightning_flash_rate_per_min = %s,
            peak_strike_current_ka = %s,
            status = %s
            WHERE id = %s
        """
        cursor.execute(sql, (
            float(data.get('current_rainfall_mm', 0)),
            float(data.get('river_water_level_m', 0)),
            int(data.get('lightning_flash_rate_per_min', 0)),
            float(data.get('peak_strike_current_ka', 0)),
            data.get('status', 'Normal'),
            station_id
        ))
        cursor.execute("SELECT * FROM sensor_stations WHERE id = %s", (station_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

# -------------------------------------------------------------
# Shelters, Dispatches, SOS
# -------------------------------------------------------------
def get_shelters():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM emergency_shelters ORDER BY id ASC")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def get_dispatches(limit=50):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = """
            SELECT d.*, f.full_name AS farmer_name, f.phone AS farmer_phone, f.village, f.district,
                   a.title AS alert_title, a.hazard_type
            FROM alert_dispatches d
            JOIN farmers f ON d.farmer_id = f.id
            JOIN weather_alerts a ON d.alert_id = a.id
            ORDER BY d.id DESC LIMIT %s
        """
        cursor.execute(sql, (limit,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def get_sos_requests():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = """
            SELECT s.*, f.full_name AS farmer_name, f.phone AS farmer_phone, f.village, f.district,
                   a.title AS alert_title
            FROM farmer_sos_requests s
            JOIN farmers f ON s.farmer_id = f.id
            LEFT JOIN weather_alerts a ON s.alert_id = a.id
            ORDER BY s.id DESC
        """
        cursor.execute(sql)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def create_sos_request(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        farmer_id = data.get('farmer_id')
        cursor.execute("SELECT latitude, longitude FROM farmers WHERE id = %s", (farmer_id,))
        farmer = cursor.fetchone()
        lat = float(data.get('gps_lat', farmer['latitude'] if farmer else 25.4215))
        lon = float(data.get('gps_lon', farmer['longitude'] if farmer else 82.8423))

        sql = """
            INSERT INTO farmer_sos_requests
            (farmer_id, alert_id, distress_type, emergency_notes, gps_lat, gps_lon, rescue_status, assigned_team)
            VALUES (%s, %s, %s, %s, %s, %s, 'Reported', 'Quick Response Team #1')
        """
        cursor.execute(sql, (
            farmer_id,
            data.get('alert_id') or None,
            data.get('distress_type', 'Trapped_In_Field'),
            data.get('emergency_notes', 'Urgent rescue needed'),
            lat, lon
        ))
        # Update farmer status to SOS_Distress
        cursor.execute("UPDATE farmers SET safety_status = 'SOS_Distress' WHERE id = %s", (farmer_id,))
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()

def update_sos_status(sos_id, status, assigned_team=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if assigned_team:
            cursor.execute("UPDATE farmer_sos_requests SET rescue_status = %s, assigned_team = %s WHERE id = %s",
                           (status, assigned_team, sos_id))
        else:
            cursor.execute("UPDATE farmer_sos_requests SET rescue_status = %s WHERE id = %s", (status, sos_id))
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conn.close()

def get_dashboard_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) AS total_farmers FROM farmers")
        total_farmers = cursor.fetchone()['total_farmers']

        cursor.execute("SELECT COUNT(*) AS at_risk FROM farmers WHERE safety_status IN ('At Risk', 'In Field', 'SOS_Distress')")
        at_risk_farmers = cursor.fetchone()['at_risk']

        cursor.execute("SELECT COUNT(*) AS active_alerts FROM weather_alerts WHERE is_active = 1")
        active_alerts = cursor.fetchone()['active_alerts']

        cursor.execute("SELECT COUNT(*) AS total_dispatches FROM alert_dispatches")
        total_dispatches = cursor.fetchone()['total_dispatches']

        cursor.execute("SELECT COUNT(*) AS pending_sos FROM farmer_sos_requests WHERE rescue_status IN ('Reported', 'Assigned', 'Team_Dispatched')")
        pending_sos = cursor.fetchone()['pending_sos']

        cursor.execute("SELECT COUNT(*) AS active_shelters, SUM(capacity_persons) AS total_capacity, SUM(current_occupancy) AS total_occupancy FROM emergency_shelters")
        shelter_stat = cursor.fetchone()

        return {
            "total_farmers": total_farmers,
            "at_risk_farmers": at_risk_farmers,
            "active_alerts": active_alerts,
            "total_dispatches": total_dispatches,
            "pending_sos": pending_sos,
            "total_shelter_capacity": shelter_stat['total_capacity'] or 0,
            "current_shelter_occupancy": shelter_stat['total_occupancy'] or 0
        }
    finally:
        cursor.close()
        conn.close()

def get_database_fingerprint():
    """
    Returns a fast composite fingerprint string representing the current state of MySQL tables.
    Used for detecting changes made directly to the database by any client or external script.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = """
            SELECT 
                (SELECT COUNT(*) FROM farmers) AS f_count,
                (SELECT COALESCE(MAX(updated_at), '1970-01-01') FROM farmers) AS f_upd,
                (SELECT COUNT(*) FROM weather_alerts) AS a_count,
                (SELECT COALESCE(MAX(created_at), '1970-01-01') FROM weather_alerts) AS a_upd,
                (SELECT COUNT(*) FROM alert_dispatches) AS d_count,
                (SELECT COUNT(*) FROM farmer_sos_requests) AS s_count,
                (SELECT COALESCE(MAX(updated_at), '1970-01-01') FROM farmer_sos_requests) AS s_upd,
                (SELECT COALESCE(MAX(last_reading_time), '1970-01-01') FROM sensor_stations) AS sn_upd
        """
        cursor.execute(sql)
        row = cursor.fetchone()
        if not row:
            return "empty"
        return f"f:{row['f_count']}_{row['f_upd']}|a:{row['a_count']}_{row['a_upd']}|d:{row['d_count']}|s:{row['s_count']}_{row['s_upd']}|sn:{row['sn_upd']}"
    finally:
        cursor.close()
        conn.close()


