DROP TABLE fmi_sim_schemmas;


CREATE TABLE fmi_sim_schemmas (
	id INT GENERATED ALWAYS AS IDENTITY,
	name VARCHAR(256) UNIQUE,
	context VARCHAR(256),
	sim_schemme JSONB
);