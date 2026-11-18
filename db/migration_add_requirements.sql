-- Migration: add a JSON `requirements` column to jobs (list of required skills)
-- and seed it for the existing job postings.
-- Safe to re-run: the column is only added if it does not already exist,
-- and seed UPDATEs only touch rows whose requirements are still NULL.

USE job_tracker;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = 'job_tracker' AND TABLE_NAME = 'jobs' AND COLUMN_NAME = 'requirements'
);
SET @ddl := IF(@col_exists = 0,
    'ALTER TABLE jobs ADD COLUMN requirements JSON NULL AFTER job_description',
    'SELECT ''requirements column already exists''');
PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Seed skills for the sample jobs (only where not yet set)
UPDATE jobs SET requirements = JSON_ARRAY('Python', 'JavaScript', 'SQL', 'Git', 'REST APIs')                 WHERE job_id = 1  AND requirements IS NULL;
UPDATE jobs SET requirements = JSON_ARRAY('SQL', 'MySQL', 'PostgreSQL', 'Backup & Recovery', 'Linux')      WHERE job_id = 2  AND requirements IS NULL;
UPDATE jobs SET requirements = JSON_ARRAY('SQL', 'Excel', 'Python', 'Tableau', 'Statistics')               WHERE job_id = 3  AND requirements IS NULL;
UPDATE jobs SET requirements = JSON_ARRAY('AWS', 'Docker', 'Kubernetes', 'Terraform', 'Linux', 'Python')   WHERE job_id = 4  AND requirements IS NULL;
UPDATE jobs SET requirements = JSON_ARRAY('JavaScript', 'HTML', 'CSS', 'Git')                              WHERE job_id = 5  AND requirements IS NULL;
UPDATE jobs SET requirements = JSON_ARRAY('Java', 'Python', 'System Design', 'SQL', 'AWS', 'Leadership')   WHERE job_id = 6  AND requirements IS NULL;
UPDATE jobs SET requirements = JSON_ARRAY('Python', 'Machine Learning', 'TensorFlow', 'PyTorch', 'SQL')    WHERE job_id = 7  AND requirements IS NULL;
UPDATE jobs SET requirements = JSON_ARRAY('Selenium', 'Python', 'Test Automation', 'SQL', 'Git')           WHERE job_id = 8  AND requirements IS NULL;
UPDATE jobs SET requirements = JSON_ARRAY('Excel', 'SQL', 'Requirements Gathering', 'Communication')       WHERE job_id = 9  AND requirements IS NULL;
UPDATE jobs SET requirements = JSON_ARRAY('Python', 'Machine Learning', 'Statistics', 'SQL', 'Pandas')     WHERE job_id = 10 AND requirements IS NULL;
UPDATE jobs SET requirements = JSON_ARRAY('Docker', 'Kubernetes', 'CI/CD', 'AWS', 'Linux', 'Git')          WHERE job_id = 11 AND requirements IS NULL;
UPDATE jobs SET requirements = JSON_ARRAY('Network Security', 'Linux', 'Python', 'SIEM')                   WHERE job_id = 12 AND requirements IS NULL;
UPDATE jobs SET requirements = JSON_ARRAY('Figma', 'HTML', 'CSS', 'User Research')                         WHERE job_id = 13 AND requirements IS NULL;
UPDATE jobs SET requirements = JSON_ARRAY('Agile', 'Communication', 'Leadership', 'SQL', 'Jira')           WHERE job_id = 14 AND requirements IS NULL;
UPDATE jobs SET requirements = JSON_ARRAY('Technical Writing', 'Markdown', 'Git', 'Communication')         WHERE job_id = 15 AND requirements IS NULL;
UPDATE jobs SET requirements = JSON_ARRAY('Python', 'SQL', 'Excel')                                        WHERE job_id = 16 AND requirements IS NULL;
UPDATE jobs SET requirements = JSON_ARRAY('JavaScript', 'Python', 'Git')                                   WHERE job_id = 17 AND requirements IS NULL;
UPDATE jobs SET requirements = JSON_ARRAY('System Design', 'Java', 'AWS', 'Microservices', 'Leadership')   WHERE job_id = 18 AND requirements IS NULL;

SELECT job_id, job_title, requirements FROM jobs ORDER BY job_id;
