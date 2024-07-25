DROP TABLE fmi_sim_schemmas;


CREATE TABLE fmi_sim_schemmas (
	id VARCHAR(256) PRIMARY KEY,
	name VARCHAR(256) UNIQUE,
	context VARCHAR(256),
	sim_schemme JSONB
);


select count(*) from fmi_sim_schemmas where context = 'gedera' and (name= 'jose' or id = 112);