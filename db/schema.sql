-- Full schema for the Job Tracker application (MySQL 8.0+).
-- Mirrors the live `job_tracker` database after migration_add_requirements.sql.
-- Used by the test suite to build an isolated `job_tracker_test` database.

CREATE TABLE IF NOT EXISTS companies (
    company_id   INT NOT NULL AUTO_INCREMENT,
    company_name VARCHAR(100) NOT NULL,
    industry     VARCHAR(50)  DEFAULT NULL,
    website      VARCHAR(200) DEFAULT NULL,
    city         VARCHAR(50)  DEFAULT NULL,
    state        VARCHAR(50)  DEFAULT NULL,
    notes        TEXT,
    created_at   TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (company_id),
    KEY idx_company_industry (industry)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS jobs (
    job_id          INT NOT NULL AUTO_INCREMENT,
    company_id      INT NOT NULL,
    job_title       VARCHAR(100) NOT NULL,
    job_description TEXT,
    requirements    JSON NULL,              -- JSON array of required skills
    salary_min      DECIMAL(10,2) DEFAULT NULL,
    salary_max      DECIMAL(10,2) DEFAULT NULL,
    job_type        VARCHAR(20)  DEFAULT NULL,
    posting_url     VARCHAR(500) DEFAULT NULL,
    date_posted     DATE DEFAULT NULL,
    is_active       TINYINT(1) DEFAULT 1,
    created_at      TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (job_id),
    KEY idx_job_title (job_title),
    KEY idx_salary (salary_min),
    KEY idx_company_type (company_id, job_type),
    CONSTRAINT jobs_ibfk_1 FOREIGN KEY (company_id) REFERENCES companies (company_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS applications (
    application_id    INT NOT NULL AUTO_INCREMENT,
    job_id            INT NOT NULL,
    application_date  DATE NOT NULL,
    status            VARCHAR(30) DEFAULT 'Applied',
    resume_version    VARCHAR(50) DEFAULT NULL,
    cover_letter_sent TINYINT(1) DEFAULT 0,
    response_date     DATE DEFAULT NULL,
    interview_date    DATETIME DEFAULT NULL,
    notes             TEXT,
    created_at        TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (application_id),
    KEY job_id (job_id),
    KEY idx_app_status (status),
    CONSTRAINT applications_ibfk_1 FOREIGN KEY (job_id) REFERENCES jobs (job_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS contacts (
    contact_id   INT NOT NULL AUTO_INCREMENT,
    company_id   INT NOT NULL,
    first_name   VARCHAR(50) NOT NULL,
    last_name    VARCHAR(50) NOT NULL,
    email        VARCHAR(100) DEFAULT NULL,
    phone        VARCHAR(20)  DEFAULT NULL,
    job_title    VARCHAR(100) DEFAULT NULL,
    linkedin_url VARCHAR(200) DEFAULT NULL,
    notes        TEXT,
    created_at   TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (contact_id),
    KEY company_id (company_id),
    CONSTRAINT contacts_ibfk_1 FOREIGN KEY (company_id) REFERENCES companies (company_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
