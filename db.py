import math
import os
import re
import tempfile
import sqlite3
import pymysql
import pymysql.cursors
from config import Config

_is_sqlite_active = False

def is_sqlite_mode():
    """
    Check if we should run in serverless SQLite mode.
    Enabled automatically on Vercel/serverless environments unless an external cloud MySQL is configured.
    """
    is_vercel = bool(os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME'))
    is_localhost = Config.MYSQL_HOST in ('127.0.0.1', 'localhost', '')
    return is_vercel and is_localhost

def get_sqlite_path():
    return os.path.join(tempfile.gettempdir(), 'farmer_alert_serverless.db')

class SQLiteCursorAdapter:
    def __init__(self, cursor):
        self._cursor = cursor
        self.lastrowid = None
        self.rowcount = 0

    def execute(self, query, params=None):
        q = query.replace('%s', '?')
        q = re.sub(r'\bNOW\(\)', "datetime('now', 'localtime')", q, flags=re.I)
        q = re.sub(r'DATE_ADD\(.*?\)', "datetime('now', '+3 hours')", q, flags=re.I)
        if params:
            self._cursor.execute(q, params)
        else:
            self._cursor.execute(q)
        self.lastrowid = self._cursor.lastrowid
        self.rowcount = self._cursor.rowcount
        return self

    def fetchone(self):
        row = self._cursor.fetchone()
        return dict(row) if row else None

    def fetchall(self):
        rows = self._cursor.fetchall()
        return [dict(r) for r in rows]

    def close(self):
        self._cursor.close()

class SQLiteConnAdapter:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return SQLiteCursorAdapter(self._conn.cursor())

    def close(self):
        self._conn.close()

    def commit(self):
        self._conn.commit()

def get_sqlite_connection():
    global _is_sqlite_active
    _is_sqlite_active = True
    db_path = get_sqlite_path()
    conn = sqlite3.connect(db_path, autocommit=True)
    conn.row_factory = sqlite3.Row
    return SQLiteConnAdapter(conn)

def init_sqlite_tables(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS farmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_code TEXT NOT NULL UNIQUE,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            alternate_phone TEXT,
            state TEXT NOT NULL DEFAULT 'Uttar Pradesh',
            district TEXT NOT NULL,
            sub_district TEXT NOT NULL,
            village TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            farm_size_acres REAL DEFAULT 2.50,
            crops_grown TEXT DEFAULT 'Paddy, Mustard',
            preferred_language TEXT DEFAULT 'English',
            alert_sms INTEGER DEFAULT 1,
            alert_whatsapp INTEGER DEFAULT 1,
            alert_ivr INTEGER DEFAULT 0,
            safety_status TEXT DEFAULT 'Safe',
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            updated_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sensor_stations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_code TEXT NOT NULL UNIQUE,
            station_name TEXT NOT NULL,
            station_type TEXT NOT NULL,
            district TEXT NOT NULL,
            river_basin TEXT DEFAULT 'Ganga-Ghaghara Basin',
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            current_rainfall_mm REAL DEFAULT 0.00,
            river_water_level_m REAL DEFAULT 0.00,
            danger_water_level_m REAL DEFAULT 12.00,
            lightning_flash_rate_per_min INTEGER DEFAULT 0,
            peak_strike_current_ka REAL DEFAULT 0.00,
            status TEXT DEFAULT 'Normal',
            last_reading_time TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS emergency_shelters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shelter_name TEXT NOT NULL,
            shelter_type TEXT NOT NULL,
            district TEXT NOT NULL,
            village TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            capacity_persons INTEGER NOT NULL DEFAULT 250,
            current_occupancy INTEGER DEFAULT 0,
            lightning_protection_installed INTEGER DEFAULT 1,
            generator_backup INTEGER DEFAULT 1,
            contact_officer TEXT NOT NULL,
            contact_phone TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS weather_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_code TEXT NOT NULL UNIQUE,
            hazard_type TEXT NOT NULL,
            severity_level TEXT NOT NULL,
            title TEXT NOT NULL,
            district TEXT NOT NULL,
            epicenter_lat REAL NOT NULL,
            epicenter_lon REAL NOT NULL,
            radius_km REAL NOT NULL DEFAULT 10.00,
            instruction_text TEXT NOT NULL,
            instruction_text_hindi TEXT,
            is_active INTEGER DEFAULT 1,
            farmers_impacted INTEGER DEFAULT 0,
            dispatched_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            expires_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alert_dispatches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id INTEGER NOT NULL,
            farmer_id INTEGER NOT NULL,
            delivery_channel TEXT NOT NULL,
            message_content TEXT NOT NULL,
            language_used TEXT DEFAULT 'English',
            status TEXT DEFAULT 'Delivered',
            farmer_ack TEXT DEFAULT 'Pending',
            dispatched_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS farmer_sos_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER NOT NULL,
            alert_id INTEGER,
            distress_type TEXT NOT NULL,
            emergency_notes TEXT,
            gps_lat REAL NOT NULL,
            gps_lon REAL NOT NULL,
            rescue_status TEXT DEFAULT 'Reported',
            assigned_team TEXT DEFAULT 'Quick Response Team #1',
            reported_at TEXT DEFAULT (datetime('now', 'localtime')),
            updated_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)

def get_db_connection(use_database=True):
    """
    Establish a connection to MySQL server.
    Tries configured port first; if failed, attempts alternative standard ports (3306, 3307).
    Falls back gracefully to SQLite if running in serverless environments (e.g. Vercel).
    """
    if is_sqlite_mode():
        return get_sqlite_connection()

    candidate_ports = [Config.MYSQL_PORT]
    if 3307 not in candidate_ports:
        candidate_ports.append(3307)
    if 3306 not in candidate_ports:
        candidate_ports.append(3306)

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
                autocommit=True,
                connect_timeout=3
            )
            return conn
        except Exception:
            continue

    # Fallback to serverless SQLite database
    return get_sqlite_connection()

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

def seed_sqlite_data(conn):
    cur = conn.cursor()
    farmers_data = [
        ('FMR-1001', 'Ramesh Chandra Patel', '+91 98765 43210', '+91 98765 43219', 'Uttar Pradesh', 'Varanasi', 'Pindra', 'Phulpur Buzurg', 25.421500, 82.842300, 4.50, 'Paddy (Basmati), Wheat, Mustard', 'Hindi', 1, 1, 1, 'In Field'),
        ('FMR-1002', 'Sunita Devi Yadav', '+91 94150 12345', None, 'Uttar Pradesh', 'Varanasi', 'Sadar', 'Shivpur Khas', 25.362100, 82.951400, 2.20, 'Vegetables (Tomato, Cauliflower), Paddy', 'Hindi', 1, 1, 0, 'Safe'),
        ('FMR-1003', 'Gurpreet Singh Dhillon', '+91 98140 87654', '+91 98140 87655', 'Uttar Pradesh', 'Gorakhpur', 'Sahjanwa', 'Bhari Baisan', 26.745100, 83.214500, 8.00, 'Sugarcane, Paddy, Maize', 'Punjabi', 1, 1, 0, 'At Risk'),
        ('FMR-1004', 'Manoj Kumar Maurya', '+91 97920 33445', None, 'Uttar Pradesh', 'Gorakhpur', 'Chauri Chaura', 'Rampur Buzurg', 26.689200, 83.562100, 3.10, 'Paddy, Black Gram (Urad), Lentil', 'Hindi', 1, 0, 1, 'In Field'),
        ('FMR-1005', 'Anand Swaroop Tiwari', '+91 94501 99887', '+91 94501 99888', 'Uttar Pradesh', 'Prayagraj', 'Soraon', 'Mau Aima Dehat', 25.621400, 81.874100, 5.00, 'Guava Orchards, Paddy, Wheat', 'Hindi', 1, 1, 1, 'Safe'),
        ('FMR-1006', 'Dhirendra Narayan Rai', '+91 91250 66778', None, 'Uttar Pradesh', 'Ayodhya', 'Sohawal', 'Rudauli North', 26.772500, 81.896400, 6.20, 'Paddy, Mustard, Sugarcane', 'English', 1, 1, 0, 'Safe'),
        ('FMR-1007', 'Kavita Kumari Roy', '+91 99341 55667', None, 'Bihar', 'Patna', 'Danapur', 'Nasriganj Diara', 25.641200, 85.042500, 1.80, 'Diara Vegetables, Maize, Watermelon', 'Hindi', 1, 1, 1, 'At Risk'),
        ('FMR-1008', 'Abdul Halim Ansari', '+91 98350 44332', '+91 98350 44333', 'Bihar', 'Patna', 'Fatuha', 'Kachi Dargah', 25.568400, 85.289100, 3.75, 'Paddy, Jute, Mustard', 'Hindi', 1, 1, 0, 'In Field'),
        ('FMR-1009', 'Bijoy Krishna Das', '+91 97321 88990', None, 'West Bengal', 'Malda', 'Harischandrapur', 'Bhaluka North', 25.431200, 87.954100, 4.00, 'Makhana, Aman Paddy, Jute', 'Bengali', 1, 1, 1, 'Safe'),
        ('FMR-1010', 'Bhavani Shankar Reddy', '+91 94401 22334', None, 'Andhra Pradesh', 'Guntur', 'Tenali', 'Angalakuduru', 16.241500, 80.642100, 5.50, 'Chilli, Cotton, Paddy', 'Telugu', 1, 1, 0, 'Safe'),
        ('FMR-2001', 'Subhash Chandra Mondal', '+91 97330 11223', None, 'West Bengal', 'Murshidabad', 'Bhagawangola', 'Habibpur', 24.321400, 88.291200, 3.50, 'Jute, Mustard, Aman Paddy', 'Bengali', 1, 1, 1, 'In Field'),
        ('FMR-2002', 'Debashis Banerjee', '+91 98321 44556', '+91 98321 44557', 'West Bengal', 'Purba Bardhaman', 'Kalna', 'Dhatrigram', 23.218500, 88.314200, 4.20, 'Boro Paddy, Potato, Mustard', 'Bengali', 1, 1, 0, 'Safe'),
        ('FMR-2003', 'Animesh Sardar', '+91 94741 77889', None, 'West Bengal', 'South 24 Parganas', 'Gosaba', 'Rangabelia', 22.164800, 88.802100, 2.80, 'Saline-resistant Aman Paddy, Betel Vine, Vegetables', 'Bengali', 1, 1, 1, 'At Risk'),
        ('FMR-2004', 'Tapas Kumar Ghosh', '+91 96472 33441', None, 'West Bengal', 'Nadia', 'Ranaghat', 'Habibpur Ghat', 23.181200, 88.562400, 3.00, 'Pointed Gourd (Patol), Jute, Paddy', 'Bengali', 1, 1, 0, 'Safe'),
        ('FMR-2005', 'Bikash Chandra Mahato', '+91 95470 55662', None, 'West Bengal', 'Bankura', 'Onda', 'Punisol', 23.142000, 87.195000, 5.00, 'Groundnut, Maize, Aman Paddy', 'Bengali', 1, 1, 1, 'In Field'),
        ('FMR-2006', 'Pranab Kanti Samanta', '+91 97355 88994', '+91 97355 88995', 'West Bengal', 'Paschim Medinipur', 'Ghatal', 'Monoharpur', 22.671000, 87.721500, 2.50, 'Boro Paddy, Winter Potato, Sesame', 'Bengali', 1, 1, 1, 'At Risk'),
        ('FMR-2007', 'Nirmal Kanti Roy', '+91 98320 66773', None, 'West Bengal', 'Jalpaiguri', 'Mainaguri', 'Padamoti', 26.562100, 88.824500, 6.00, 'Aman Paddy, Jute, Tea Leaves', 'Bengali', 1, 1, 0, 'Safe'),
        ('FMR-2008', 'Sukumar Das', '+91 94340 99112', None, 'West Bengal', 'Hooghly', 'Arambagh', 'Mayapur Char', 22.884500, 87.781200, 3.80, 'Jyoti Potato, Boro Paddy, Jute', 'Bengali', 1, 1, 0, 'In Field'),
        ('FMR-2009', 'Abhijit Biswas', '+91 98311 22334', None, 'West Bengal', 'North 24 Parganas', 'Basirhat', 'Dandirhat', 22.654000, 88.892000, 2.20, 'Aman Paddy, Vegetables, Til', 'Bengali', 1, 1, 0, 'Safe'),
        ('FMR-2010', 'Biren Chandra Barman', '+91 94750 33445', None, 'West Bengal', 'Cooch Behar', 'Dinhata', 'Bhitarkamta', 26.134000, 89.467000, 4.50, 'Tobacco, Jute, Paddy', 'Bengali', 1, 1, 1, 'Safe')
    ]
    for row in farmers_data:
        cur.execute("""
            INSERT OR REPLACE INTO farmers
            (farmer_code, full_name, phone, alternate_phone, state, district, sub_district, village, latitude, longitude, farm_size_acres, crops_grown, preferred_language, alert_sms, alert_whatsapp, alert_ivr, safety_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, row)

    sensors_data = [
        ('AWS-VNS-01', 'Varanasi Babatpur Radar & AWS', 'Combined_AWS', 'Varanasi', 'Ganga Basin', 25.452200, 82.859400, 48.50, 71.80, 71.26, 42, 65.40, 'Emergency'),
        ('LGT-GKP-02', 'Gorakhpur Lightning Early Detection Unit', 'Lightning_Detector', 'Gorakhpur', 'Rapti Basin', 26.760600, 83.373200, 18.20, 0.00, 0.00, 68, 89.20, 'Warning'),
        ('STR-GKP-03', 'Rapti River Birdghat Stream Gauge', 'Stream_Gauge', 'Gorakhpur', 'Rapti Basin', 26.721400, 83.351200, 62.00, 75.85, 74.98, 0, 0.00, 'Emergency'),
        ('STR-PRY-04', 'Prayagraj Phaphamau Ganga Gauge', 'Stream_Gauge', 'Prayagraj', 'Ganga-Yamuna Basin', 25.512000, 81.854000, 22.40, 84.10, 84.73, 5, 12.00, 'Watch'),
        ('AWS-PAT-05', 'Patna Digha Flood Telemetry Unit', 'Combined_AWS', 'Patna', 'Ganga-Son Basin', 25.642000, 85.098000, 39.80, 50.15, 50.52, 28, 44.50, 'Warning'),
        ('STR-MLD-06', 'Farakka Barrage Ganga Hydro Gauge', 'Stream_Gauge', 'Malda', 'Ganga-Bhagirathi Basin', 24.801000, 87.925000, 45.20, 22.80, 22.25, 0, 0.00, 'Emergency'),
        ('LGT-BNK-07', 'Bankura Chhotanagpur Lightning Early Warning Unit', 'Lightning_Detector', 'Bankura', 'Damodar-Kangsabati Basin', 23.225000, 87.081000, 15.00, 0.00, 0.00, 58, 76.40, 'Warning'),
        ('AWS-S24-08', 'Sundarbans Coastal Doppler & Storm AWS', 'Combined_AWS', 'South 24 Parganas', 'Sundarbans Delta', 22.180000, 88.810000, 72.40, 4.80, 4.20, 34, 48.20, 'Warning'),
        ('STR-GHT-09', 'Ghatal Shilabati River Stream Gauge', 'Stream_Gauge', 'Paschim Medinipur', 'Shilabati Basin', 22.668000, 87.718000, 58.00, 13.40, 12.80, 12, 22.00, 'Emergency')
    ]
    for row in sensors_data:
        cur.execute("""
            INSERT OR REPLACE INTO sensor_stations
            (station_code, station_name, station_type, district, river_basin, latitude, longitude, current_rainfall_mm, river_water_level_m, danger_water_level_m, lightning_flash_rate_per_min, peak_strike_current_ka, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, row)

    shelters_data = [
        ('Phulpur Multi-Hazard Relief Shelter', 'Flood_Center', 'Varanasi', 'Phulpur Buzurg', 25.429000, 82.839000, 450, 35, 1, 1, 'Shri Anand Verma (BDO Pindra)', '+91 94544 11201'),
        ('Panchayat Bhavan Elevated Shelter Shivpur', 'Elevated_Panchayat_Bhavan', 'Varanasi', 'Shivpur Khas', 25.367000, 82.948000, 200, 12, 1, 1, 'Smt. Pratima Devi (Gram Pradhan)', '+91 94544 11202'),
        ('Sahjanwa High School Flood Refuge', 'School_Building', 'Gorakhpur', 'Bhari Baisan', 26.749000, 83.219000, 600, 85, 1, 1, 'Dr. R. K. Srivastava (Principal)', '+91 94544 22301'),
        ('Chauri Chaura Cyclone & Storm Haven', 'Cyclone_Shelter', 'Gorakhpur', 'Rampur Buzurg', 26.694000, 83.568000, 500, 40, 1, 1, 'Shri M. P. Singh (Tehsildar)', '+91 94544 22302'),
        ('Danapur Diara Elevated Flood Shelter #2', 'Flood_Center', 'Patna', 'Nasriganj Diara', 25.648000, 85.049000, 750, 140, 1, 1, 'Inspector Rajiv Sinha (SDRF Bihar)', '+91 94318 33401'),
        ('Manikchak High School Ganga Flood Haven', 'School_Building', 'Malda', 'Manikchak Ghat', 25.075000, 87.912000, 500, 45, 1, 1, 'Shri Partha Ghosh (BDO Manikchak)', '+91 94340 77101'),
        ('Kandi Sub-Divisional Flood Relief Shelter', 'Flood_Center', 'Murshidabad', 'Kandi Hospital Road', 23.954000, 88.038000, 650, 70, 1, 1, 'Dr. S. K. Roy (Sub-Divisional Officer)', '+91 94340 77102'),
        ('Gosaba Multi-Hazard Cyclone & Flood Shelter #3', 'Cyclone_Shelter', 'South 24 Parganas', 'Rangabelia Bazar', 22.169000, 88.809000, 800, 120, 1, 1, 'Inspector Amalendu Mondal (Disaster Mgmt)', '+91 94340 77103'),
        ('Ghatal Elevated Flood Refuge Center', 'Flood_Center', 'Paschim Medinipur', 'Ghatal Old Bus Stand', 22.673000, 87.724000, 550, 60, 1, 1, 'Shri T. K. Maiti (Municipality Officer)', '+91 94340 77104'),
        ('Onda Panchayat Bhavan Lightning Protected Shelter', 'Elevated_Panchayat_Bhavan', 'Bankura', 'Punisol More', 23.146000, 87.198000, 350, 20, 1, 1, 'Smt. Anjali Mahato (Pradhan)', '+91 94340 77105')
    ]
    for row in shelters_data:
        cur.execute("""
            INSERT OR REPLACE INTO emergency_shelters
            (shelter_name, shelter_type, district, village, latitude, longitude, capacity_persons, current_occupancy, lightning_protection_installed, generator_backup, contact_officer, contact_phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, row)

    alerts_data = [
        ('ALT-2026-LGT-01', 'Lightning', 'Severe_Emergency', 'URGENT: Intense Cloud-to-Ground Lightning Strikes Detected', 'Varanasi', 25.425000, 82.845000, 12.50, 'SEVERE LIGHTNING WARNING: 40+ strikes/min recorded within 12km. CEASE ALL OUTDOOR FIELD WORK IMMEDIATELY.', 'अत्यंत गंभीर आकाशीय बिजली चेतावनी: 12 किमी क्षेत्र में तुरंत खेतों में काम बंद करें।', 1, 142, 142),
        ('ALT-2026-FLD-02', 'Flash_Flood', 'Warning', 'Rapti River Rapid Water Surge & Low-Lying Inundation', 'Gorakhpur', 26.730000, 83.350000, 18.00, 'RIVER FLOOD WARNING: Rapti River water level has crossed Danger Mark. Move harvest to elevated ground.', 'राप्ती नदी बाढ़ चेतावनी: नदी का जलस्तर खतरे के निशान को पार कर गया है।', 1, 310, 310)
    ]
    for row in alerts_data:
        cur.execute("""
            INSERT OR REPLACE INTO weather_alerts
            (alert_code, hazard_type, severity_level, title, district, epicenter_lat, epicenter_lon, radius_km, instruction_text, instruction_text_hindi, is_active, farmers_impacted, dispatched_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, row)

def init_db():
    """
    Initializes database schema and seed data if not already present.
    Supports both MySQL (local/cloud) and SQLite (Vercel serverless fallback).
    """
    if is_sqlite_mode() or _is_sqlite_active:
        conn = get_sqlite_connection()
        init_sqlite_tables(conn)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) AS total FROM farmers")
            result = cursor.fetchone()
            if not result or result['total'] == 0:
                print("[Database] Seeding initial data into SQLite...")
                seed_sqlite_data(conn)
            print("[Database] SQLite serverless database ready.")
        finally:
            cursor.close()
            conn.close()
        return

    base_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(base_dir, 'schema.sql')
    seed_path = os.path.join(base_dir, 'seed_data.sql')

    print("[Database] Checking MySQL database initialization...")
    execute_sql_file(schema_path)

    conn = get_db_connection(use_database=True)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) AS total FROM farmers")
        result = cursor.fetchone()
        if result['total'] == 0:
            print("[Database] Seeding initial mock data into MySQL...")
            execute_sql_file(seed_path)
        print("[Database] MySQL database initialized and ready.")
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


