CREATE TABLE user (
	id SERIAL PRIMARY KEY,
	username VARCHAR(20) UNIQUE NOT NULL,
	password TEXT NOT NULL,
	refresh_token TEXT NOT NULL,
	user_type INTEGER DEFAULT 1 NOT NULL
)
;

CREATE TABLE user_plate (
	id SERIAL PRIMARY KEY,
	username VARCHAR(20) NOT NULL,
	plate VARCHAR(20) UNIQUE NOT NULL
)
;

CREATE TABLE config (
	id SERIAL PRIMARY KEY,
	name VARCHAR(50) UNIQUE NOT NULL,
	value VARCHAR(50) NOT NULL
)
;

CREATE TABLE history_202311 (
	id SERIAL PRIMARY KEY,
	username VARCHAR(20) NOT NULL,
	plate VARCHAR(20) NOT NULL,
	region VARCHAR(10) NOT NULL,
	type VARCHAR(30) NOT NULL,
	bbox VARCHAR(30) NOT NULL,
	path TEXT NOT NULL,
	create_time TIMESTAMP NOT NULL DEFAULT (now())
)
;

INSERT INTO "user" (username, password, refresh_token, user_type)
VALUES ('admin', '$2b$12$UyHbRPZEmhiwHvzlBRRzteiZM6MBakrONZa8QYcAOX3HMUcI7Kn2C', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwicGFzc3dvcmQiOiJhZG1pbiJ9.5q0UgohNs_wIjB_xiORFhavphXzYfX3yaClnl7Yd2_4', 0)

INSERT INTO "config" (name, value)
VALUES ('roi', '600 200 1270 710');

INSERT INTO "config" (name, value)
VALUES ('obj_size', '30000');

INSERT INTO "config" (name, value)
VALUES ('file', 'video.mp4');