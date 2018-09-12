CREATE DATABASE myDB;
USE myDB;
DROP TABLE users;
CREATE TABLE users (
    id int NOT NULL AUTO_INCREMENT,
    first_name varchar(255),
    last_name varchar(255),
	email varchar(255),
    password varchar(255),
    created_at datetime,
    updated_at datetime,
    PRIMARY KEY (id)
);

CREATE TABLE messages (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT,
	message varchar(255),
    sender_id INT,
    created_at datetime,
    updated_at datetime,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

INSERT into messages (user_id, message, sender_id, created_at, updated_at)
VALUES (2, "Hello again Jim, it's jeff the weirdo!", 5, now(), now());

SELECT * FROM messages;

SELECT messages.user_id, messages.message, messages.created_at, CONCAT(users.first_name, " ", users.last_name) AS sender_name
FROM messages 
JOIN users ON messages.sender_id = users.id
WHERE user_id = 2;

SELECT messages.user_id, messages.message, messages.created_at, CONCAT(users.first_name, " ", users.last_name) AS sender_name FROM messages JOIN users ON messages.sender_id = users.id WHERE user_id = "2";

INSERT INTO messages (user_id, message, sender_id, created_at, updated_at) VALUES (2, "Yo stupid",  6, now(), now());


SELECT * FROM messages;

DELETE FROM messages WHERE id = 2;

DELETE FROM users
WHERE id = 3;
SELECT users.email FROM users;

DROP TABLE messages;
