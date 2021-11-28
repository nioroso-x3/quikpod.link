DROP DATABASE quikpod_dev;
CREATE DATABASE quikpod_dev;
GRANT ALL PRIVILEGES ON quikpod_dev.* TO 'quikpod_dev'@'localhost' IDENTIFIED BY 'placeholderpassword';
USE quikpod_dev;
CREATE TABLE jobs (id      INT NOT NULL PRIMARY KEY AUTO_INCREMENT, 
	           address TEXT NOT NULL,
	           action TEXT NOT NULL,
		   status TEXT NOT NULL,
		   result JSON,
		   pid INT,
		   created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
		   updated TIMESTAMP,
	           argv   JSON);
CREATE TABLE pods (id      INT NOT NULL PRIMARY KEY AUTO_INCREMENT, 
                   address TEXT NOT NULL,
                   podid TEXT NOT NULL,
		   name TEXT NOT NULL,
		   img TEXT,
		   ip TEXT,
		   http TEXT,
		   created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                   updated TIMESTAMP,
                   status TEXT NOT NULL);

