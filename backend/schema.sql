-- Физическая модель БД: сгенерировано из SQLAlchemy-моделей


CREATE TABLE article (
	id SERIAL NOT NULL, 
	number VARCHAR(20) NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	version INTEGER NOT NULL, 
	locked_by VARCHAR, 
	locked_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)



CREATE TABLE brand (
	id SERIAL NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	version INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
)



CREATE TABLE color (
	id SERIAL NOT NULL, 
	name VARCHAR(30) NOT NULL, 
	version INTEGER NOT NULL, 
	locked_by VARCHAR, 
	locked_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (name)
)



CREATE TABLE inspector (
	id SERIAL NOT NULL, 
	last_name VARCHAR(50) NOT NULL, 
	first_name VARCHAR(50) NOT NULL, 
	middle_name VARCHAR(50) NOT NULL, 
	department VARCHAR(100) NOT NULL, 
	rank VARCHAR(50) NOT NULL, 
	version INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	updated_at TIMESTAMP WITH TIME ZONE, 
	locked_by VARCHAR, 
	locked_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)



CREATE TABLE owner (
	id SERIAL NOT NULL, 
	last_name VARCHAR(50) NOT NULL, 
	first_name VARCHAR(50) NOT NULL, 
	middle_name VARCHAR(50) NOT NULL, 
	date_of_birth DATE NOT NULL, 
	address VARCHAR(100) NOT NULL, 
	version INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	updated_at TIMESTAMP WITH TIME ZONE, 
	locked_by VARCHAR, 
	locked_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)



CREATE TABLE user_account (
	id SERIAL NOT NULL, 
	username VARCHAR(50) NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (username)
)



CREATE TABLE violation_type (
	id SERIAL NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	version INTEGER NOT NULL, 
	locked_by VARCHAR, 
	locked_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (name)
)



CREATE TABLE model (
	id SERIAL NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	brand_id INTEGER NOT NULL, 
	version INTEGER NOT NULL, 
	locked_by VARCHAR, 
	locked_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(brand_id) REFERENCES brand (id)
)



CREATE TABLE violation (
	id SERIAL NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	violation_type_id INTEGER NOT NULL, 
	article_id INTEGER NOT NULL, 
	version INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	updated_at TIMESTAMP WITH TIME ZONE, 
	locked_by VARCHAR, 
	locked_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(violation_type_id) REFERENCES violation_type (id), 
	FOREIGN KEY(article_id) REFERENCES article (id)
)



CREATE TABLE vehicle (
	id SERIAL NOT NULL, 
	state_number VARCHAR(20) NOT NULL, 
	model_id INTEGER NOT NULL, 
	color_id INTEGER NOT NULL, 
	owner_id INTEGER NOT NULL, 
	version INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	updated_at TIMESTAMP WITH TIME ZONE, 
	locked_by VARCHAR, 
	locked_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (state_number), 
	FOREIGN KEY(model_id) REFERENCES model (id), 
	FOREIGN KEY(color_id) REFERENCES color (id), 
	FOREIGN KEY(owner_id) REFERENCES owner (id)
)



CREATE TABLE protocol (
	id SERIAL NOT NULL, 
	number VARCHAR(20) NOT NULL, 
	issue_date DATE NOT NULL, 
	issue_time TIME WITHOUT TIME ZONE NOT NULL, 
	vehicle_id INTEGER NOT NULL, 
	owner_id INTEGER NOT NULL, 
	inspector_id INTEGER NOT NULL, 
	violation_id INTEGER NOT NULL, 
	version INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	updated_at TIMESTAMP WITH TIME ZONE, 
	locked_by VARCHAR, 
	locked_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (number), 
	FOREIGN KEY(vehicle_id) REFERENCES vehicle (id), 
	FOREIGN KEY(owner_id) REFERENCES owner (id), 
	FOREIGN KEY(inspector_id) REFERENCES inspector (id), 
	FOREIGN KEY(violation_id) REFERENCES violation (id)
)


