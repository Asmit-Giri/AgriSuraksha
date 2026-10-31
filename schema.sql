-- ====================================================================
-- Database Schema: farmer_alert_db
-- Lightning and Flood Alert Registry for Farmers
-- MySQL 8.0+
-- ====================================================================

CREATE DATABASE IF NOT EXISTS farmer_alert_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE farmer_alert_db;

-- 1. Farmers Registry Table
CREATE TABLE IF NOT EXISTS farmers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    farmer_code VARCHAR(20) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    alternate_phone VARCHAR(20),
    state VARCHAR(50) NOT NULL DEFAULT 'Uttar Pradesh',
    district VARCHAR(50) NOT NULL,
    sub_district VARCHAR(50) NOT NULL,
    village VARCHAR(80) NOT NULL,
    latitude DECIMAL(10, 6) NOT NULL,
    longitude DECIMAL(10, 6) NOT NULL,
    farm_size_acres DECIMAL(6, 2) DEFAULT 2.50,
    crops_grown VARCHAR(255) DEFAULT 'Paddy, Mustard',
    preferred_language VARCHAR(30) DEFAULT 'English',
    alert_sms BOOLEAN DEFAULT TRUE,
    alert_whatsapp BOOLEAN DEFAULT TRUE,
    alert_ivr BOOLEAN DEFAULT FALSE,
    safety_status ENUM('Safe', 'In Field', 'At Risk', 'Evacuating', 'SOS_Distress') DEFAULT 'Safe',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_district (district),
    INDEX idx_coords (latitude, longitude),
    INDEX idx_phone (phone)
) ENGINE=InnoDB;

-- 2. Weather & Hydrological Sensor Telemetry Stations
CREATE TABLE IF NOT EXISTS sensor_stations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    station_code VARCHAR(30) NOT NULL UNIQUE,
    station_name VARCHAR(100) NOT NULL,
    station_type ENUM('Lightning_Detector', 'Stream_Gauge', 'Rain_Gauge', 'Combined_AWS') NOT NULL,
    district VARCHAR(50) NOT NULL,
    river_basin VARCHAR(80) DEFAULT 'Ganga-Ghaghara Basin',
    latitude DECIMAL(10, 6) NOT NULL,
    longitude DECIMAL(10, 6) NOT NULL,
    current_rainfall_mm DECIMAL(6, 2) DEFAULT 0.00,
    river_water_level_m DECIMAL(6, 2) DEFAULT 0.00,
    danger_water_level_m DECIMAL(6, 2) DEFAULT 12.00,
    lightning_flash_rate_per_min INT DEFAULT 0,
    peak_strike_current_ka DECIMAL(6, 2) DEFAULT 0.00,
    status ENUM('Normal', 'Advisory', 'Watch', 'Warning', 'Emergency') DEFAULT 'Normal',
    last_reading_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_station_type (station_type),
    INDEX idx_station_district (district)
) ENGINE=InnoDB;

-- 3. Emergency Safe Shelters Table
CREATE TABLE IF NOT EXISTS emergency_shelters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    shelter_name VARCHAR(120) NOT NULL,
    shelter_type ENUM('Flood_Center', 'Cyclone_Shelter', 'Elevated_Panchayat_Bhavan', 'School_Building') NOT NULL,
    district VARCHAR(50) NOT NULL,
    village VARCHAR(80) NOT NULL,
    latitude DECIMAL(10, 6) NOT NULL,
    longitude DECIMAL(10, 6) NOT NULL,
    capacity_persons INT NOT NULL DEFAULT 250,
    current_occupancy INT DEFAULT 0,
    lightning_protection_installed BOOLEAN DEFAULT TRUE,
    generator_backup BOOLEAN DEFAULT TRUE,
    contact_officer VARCHAR(100) NOT NULL,
    contact_phone VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_shelter_district (district)
) ENGINE=InnoDB;

-- 4. Weather Alerts Table
CREATE TABLE IF NOT EXISTS weather_alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    alert_code VARCHAR(30) NOT NULL UNIQUE,
    hazard_type ENUM('Lightning', 'Flash_Flood', 'Thunderstorm_Severe', 'River_Overflow') NOT NULL,
    severity_level ENUM('Advisory', 'Watch', 'Warning', 'Severe_Emergency') NOT NULL,
    title VARCHAR(150) NOT NULL,
    district VARCHAR(50) NOT NULL,
    epicenter_lat DECIMAL(10, 6) NOT NULL,
    epicenter_lon DECIMAL(10, 6) NOT NULL,
    radius_km DECIMAL(6, 2) NOT NULL DEFAULT 10.00,
    instruction_text TEXT NOT NULL,
    instruction_text_hindi TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    farmers_impacted INT DEFAULT 0,
    dispatched_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,
    INDEX idx_active_alerts (is_active, hazard_type),
    INDEX idx_alert_district (district)
) ENGINE=InnoDB;

-- 5. Alert Dispatches (Communication Audit Trail)
CREATE TABLE IF NOT EXISTS alert_dispatches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    alert_id INT NOT NULL,
    farmer_id INT NOT NULL,
    delivery_channel ENUM('SMS', 'WhatsApp', 'IVR_Call') NOT NULL,
    message_content TEXT NOT NULL,
    language_used VARCHAR(30) DEFAULT 'English',
    status ENUM('Queued', 'Sent', 'Delivered', 'Failed') DEFAULT 'Delivered',
    farmer_ack ENUM('Pending', 'Acknowledged_Safe', 'Acknowledged_Evacuating', 'SOS') DEFAULT 'Pending',
    dispatched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (alert_id) REFERENCES weather_alerts(id) ON DELETE CASCADE,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE,
    INDEX idx_dispatch_alert (alert_id),
    INDEX idx_dispatch_farmer (farmer_id)
) ENGINE=InnoDB;

-- 6. Farmer Distress / SOS Emergency Requests
CREATE TABLE IF NOT EXISTS farmer_sos_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    farmer_id INT NOT NULL,
    alert_id INT NULL,
    distress_type ENUM('Lightning_Victim', 'Trapped_In_Field', 'Livestock_Threatened', 'Shelter_Required') NOT NULL,
    emergency_notes TEXT,
    gps_lat DECIMAL(10, 6) NOT NULL,
    gps_lon DECIMAL(10, 6) NOT NULL,
    rescue_status ENUM('Reported', 'Assigned', 'Team_Dispatched', 'Rescued', 'Resolved') DEFAULT 'Reported',
    assigned_team VARCHAR(100) DEFAULT 'Quick Response Team #1',
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE,
    FOREIGN KEY (alert_id) REFERENCES weather_alerts(id) ON DELETE SET NULL,
    INDEX idx_sos_status (rescue_status)
) ENGINE=InnoDB;

