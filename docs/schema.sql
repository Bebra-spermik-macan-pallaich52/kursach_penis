
CREATE TABLE users (
	id SERIAL NOT NULL, 
	username VARCHAR(50) NOT NULL, 
	password_hash VARCHAR(256) NOT NULL, 
	full_name VARCHAR(150) NOT NULL, 
	birth_date DATE, 
	email VARCHAR(254) NOT NULL, 
	institution VARCHAR(200) NOT NULL, 
	education_level VARCHAR(100) NOT NULL, 
	course INTEGER, 
	specialty VARCHAR(150) NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	token_version INTEGER NOT NULL, 
	created_by INTEGER, 
	PRIMARY KEY (id), 
	UNIQUE (username), 
	UNIQUE (email), 
	FOREIGN KEY(created_by) REFERENCES users (id)
)

;


CREATE TABLE olympiads (
	id SERIAL NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	description TEXT NOT NULL, 
	teacher_id INTEGER NOT NULL, 
	start_date DATE NOT NULL, 
	end_date DATE NOT NULL, 
	protocol_status VARCHAR(20) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT dates_order CHECK (end_date >= start_date), 
	FOREIGN KEY(teacher_id) REFERENCES users (id)
)

;


CREATE TABLE attachments (
	id SERIAL NOT NULL, 
	olympiad_id INTEGER NOT NULL, 
	kind VARCHAR(20) NOT NULL, 
	title VARCHAR(150) NOT NULL, 
	original_name VARCHAR(200) NOT NULL, 
	stored_name VARCHAR(100) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(olympiad_id) REFERENCES olympiads (id)
)

;


CREATE TABLE participations (
	id SERIAL NOT NULL, 
	olympiad_id INTEGER NOT NULL, 
	student_id INTEGER NOT NULL, 
	score NUMERIC(8, 2), 
	result VARCHAR(20), 
	PRIMARY KEY (id), 
	CONSTRAINT unique_enrollment UNIQUE (olympiad_id, student_id), 
	CONSTRAINT nonnegative_score CHECK (score >= 0), 
	FOREIGN KEY(olympiad_id) REFERENCES olympiads (id), 
	FOREIGN KEY(student_id) REFERENCES users (id)
)

;