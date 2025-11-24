-- Drop existing tables
DROP TABLE IF EXISTS JOB_APPLICATION;
DROP TABLE IF EXISTS APPOINTMENT;
DROP TABLE IF EXISTS JOB;
DROP TABLE IF EXISTS ADDRESS;
DROP TABLE IF EXISTS MEMBER;
DROP TABLE IF EXISTS CAREGIVER;
DROP TABLE IF EXISTS USER;

-- Create Tables
-- User
CREATE TABLE USER (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL UNIQUE,
    given_name VARCHAR(100) NOT NULL,
    surname VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    profile_description TEXT,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT check_email_format CHECK (email LIKE '%@%.%'),
    CONSTRAINT check_phone_length CHECK (
            LENGTH(phone_number) = 11 AND
            phone_number REGEXP '^[0-9]{11}$'
        )
);


-- Caregiver
CREATE TABLE CAREGIVER (
    caregiver_user_id INT PRIMARY KEY,
    photo VARCHAR(500),
    gender ENUM('Male', 'Female', 'Other', 'Prefer not to say') NOT NULL,
    caregiving_type ENUM('babysitter', 'caregiver for elderly', 'playmate for children') NOT NULL,
    hourly_rate INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    rating DECIMAL(3, 2) DEFAULT 0.00,
    total_reviews INT DEFAULT 0,

    CONSTRAINT fk_caregiver_user FOREIGN KEY (caregiver_user_id)
        REFERENCES USER(user_id) ON DELETE CASCADE,

    CONSTRAINT check_hourly_rate CHECK (hourly_rate >= 0),
    CONSTRAINT check_rating CHECK (rating >= 0 AND rating <= 5.00)
);


-- Member
CREATE TABLE MEMBER (
    member_user_id INT PRIMARY KEY,
    house_rules TEXT,
    dependent_description TEXT,

    CONSTRAINT fk_member_user FOREIGN KEY (member_user_id)
        REFERENCES USER(user_id) ON DELETE CASCADE
);


-- Address
CREATE TABLE ADDRESS (
    address_id INT PRIMARY KEY AUTO_INCREMENT,
    member_user_id INT NOT NULL,
    house_number VARCHAR(10) NOT NULL,
    street VARCHAR(200) NOT NULL,
    town VARCHAR(100) NOT NULL,

    CONSTRAINT fk_address_member FOREIGN KEY (member_user_id)
        REFERENCES MEMBER(member_user_id) ON DELETE CASCADE
);


-- Job
CREATE TABLE JOB (
    job_id INT PRIMARY KEY AUTO_INCREMENT,
    member_user_id INT NOT NULL,
    required_caregiving_type ENUM('babysitter', 'caregiver for elderly', 'playmate for children') NOT NULL,
    other_requirements TEXT,
    date_posted DATE NOT NULL,
    status ENUM('open', 'closed') DEFAULT 'open',

    dependent_age INT,
    preferred_time_start TIME,
    preferred_time_end TIME,
    frequency ENUM('daily', 'weekly', 'weekends only', 'as needed') DEFAULT 'as needed',
    duration INT,

    CONSTRAINT fk_job_member FOREIGN KEY (member_user_id)
        REFERENCES MEMBER(member_user_id) ON DELETE CASCADE,

    CONSTRAINT check_dependent_age CHECK (dependent_age >= 0 AND dependent_age <= 200),
    CONSTRAINT check_time_range CHECK (preferred_time_start < preferred_time_end)
);

-- Job Application
CREATE TABLE JOB_APPLICATION (
    application_id INT PRIMARY KEY AUTO_INCREMENT,
    caregiver_user_id INT NOT NULL,
    job_id INT NOT NULL,
    date_applied DATE NOT NULL,
    cover_letter TEXT,
    application_status ENUM('pending', 'reviewed', 'accepted', 'rejected') DEFAULT 'pending',

    CONSTRAINT fk_application_caregiver FOREIGN KEY (caregiver_user_id)
        REFERENCES CAREGIVER(caregiver_user_id) ON DELETE CASCADE,
    CONSTRAINT fk_application_job FOREIGN KEY (job_id)
        REFERENCES JOB(job_id) ON DELETE CASCADE,

    CONSTRAINT unique_application UNIQUE (caregiver_user_id, job_id)
);

-- Appointment
CREATE TABLE APPOINTMENT (
    appointment_id INT PRIMARY KEY AUTO_INCREMENT,
    caregiver_user_id INT NOT NULL,
    member_user_id INT NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    work_hours DECIMAL(4, 2) NOT NULL,
    status ENUM('pending', 'confirmed', 'declined', 'completed', 'cancelled') DEFAULT 'pending',
    total_cost DECIMAL(10, 2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_appointment_caregiver FOREIGN KEY (caregiver_user_id)
        REFERENCES CAREGIVER(caregiver_user_id) ON DELETE CASCADE,
    CONSTRAINT fk_appointment_member FOREIGN KEY (member_user_id)
        REFERENCES MEMBER(member_user_id) ON DELETE CASCADE,

    CONSTRAINT check_work_hours CHECK (work_hours > 0 AND work_hours <= 24),
    CONSTRAINT check_total_cost CHECK (total_cost >= 0)
);

-- Indexes
-- User Index
CREATE INDEX idx_user_city ON USER(city);
CREATE INDEX idx_user_name ON USER(given_name, surname);

-- Caregiver Index
CREATE INDEX idx_caregiver_type ON CAREGIVER(caregiving_type);
CREATE INDEX idx_caregiver_activity ON CAREGIVER(is_active);
CREATE INDEX idx_caregiver_rating ON CAREGIVER(rating DESC, total_reviews DESC);

-- Address Index
CREATE INDEX idx_address_street ON ADDRESS(street);
CREATE INDEX idx_address_town ON ADDRESS(town);

-- Job Index
CREATE INDEX idx_job_member ON JOB(member_user_id);
CREATE INDEX idx_job_type ON JOB(required_caregiving_type);
CREATE INDEX idx_job_status ON JOB(status);
CREATE INDEX idx_job_date ON JOB(date_posted DESC);

-- Job Application Index
CREATE INDEX idx_application_caregiver ON JOB_APPLICATION(caregiver_user_id);
CREATE INDEX idx_application_job ON JOB_APPLICATION(job_id);
CREATE INDEX idx_application_status ON JOB_APPLICATION(application_status);

-- Appointment Index
CREATE INDEX idx_appointment_caregiver ON APPOINTMENT(caregiver_user_id);
CREATE INDEX idx_appointment_member ON APPOINTMENT(member_user_id);
CREATE INDEX idx_appointment_date ON APPOINTMENT(appointment_date);
CREATE INDEX idx_appointment_status ON APPOINTMENT(status);

-- Sample Data
-- User Members
INSERT INTO USER (email, given_name, surname, city, phone_number, profile_description, password) VALUES
('aidar.bekmuratov@gmail.com', 'Aidar', 'Bekmuratov', 'Almaty', '77081234567', '', '88925/Am'),
('dinara.sultanova@gmail.com', 'Dinara', 'Sultanova', 'Astana', '77771928374', '', 'y?9#M228'),
('yerlan.omarov@gmail.com', 'Yerlan', 'Omarov', 'Taraz', '77085647382', '', 'kl2345ihu'),
('asel.nurzhanova@gmail.com', 'Asel', 'Nurzhanova', 'Almaty', '77779283746', '', 'dsfklsdfg89'),
('murat.akhmetov@gmail.com', 'Murat', 'Akhmetov', 'Almaty', '77713829475', '', 'ljksdfg789'),
('saule.zhaksylykova@gmail.com', 'Saule', 'Zhaksylykova', 'Taraz', '77775638291', '', 'jklhasdf578'),
('nurzhan.alimzhanov@gmail.com', 'Nurzhan', 'Alimzhanov', 'Kostanay', '77089374652', '', 'vlcvbk231'),
('zhanna.serikova@gmail.com', 'Zhanna', 'Serikova', 'Astana', '77778392847', '', 'JKHt9034'),
('arman.tulegenov@gmail.com', 'Arman', 'Tulegenov', 'Kostanay', '77716485927', '', 'iHop83459'),
('gaukhar.mukhanova@gmail.com', 'Gaukhar', 'Mukhanova', 'Taraz', '77773829561', '', '1234598iasd'),
('arman.armanov@gmail.com', 'Arman', 'Armanov', 'Almaty', '77712345678', '', 'pass123'),
('amina.aminova@gmail.com', 'Amina', 'Aminova', 'Astana', '77771234567', '', 'amina2024');

-- User Caregivers Insert
INSERT INTO USER (email, given_name, surname, city, phone_number, profile_description, password) VALUES
('baurzhan.karimov@gmail.com', 'Baurzhan', 'Karimov', 'Almaty', '77082937465', '', 'fD4#tY7$nK'),
('madina.zhunisova@gmail.com', 'Madina', 'Zhunisova', 'Astana', '77774826193', '', 'xP9@mW3&hL'),
('dauren.ospanov@gmail.com', 'Dauren', 'Ospanov', 'Taraz', '77719263847', '', 'rN2^kV8#qT'),
('aliya.kassymova@gmail.com', 'Aliya', 'Kassymova', 'Almaty', '77083746529', '', 'bH6$wZ1@mP'),
('timur.suleimenov@gmail.com', 'Timur', 'Suleimenov', 'Almaty', '77778394756', '', 'yL4#pR9&cX'),
('kamila.baiguzhinova@gmail.com', 'Kamila', 'Baiguzhinova', 'Taraz', '77715829364', '', 'nT7^gK2$vW'),
('serik.amangeldy@gmail.com', 'Serik', 'Amangeldy', 'Kostanay', '77089182736', '', 'qM5@hX8#nL'),
('roza.abilova@gmail.com', 'Roza', 'Abilova', 'Astana', '77773651924', '', 'zB3$rT6&mK'),
('azamat.zhumabekov@gmail.com', 'Azamat', 'Zhumabekov', 'Kostanay', '77718293745', '', 'pW1^nH9@tY'),
('lyazzat.bakytova@gmail.com', 'Lyazzat', 'Bakytova', 'Taraz', '77082649173', '', 'cK4#xL7$vR');

-- Caregivers Insert
INSERT INTO CAREGIVER (caregiver_user_id, photo, gender, caregiving_type, hourly_rate, rating, total_reviews) VALUES
(11, 'photos/baurzhan-karimov.jpg', 'Male', 'babysitter', 25.00, 4.80, 45),
(12, 'photos/madina-zhunisova.jpg', 'Female', 'caregiver for elderly', 30.00, 4.95, 78),
(13, 'photos/dauren-ospanov.jpg', 'Male', 'playmate for children', 8.50, 4.70, 32),
(14, 'photos/aliya-kassymova.jpg', 'Female', 'babysitter', 28.00, 4.85, 62),
(15, 'photos/timur-suleimenov.jpg', 'Male', 'caregiver for elderly', 32.00, 4.90, 54),
(16, 'photos/kamila-baiguzhinova.jpg', 'Female', 'babysitter', 9.75, 4.88, 71),
(17, 'photos/serik-amangeldy.jpg', 'Prefer not to say', 'playmate for children', 7.00, 4.75, 28),
(18, 'photos/roza-abilova.jpg', 'Other', 'caregiver for elderly', 35.00, 4.92, 89),
(19, 'photos/azamat-zhumabekov.jpg', 'Male', 'babysitter', 9.50, 4.78, 41),
(20, 'photos/lyazzat-bakytova.jpg', 'Female', 'playmate for children', 23.00, 4.82, 55);

-- Members Insert
INSERT INTO MEMBER (member_user_id, house_rules, dependent_description) VALUES
(1, 'No smoking. Please remove shoes at the door. Be punctual.', 'I have a 5-year-old son who loves painting and building blocks. He is very energetic and needs constant attention.'),
(2, 'No pets. My mother has limited mobility. Please help with meal preparation and medication reminders.', 'My mother is 78 years old, has diabetes, and needs help with daily activities.'),
(3, 'Our son is shy at first but warms up quickly. He loves outdoor activities.', '6-year-old boy who enjoys sports, especially soccer. Needs a playmate 3 times a week.'),
(4, 'Pet-friendly home. We have a small dog. Flexible schedule needed.', 'Twin girls, age 3, very active and playful.'),
(5, 'Clean environment required. No pets allowed. Prefer experienced caregivers.', 'My father is 82 years old, recovering from surgery. Needs assistance with mobility and medication.'),
(6, 'Quiet household. Educational activities encouraged. Healthy meals only.', '7-year-old daughter who loves reading and drawing. Needs help with homework and creative play.'),
(7, 'No alcohol or smoking. Must be comfortable with cats. Evening availability preferred.', 'My grandmother is 85, has mild dementia. Needs companionship and help with daily routines.'),
(8, 'Respectful and kind attitude required. No pets. Open communication is important.', '4-year-old boy with high energy. Loves dinosaurs and outdoor adventures.'),
(9, 'Punctuality is essential. CPR certification preferred. Non-smoking household.', 'Twin boys, age 8, very active in sports. Need supervision after school.'),
(10, 'Flexible schedule. Must be patient and loving. We value reliability.', 'My mother is 75, uses a wheelchair. Needs help with daily care and companionship.'),
(11, 'No smoking. Quiet environment preferred.', 'Need caregiver for elderly father with mobility issues.'),
(12, 'No smoking. Pet-friendly home.', 'Looking for caregiver for my 3-year-old daughter who loves music and dancing.');

-- Address Insert
INSERT INTO ADDRESS (member_user_id, house_number, street, town) VALUES
(1, '123', 'Abay Avenue', 'Medeu District'),
(2, '456', 'Kabanbay Batyr', 'Yesil District'),
(3, '789', 'Tole Bi Street', 'Central District'),
(4, '321', 'Dostyk Avenue', 'Almaly District'),
(5, '654', 'Mangilik El Avenue', 'Saryarka District'),
(6, '147', 'Zheltoksan Street', 'Auezov District'),
(7, '258', 'Al-Farabi Avenue', 'Bostandyk District'),
(8, '369', 'Respublika Avenue', 'Yesil District'),
(9, '741', 'Abylai Khan Street', 'Central District'),
(10, '852', 'Nazarbayev Avenue', 'Central District'),
(11, '999', 'Samal Street', 'Almaly District'),
(12, '555', 'Turan Avenue', 'Yesil District');

-- Job Insert
INSERT INTO JOB (member_user_id, required_caregiving_type, other_requirements, date_posted, status, dependent_age, preferred_time_start, preferred_time_end, frequency, duration) VALUES
(1, 'babysitter', 'Must have experience with active children. CPR certification preferred. Looking for someone soft-spoken.', '2025-11-15', 'open', 5, '09:00:00', '15:00:00', 'daily', 12),
(2, 'caregiver for elderly', 'Must be patient and have experience with elderly care. Medical background is a plus. Prefer soft-spoken caregiver.', '2025-11-18', 'open', 78, '08:00:00', '12:00:00', 'daily', 8),
(3, 'playmate for children', 'Looking for someone to engage my son in outdoor activities.', '2025-11-20', 'open', 6, '15:00:00', '18:00:00', 'weekly', 4),
(4, 'babysitter', 'Need help with twin girls on weekends. Must be energetic!', '2025-11-19', 'open', 3, '10:00:00', '16:00:00', 'weekends only', 8),
(5, 'caregiver for elderly', 'Seeking experienced caregiver for post-surgery care. Must be reliable and compassionate.', '2025-11-16', 'open', 82, '07:00:00', '13:00:00', 'daily', 6),
(6, 'babysitter', 'Need someone to help with homework and creative activities after school.', '2025-11-21', 'open', 7, '14:00:00', '18:00:00', 'daily', 10),
(7, 'caregiver for elderly', 'Looking for patient caregiver for grandmother with mild dementia. Must be understanding.', '2025-11-17', 'open', 85, '16:00:00', '20:00:00', 'daily', 12),
(8, 'playmate for children', 'Need energetic person to supervise active 4-year-old. Outdoor activities encouraged.', '2025-11-22', 'open', 4, '13:00:00', '17:00:00', 'weekly', 6),
(9, 'babysitter', 'Looking for reliable caregiver for twin boys after school. Sports experience preferred.', '2025-11-14', 'open', 8, '15:00:00', '19:00:00', 'daily', 16),
(10, 'caregiver for elderly', 'Seeking compassionate caregiver for mother in wheelchair. Patience and experience required.', '2025-11-13', 'open', 75, '10:00:00', '14:00:00', 'daily', 20),
(12, 'babysitter', 'Must love music and creative activities. Experience with toddlers required.', '2025-11-23', 'open', 3, '10:00:00', '14:00:00', 'daily', 8),
(12, 'playmate for children', 'Looking for energetic person to engage my daughter in educational play.', '2025-11-23', 'open', 3, '15:00:00', '18:00:00', 'weekly', 6);

-- Job Application Insert
INSERT INTO JOB_APPLICATION (caregiver_user_id, job_id, date_applied, cover_letter, application_status) VALUES
(11, 1, '2025-11-15', 'I have 3 years of experience working with energetic children. I am patient, creative, and CPR certified. I would love to help your son develop his artistic skills.', 'pending'),
(11, 4, '2025-11-19', 'I am experienced with twins and high-energy children. I can provide engaging activities and ensure their safety at all times.', 'accepted'),
(11, 6, '2025-11-21', 'I enjoy helping children with homework and encouraging their creativity. I have a background in education and child development.', 'pending'),
(12, 2, '2025-11-18', 'I have 5 years of experience in elderly care, including working with patients with diabetes. I am patient, compassionate, and trained in medication management.', 'accepted'),
(12, 5, '2025-11-16', 'I have extensive experience in post-surgical care and mobility assistance. I am gentle and understanding with elderly patients.', 'pending'),
(12, 7, '2025-11-17', 'I have worked with dementia patients and understand the importance of routine and companionship. I am patient and caring.', 'accepted'),
(12, 10, '2025-11-13', 'I have experience caring for wheelchair-bound patients. I can provide compassionate daily care and emotional support.', 'pending'),
(13, 3, '2025-11-20', 'I love outdoor activities and sports. I can help your son build confidence and social skills through play and exercise.', 'accepted'),
(14, 6, '2025-11-21', 'I love helping children learn through play. I can assist with homework and provide educational entertainment.', 'accepted'),
(14, 9, '2025-11-14', 'I am experienced with school-age boys and can supervise sports activities. I am reliable and CPR certified.', 'pending'),
(14, 8, '2025-11-22', 'I enjoy working with preschool-age children and can organize creative play sessions.', 'rejected'),
(15, 2, '2025-11-18', 'I have a medical background and experience with diabetic care. I am thorough with medication reminders and meal preparation.', 'pending'),
(15, 5, '2025-11-16', 'I specialize in post-operative care and rehabilitation support. I am patient and dedicated to helping patients recover.', 'accepted'),
(15, 7, '2025-11-17', 'I understand the challenges of dementia care and can provide consistent, compassionate support to your grandmother.', 'pending'),
(15, 10, '2025-11-13', 'I have extensive experience with wheelchair-bound patients and can provide excellent daily care.', 'accepted'),
(16, 1, '2025-11-15', 'I am creative and patient with young children. I can engage your son in painting and building activities he loves.', 'pending'),
(16, 4, '2025-11-19', 'I have experience with multiple children and am energetic enough to keep up with active twins.', 'accepted'),
(17, 3, '2025-11-20', 'I am passionate about soccer and outdoor activities. I can help your son develop his athletic skills while having fun.', 'pending'),
(17, 8, '2025-11-22', 'I am energetic and love creating adventure games for young children. I can keep your son entertained and active.', 'accepted'),
(17, 6, '2025-11-21', 'I enjoy organizing creative play sessions that combine learning and fun for children.', 'pending'),
(18, 2, '2025-11-18', 'I have 7 years of experience in elderly care with a focus on chronic disease management. I am compassionate and detail-oriented.', 'accepted'),
(18, 5, '2025-11-16', 'I have worked extensively with post-surgical patients and understand the importance of gentle, supportive care.', 'accepted'),
(18, 7, '2025-11-17', 'I specialize in dementia care and can provide the patience and understanding your grandmother needs.', 'accepted'),
(18, 10, '2025-11-13', 'I am experienced in all aspects of wheelchair care and can provide comprehensive daily support.', 'pending'),
(19, 4, '2025-11-19', 'I am comfortable with pets and have experience managing multiple children at once.', 'pending'),
(19, 6, '2025-11-21', 'I can support your daughter with homework and encourage her love of reading and drawing.', 'rejected'),
(19, 9, '2025-11-14', 'I am punctual, reliable, and experienced with active school-age boys.', 'pending'),
(20, 3, '2025-11-20', 'I love sports and outdoor play. I can help your son enjoy soccer while building his confidence.', 'accepted'),
(20, 8, '2025-11-22', 'I am enthusiastic about outdoor activities and can create exciting adventures for your active son.', 'accepted'),
(20, 6, '2025-11-21', 'I enjoy combining play with learning and can provide engaging activities for your daughter.', 'pending'),
(20, 1, '2025-11-15', 'I have some experience with younger children and would love to work with your creative son.', 'rejected');

-- Appointment Insert
INSERT INTO APPOINTMENT (caregiver_user_id, member_user_id, appointment_date, appointment_time, work_hours, status, total_cost, notes) VALUES
(11, 1, '2024-11-25', '09:00:00', 6.00, 'confirmed', 15000.00, 'First day trial with painting and building activities'),
(12, 2, '2024-11-26', '08:00:00', 4.00, 'confirmed', 12000.00, 'Morning care including medication reminders and breakfast'),
(13, 3, '2024-11-27', '15:00:00', 3.00, 'confirmed', 6000.00, 'Soccer practice at the park'),
(14, 4, '2024-11-28', '10:00:00', 6.00, 'confirmed', 16800.00, 'Weekend childcare for twins'),
(15, 5, '2024-11-29', '07:00:00', 6.00, 'pending', 19200.00, 'Post-surgery care and mobility assistance'),
(16, 6, '2024-11-30', '14:00:00', 4.00, 'confirmed', 10400.00, 'After-school homework help and creative activities'),
(17, 8, '2024-12-01', '13:00:00', 4.00, 'pending', 8800.00, 'Outdoor playtime and dinosaur adventures'),
(18, 7, '2024-12-02', '16:00:00', 4.00, 'confirmed', 14000.00, 'Evening care for grandmother with dementia'),
(19, 9, '2024-12-03', '15:00:00', 4.00, 'confirmed', 9600.00, 'After-school supervision for twin boys'),
(20, 3, '2024-12-04', '15:00:00', 3.00, 'pending', 6900.00, 'Outdoor sports and play session');


-- Views
-- Active Caregivers All Info
CREATE OR REPLACE VIEW vw_caregiver_profiles AS
SELECT
    u.user_id,
    u.email,
    u.given_name,
    u.surname,
    u.city,
    u.phone_number,
    u.profile_description,
    c.photo,
    c.gender,
    c.caregiving_type,
    c.hourly_rate,
    c.is_active,
    c.rating,
    c.total_reviews
FROM USER u
INNER JOIN CAREGIVER c
ON u.user_id = c.caregiver_user_id
WHERE c.is_active = TRUE;

-- Members All Info
CREATE OR REPLACE VIEW vw_member_profiles AS
SELECT
    u.user_id,
    u.email,
    u.given_name,
    u.surname,
    u.city,
    u.phone_number,
    m.house_rules,
    m.dependent_description,
    addr.house_number,
    addr.street,
    addr.town
FROM USER u
JOIN MEMBER m
ON u.user_id = m.member_user_id
LEFT JOIN ADDRESS addr
ON m.member_user_id = addr.member_user_id;

-- ----------------------------------------------------------------------------
-- View: Open Jobs with Details
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_open_jobs AS
SELECT
    j.job_id,
    j.required_caregiving_type,
    j.date_posted,
    j.dependent_age,
    j.preferred_time_start,
    j.preferred_time_end,
    j.frequency,
    j.duration,
    j.other_requirements,
    u.given_name AS member_name,
    u.surname AS member_surname,
    u.city,
    m.dependent_description,
    (SELECT COUNT(*) FROM JOB_APPLICATION ja WHERE ja.job_id = j.job_id) AS application_count
FROM JOB j
JOIN MEMBER m ON j.member_user_id = m.member_user_id
JOIN USER u ON m.member_user_id = u.user_id
WHERE j.status = 'open';


-- Procedures
-- Create Appointment
DELIMITER //
CREATE PROCEDURE sp_create_appointment(
    IN p_caregiver_id INT,
    IN p_member_id INT,
    IN p_date DATE,
    IN p_time TIME,
    IN p_hours DECIMAL(4,2),
    IN p_notes TEXT,
    OUT p_appointment_id INT,
    OUT p_total_cost DECIMAL(10,2)
)
BEGIN
    DECLARE v_hourly_rate DECIMAL(10,2);

    SELECT hourly_rate INTO v_hourly_rate
    FROM CAREGIVER
    WHERE caregiver_user_id = p_caregiver_id;

    SET p_total_cost = v_hourly_rate * p_hours;

    INSERT INTO APPOINTMENT (
        caregiver_user_id,
        member_user_id,
        appointment_date,
        appointment_time,
        work_hours,
        status,
        total_cost,
        notes
    ) VALUES (
        p_caregiver_id,
        p_member_id,
        p_date,
        p_time,
        p_hours,
        'pending',
        p_total_cost,
        p_notes
    );

    SET p_appointment_id = LAST_INSERT_ID();
END//
DELIMITER ;


-- Triggers
-- Calculate appointment cost before insert
DELIMITER //
CREATE TRIGGER trg_calculate_appointment_cost
BEFORE INSERT ON APPOINTMENT
FOR EACH ROW
BEGIN
    DECLARE temp_hourly_rate DECIMAL(10,2);

    SELECT hourly_rate INTO temp_hourly_rate
    FROM CAREGIVER
    WHERE caregiver_user_id = NEW.caregiver_user_id;

    IF NEW.total_cost IS NULL THEN
        SET NEW.total_cost = temp_hourly_rate * NEW.work_hours;
    END IF;
END//
DELIMITER ;
