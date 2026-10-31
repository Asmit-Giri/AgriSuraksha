-- ====================================================================
-- Seed Data: farmer_alert_db
-- Realistic dataset for prototype testing and evaluation
-- ====================================================================

USE farmer_alert_db;

-- 1. Insert Sample Farmers (UP, Bihar, West Bengal, Andhra Pradesh)
INSERT INTO farmers 
(farmer_code, full_name, phone, alternate_phone, state, district, sub_district, village, latitude, longitude, farm_size_acres, crops_grown, preferred_language, alert_sms, alert_whatsapp, alert_ivr, safety_status) 
VALUES
('FMR-1001', 'Ramesh Chandra Patel', '+91 98765 43210', '+91 98765 43219', 'Uttar Pradesh', 'Varanasi', 'Pindra', 'Phulpur Buzurg', 25.421500, 82.842300, 4.50, 'Paddy (Basmati), Wheat, Mustard', 'Hindi', 1, 1, 1, 'In Field'),
('FMR-1002', 'Sunita Devi Yadav', '+91 94150 12345', NULL, 'Uttar Pradesh', 'Varanasi', 'Sadar', 'Shivpur Khas', 25.362100, 82.951400, 2.20, 'Vegetables (Tomato, Cauliflower), Paddy', 'Hindi', 1, 1, 0, 'Safe'),
('FMR-1003', 'Gurpreet Singh Dhillon', '+91 98140 87654', '+91 98140 87655', 'Uttar Pradesh', 'Gorakhpur', 'Sahjanwa', 'Bhari Baisan', 26.745100, 83.214500, 8.00, 'Sugarcane, Paddy, Maize', 'Punjabi', 1, 1, 0, 'At Risk'),
('FMR-1004', 'Manoj Kumar Maurya', '+91 97920 33445', NULL, 'Uttar Pradesh', 'Gorakhpur', 'Chauri Chaura', 'Rampur Buzurg', 26.689200, 83.562100, 3.10, 'Paddy, Black Gram (Urad), Lentil', 'Hindi', 1, 0, 1, 'In Field'),
('FMR-1005', 'Anand Swaroop Tiwari', '+91 94501 99887', '+91 94501 99888', 'Uttar Pradesh', 'Prayagraj', 'Soraon', 'Mau Aima Dehat', 25.621400, 81.874100, 5.00, 'Guava Orchards, Paddy, Wheat', 'Hindi', 1, 1, 1, 'Safe'),
('FMR-1006', 'Dhirendra Narayan Rai', '+91 91250 66778', NULL, 'Uttar Pradesh', 'Ayodhya', 'Sohawal', 'Rudauli North', 26.772500, 81.896400, 6.20, 'Paddy, Mustard, Sugarcane', 'English', 1, 1, 0, 'Safe'),
('FMR-1007', 'Kavita Kumari Roy', '+91 99341 55667', NULL, 'Bihar', 'Patna', 'Danapur', 'Nasriganj Diara', 25.641200, 85.042500, 1.80, 'Diara Vegetables, Maize, Watermelon', 'Hindi', 1, 1, 1, 'At Risk'),
('FMR-1008', 'Abdul Halim Ansari', '+91 98350 44332', '+91 98350 44333', 'Bihar', 'Patna', 'Fatuha', 'Kachi Dargah', 25.568400, 85.289100, 3.75, 'Paddy, Jute, Mustard', 'Hindi', 1, 1, 0, 'In Field'),
('FMR-1009', 'Bijoy Krishna Das', '+91 97321 88990', NULL, 'West Bengal', 'Malda', 'Harischandrapur', 'Bhaluka North', 25.431200, 87.954100, 4.00, 'Makhana, Aman Paddy, Jute', 'Bengali', 1, 1, 1, 'Safe'),
('FMR-1010', 'Bhavani Shankar Reddy', '+91 94401 22334', NULL, 'Andhra Pradesh', 'Guntur', 'Tenali', 'Angalakuduru', 16.241500, 80.642100, 5.50, 'Chilli, Cotton, Paddy', 'Telugu', 1, 1, 0, 'Safe'),
-- West Bengal Farmers
('FMR-2001', 'Subhash Chandra Mondal', '+91 97330 11223', NULL, 'West Bengal', 'Murshidabad', 'Bhagawangola', 'Habibpur', 24.321400, 88.291200, 3.50, 'Jute, Mustard, Aman Paddy', 'Bengali', 1, 1, 1, 'In Field'),
('FMR-2002', 'Debashis Banerjee', '+91 98321 44556', '+91 98321 44557', 'West Bengal', 'Purba Bardhaman', 'Kalna', 'Dhatrigram', 23.218500, 88.314200, 4.20, 'Boro Paddy, Potato, Mustard', 'Bengali', 1, 1, 0, 'Safe'),
('FMR-2003', 'Animesh Sardar', '+91 94741 77889', NULL, 'West Bengal', 'South 24 Parganas', 'Gosaba', 'Rangabelia', 22.164800, 88.802100, 2.80, 'Saline-resistant Aman Paddy, Betel Vine, Vegetables', 'Bengali', 1, 1, 1, 'At Risk'),
('FMR-2004', 'Tapas Kumar Ghosh', '+91 96472 33441', NULL, 'West Bengal', 'Nadia', 'Ranaghat', 'Habibpur Ghat', 23.181200, 88.562400, 3.00, 'Pointed Gourd (Patol), Jute, Paddy', 'Bengali', 1, 1, 0, 'Safe'),
('FMR-2005', 'Bikash Chandra Mahato', '+91 95470 55662', NULL, 'West Bengal', 'Bankura', 'Onda', 'Punisol', 23.142000, 87.195000, 5.00, 'Groundnut, Maize, Aman Paddy', 'Bengali', 1, 1, 1, 'In Field'),
('FMR-2006', 'Pranab Kanti Samanta', '+91 97355 88994', '+91 97355 88995', 'West Bengal', 'Paschim Medinipur', 'Ghatal', 'Monoharpur', 22.671000, 87.721500, 2.50, 'Boro Paddy, Winter Potato, Sesame', 'Bengali', 1, 1, 1, 'At Risk'),
('FMR-2007', 'Nirmal Kanti Roy', '+91 98320 66773', NULL, 'West Bengal', 'Jalpaiguri', 'Mainaguri', 'Padamoti', 26.562100, 88.824500, 6.00, 'Aman Paddy, Jute, Tea Leaves', 'Bengali', 1, 1, 0, 'Safe'),
('FMR-2008', 'Sukumar Das', '+91 94340 99112', NULL, 'West Bengal', 'Hooghly', 'Arambagh', 'Mayapur Char', 22.884500, 87.781200, 3.80, 'Jyoti Potato, Boro Paddy, Jute', 'Bengali', 1, 1, 0, 'In Field'),
('FMR-2009', 'Abhijit Biswas', '+91 98311 22334', NULL, 'West Bengal', 'North 24 Parganas', 'Basirhat', 'Dandirhat', 22.654000, 88.892000, 2.20, 'Aman Paddy, Vegetables, Til', 'Bengali', 1, 1, 0, 'Safe'),
('FMR-2010', 'Biren Chandra Barman', '+91 94750 33445', NULL, 'West Bengal', 'Cooch Behar', 'Dinhata', 'Bhitarkamta', 26.134000, 89.467000, 4.50, 'Tobacco, Jute, Paddy', 'Bengali', 1, 1, 1, 'Safe')
ON DUPLICATE KEY UPDATE full_name=VALUES(full_name), village=VALUES(village), district=VALUES(district);

-- 2. Insert Sensor & Weather Stations
INSERT INTO sensor_stations
(station_code, station_name, station_type, district, river_basin, latitude, longitude, current_rainfall_mm, river_water_level_m, danger_water_level_m, lightning_flash_rate_per_min, peak_strike_current_ka, status)
VALUES
('AWS-VNS-01', 'Varanasi Babatpur Radar & AWS', 'Combined_AWS', 'Varanasi', 'Ganga Basin', 25.452200, 82.859400, 48.50, 71.80, 71.26, 42, 65.40, 'Emergency'),
('LGT-GKP-02', 'Gorakhpur Lightning Early Detection Unit', 'Lightning_Detector', 'Gorakhpur', 'Rapti Basin', 26.760600, 83.373200, 18.20, 0.00, 0.00, 68, 89.20, 'Warning'),
('STR-GKP-03', 'Rapti River Birdghat Stream Gauge', 'Stream_Gauge', 'Gorakhpur', 'Rapti Basin', 26.721400, 83.351200, 62.00, 75.85, 74.98, 0, 0.00, 'Emergency'),
('STR-PRY-04', 'Prayagraj Phaphamau Ganga Gauge', 'Stream_Gauge', 'Prayagraj', 'Ganga-Yamuna Basin', 25.512000, 81.854000, 22.40, 84.10, 84.73, 5, 12.00, 'Watch'),
('AWS-PAT-05', 'Patna Digha Flood Telemetry Unit', 'Combined_AWS', 'Patna', 'Ganga-Son Basin', 25.642000, 85.098000, 39.80, 50.15, 50.52, 28, 44.50, 'Warning'),
-- West Bengal Telemetry
('STR-MLD-06', 'Farakka Barrage Ganga Hydro Gauge', 'Stream_Gauge', 'Malda', 'Ganga-Bhagirathi Basin', 24.801000, 87.925000, 45.20, 22.80, 22.25, 0, 0.00, 'Emergency'),
('LGT-BNK-07', 'Bankura Chhotanagpur Lightning Early Warning Unit', 'Lightning_Detector', 'Bankura', 'Damodar-Kangsabati Basin', 23.225000, 87.081000, 15.00, 0.00, 0.00, 58, 76.40, 'Warning'),
('AWS-S24-08', 'Sundarbans Coastal Doppler & Storm AWS', 'Combined_AWS', 'South 24 Parganas', 'Sundarbans Delta', 22.180000, 88.810000, 72.40, 4.80, 4.20, 34, 48.20, 'Warning'),
('STR-GHT-09', 'Ghatal Shilabati River Stream Gauge', 'Stream_Gauge', 'Paschim Medinipur', 'Shilabati Basin', 22.668000, 87.718000, 58.00, 13.40, 12.80, 12, 22.00, 'Emergency')
ON DUPLICATE KEY UPDATE station_name=VALUES(station_name);

-- 3. Insert Emergency Safe Shelters
INSERT INTO emergency_shelters
(shelter_name, shelter_type, district, village, latitude, longitude, capacity_persons, current_occupancy, lightning_protection_installed, generator_backup, contact_officer, contact_phone)
VALUES
('Phulpur Multi-Hazard Relief Shelter', 'Flood_Center', 'Varanasi', 'Phulpur Buzurg', 25.429000, 82.839000, 450, 35, 1, 1, 'Shri Anand Verma (BDO Pindra)', '+91 94544 11201'),
('Panchayat Bhavan Elevated Shelter Shivpur', 'Elevated_Panchayat_Bhavan', 'Varanasi', 'Shivpur Khas', 25.367000, 82.948000, 200, 12, 1, 1, 'Smt. Pratima Devi (Gram Pradhan)', '+91 94544 11202'),
('Sahjanwa High School Flood Refuge', 'School_Building', 'Gorakhpur', 'Bhari Baisan', 26.749000, 83.219000, 600, 85, 1, 1, 'Dr. R. K. Srivastava (Principal)', '+91 94544 22301'),
('Chauri Chaura Cyclone & Storm Haven', 'Cyclone_Shelter', 'Gorakhpur', 'Rampur Buzurg', 26.694000, 83.568000, 500, 40, 1, 1, 'Shri M. P. Singh (Tehsildar)', '+91 94544 22302'),
('Danapur Diara Elevated Flood Shelter #2', 'Flood_Center', 'Patna', 'Nasriganj Diara', 25.648000, 85.049000, 750, 140, 1, 1, 'Inspector Rajiv Sinha (SDRF Bihar)', '+91 94318 33401'),
-- West Bengal Shelters
('Manikchak High School Ganga Flood Haven', 'School_Building', 'Malda', 'Manikchak Ghat', 25.075000, 87.912000, 500, 45, 1, 1, 'Shri Partha Ghosh (BDO Manikchak)', '+91 94340 77101'),
('Kandi Sub-Divisional Flood Relief Shelter', 'Flood_Center', 'Murshidabad', 'Kandi Hospital Road', 23.954000, 88.038000, 650, 70, 1, 1, 'Dr. S. K. Roy (Sub-Divisional Officer)', '+91 94340 77102'),
('Gosaba Multi-Hazard Cyclone & Flood Shelter #3', 'Cyclone_Shelter', 'South 24 Parganas', 'Rangabelia Bazar', 22.169000, 88.809000, 800, 120, 1, 1, 'Inspector Amalendu Mondal (Disaster Mgmt)', '+91 94340 77103'),
('Ghatal Elevated Flood Refuge Center', 'Flood_Center', 'Paschim Medinipur', 'Ghatal Old Bus Stand', 22.673000, 87.724000, 550, 60, 1, 1, 'Shri T. K. Maiti (Municipality Officer)', '+91 94340 77104'),
('Onda Panchayat Bhavan Lightning Protected Shelter', 'Elevated_Panchayat_Bhavan', 'Bankura', 'Punisol More', 23.146000, 87.198000, 350, 20, 1, 1, 'Smt. Anjali Mahato (Pradhan)', '+91 94340 77105')
ON DUPLICATE KEY UPDATE shelter_name=VALUES(shelter_name);

-- 4. Insert Initial Active Weather Alerts
INSERT INTO weather_alerts
(alert_code, hazard_type, severity_level, title, district, epicenter_lat, epicenter_lon, radius_km, instruction_text, instruction_text_hindi, is_active, farmers_impacted, dispatched_count, expires_at)
VALUES
('ALT-2026-LGT-01', 'Lightning', 'Severe_Emergency', 'URGENT: Intense Cloud-to-Ground Lightning Strikes Detected', 'Varanasi', 25.425000, 82.845000, 12.50, 
'SEVERE LIGHTNING WARNING: 40+ strikes/min recorded within 12km. CEASE ALL OUTDOOR FIELD WORK IMMEDIATELY. Do not seek shelter under isolated trees, tin sheds, or metal tractors. Move inside pucca buildings or enclosed vehicles. Keep livestock untethered in safe enclosures.', 
'अत्यंत गंभीर आकाशीय बिजली चेतावनी: 12 किमी क्षेत्र में प्रति मिनट 40 से अधिक वज्रपात दर्ज किए गए हैं। तुरंत खेतों में काम बंद करें और खुले में न रहें। ऊंचे पेड़ों, बिजली के खंभों, टिन शेड या ट्रैक्टर के नीचे शरण न लें। पक्के मकान में सुरक्षित जाएं।', 
1, 142, 142, DATE_ADD(NOW(), INTERVAL 3 HOUR)),

('ALT-2026-FLD-02', 'Flash_Flood', 'Warning', 'Rapti River Rapid Water Surge & Low-Lying Inundation', 'Gorakhpur', 26.730000, 83.350000, 18.00,
'RIVER FLOOD WARNING: Rapti River water level has crossed Danger Mark (74.98m) and reached 75.85m. Low-lying agricultural fields in Sahjanwa and Campierganj blocks are facing imminent submergence. Evacuate harvest and machinery to elevated ground. Report to Sahjanwa High School Refuge if water enters village.',
'राप्ती नदी बाढ़ चेतावनी: नदी का जलस्तर खतरे के निशान (74.98 मी) को पार कर 75.85 मीटर पहुंच गया है। सहजनवा क्षेत्र के निचले खेतों में जलभराव शुरू हो चुका है। अपनी कटी हुई फसल, मवेशी और कृषि उपकरण तुरंत ऊंचे स्थानों पर पहुंचाएं।',
1, 310, 310, DATE_ADD(NOW(), INTERVAL 12 HOUR)),

('ALT-2026-FLD-03', 'River_Overflow', 'Severe_Emergency', 'Shilabati River Basin Inundation & Ghatal Flood Alert', 'Paschim Medinipur', 22.671000, 87.721500, 20.00,
'CRITICAL FLOOD WARNING: Shilabati river is flowing 0.60m above danger level. Extensive inundation in Ghatal and Daspur blocks. Farmers must move harvest from fields to Elevated Flood Refuge Center immediately.',
'বিপর্যয় সতর্কতা: শিলাবতী নদীর জল বিপদসীমার উপরে প্রবাহিত হচ্ছে। ঘাটাল ও দাসপুর ব্লকের কৃষিজমিতে জল ঢুকছে। দ্রুত পাকা ধান ও গবাদি পশু নিরাপদ আশ্রয়কেন্দ্রে সরিয়ে নিন।',
1, 240, 240, DATE_ADD(NOW(), INTERVAL 10 HOUR))
ON DUPLICATE KEY UPDATE title=VALUES(title);

-- 5. Insert Sample Alert Dispatches
INSERT INTO alert_dispatches
(alert_id, farmer_id, delivery_channel, message_content, language_used, status, farmer_ack)
VALUES
(1, 1, 'WhatsApp', '🚨 ALERT: Severe Lightning strikes (40/min) detected in Pindra/Varanasi! Move indoors immediately. 30-30 Rule in effect.', 'Hindi', 'Delivered', 'Acknowledged_Safe'),
(1, 1, 'SMS', 'Kisan Alert: Vajrapaat ki chetavani! Khet se bahar nikle aur pakke makan me jaye.', 'Hindi', 'Delivered', 'Acknowledged_Safe'),
(2, 3, 'SMS', 'Flood Alert: Rapti river above danger mark. Move livestock and crops to elevated ground.', 'Punjabi', 'Delivered', 'Acknowledged_Evacuating'),
(2, 4, 'WhatsApp', 'Flood Alert: Rapti river overflow imminent in Chauri Chaura belt. Evacuate to nearest shelter.', 'Hindi', 'Delivered', 'Pending')
ON DUPLICATE KEY UPDATE message_content=VALUES(message_content);

-- 6. Insert Sample Distress / SOS Request
INSERT INTO farmer_sos_requests
(farmer_id, alert_id, distress_type, emergency_notes, gps_lat, gps_lon, rescue_status, assigned_team)
VALUES
(4, 2, 'Trapped_In_Field', 'Farmer trapped in tube-well shed with 4 cattle due to sudden flood surge from stream. Water level 3.5 feet.', 26.689200, 83.562100, 'Team_Dispatched', 'Gorakhpur NDRF Unit 4');
