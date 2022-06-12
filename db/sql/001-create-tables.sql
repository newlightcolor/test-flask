---- drop ----
DROP TABLE IF EXISTS `test_table`;

---- create ----
create table IF not exists `test_table`
(
 `id`               INT(20) AUTO_INCREMENT,
 `name`             VARCHAR(20) NOT NULL,
 `created_at`       Datetime DEFAULT NULL,
 `updated_at`       Datetime DEFAULT NULL,
    PRIMARY KEY (`id`)
) DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE user (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(30) NOT NULL,
    age INT,
    PRIMARY KEY (id)
);

INSERT INTO user (name, age) VALUES ("太郎", 15);
INSERT INTO user (name, age) VALUES ("次郎", 18);
INSERT INTO user (name, age) VALUES ("花子", 20);