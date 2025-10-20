CREATE TABLE users (id INT, name VARCHAR(100), active BOOLEAN);
INSERT INTO users (id, name, active) VALUES (1, 'David', TRUE);
SELECT * FROM users;
SELECT id, name FROM users WHERE active = TRUE;
UPDATE users SET name = 'David Castellanos' WHERE id = 1;
DELETE FROM users WHERE id = 1;
