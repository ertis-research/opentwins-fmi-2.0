DROP TABLE fmi_sim_schemmas;

-- TODO: Hay que hacer que la clave primaria sea una combinacion entre id, nombre y contexto.

CREATE TABLE fmi_sim_schemmas (
	id VARCHAR(256) PRIMARY KEY,
	name VARCHAR(256) UNIQUE,
	context VARCHAR(256),
	sim_schemme JSONB
);


CREATE TABLE fmi_sim_schemas (
	id VARCHAR(256),
	name VARCHAR(256),
	context VARCHAR(256),
	sim_schemme JSONB
	PRIMARY KEY (id, name, context)
);



select count(*) from fmi_sim_schemmas where context = 'gedera' and (name= 'jose' or id = 112);