CREATE TABLE users (id INT, name VARCHAR(100), active BOOLEAN);
INSERT INTO users (id, name, active) VALUES (1, 'Ana', TRUE);
SELECT * FROM users;
SELECT id, name FROM users WHERE active = TRUE;
UPDATE users SET name = 'Ana Maria' WHERE id = 1;
DELETE FROM users WHERE id = 1;
