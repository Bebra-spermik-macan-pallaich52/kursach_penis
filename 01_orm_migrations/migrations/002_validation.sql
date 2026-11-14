ALTER TABLE users ADD CONSTRAINT valid_role CHECK (role IN ('admin', 'teacher', 'student'));
ALTER TABLE users ADD CONSTRAINT valid_course CHECK (course BETWEEN 1 AND 6);
ALTER TABLE olympiads ADD CONSTRAINT valid_status CHECK (protocol_status IN ('draft', 'prepared', 'published'));
ALTER TABLE participations ADD CONSTRAINT valid_result CHECK (result IN ('winner', 'prize', 'participant'));
ALTER TABLE participations ADD CONSTRAINT maximum_score CHECK (score <= 999999.99);
ALTER TABLE attachments ADD CONSTRAINT valid_kind CHECK (kind IN ('regulation', 'task', 'certificate', 'award'));
