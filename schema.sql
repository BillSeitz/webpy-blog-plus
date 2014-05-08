CREATE TABLE "entries" (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NULL,
    title TEXT,
    content TEXT,
    posted_on DATETIME
);
CREATE TABLE "users" (
    user_id             INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    user_name          varchar(64) NOT NULL,
    user_password       varchar(255) NOT NULL,
    user_email          varchar(64),
    user_status         varchar(16) NOT NULL DEFAULT 'active',
    user_last_login     datetime NOT NULL, 
    hash_temp           varchar(64) NULL, create_date datetime, update_date datetime, cluster integer);
