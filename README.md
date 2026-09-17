# opentwins-fmi-2.0

Motor de simulación de modelos **FMI/FMU** para [OpenTwins](https://github.com/ertis-research/opentwins), desplegado sobre Kubernetes. Permite subir FMUs, definir esquemas de simulación (uno o varios FMUs conectados entre sí) y lanzar simulaciones puntuales o programadas, cuyos resultados se publican en un broker de mensajería.

## Índice

- [Arquitectura](#arquitectura)
- [Flujo de uso](#flujo-de-uso)
- [Funcionalidades](#funcionalidades)
  - [Gestión de FMUs](#gestión-de-fmus)
  - [Gestión de esquemas de simulación](#gestión-de-esquemas-de-simulación)
  - [Gestión de simulaciones](#gestión-de-simulaciones)
  - [Motor de simulación](#motor-de-simulación)
- [API REST](#api-rest)
- [Puesta en marcha](#puesta-en-marcha)
  - [Requisitos previos](#requisitos-previos)
  - [Variables de entorno](#variables-de-entorno)
  - [Despliegue en Kubernetes](#despliegue-en-kubernetes)
  - [Ejecución local (desarrollo)](#ejecución-local-desarrollo)
- [Limitaciones conocidas](#limitaciones-conocidas)

## Arquitectura

El proyecto tiene tres componentes independientes, cada uno con su propio `Dockerfile` y `requirements.txt`:

| Componente | Qué es | Cómo se ejecuta |
|---|---|---|
| [`API controller/`](API%20controller) | API REST (FastAPI) que expone toda la funcionalidad y orquesta el resto | Deployment permanente en Kubernetes ([kubernetes/deployent.yaml](kubernetes/deployent.yaml)) |
| [`Single FMU executer/`](Single%20FMU%20executer) | Motor que simula **un único FMU** con [FMPy](https://github.com/CATIA-Systems/FMPy) | Lanzado bajo demanda por la API como Job/CronJob de Kubernetes |
| [`Multiple FMU executer/`](Multiple%20FMU%20executer) | Motor que simula **varios FMUs conectados** entre sí (formato SSP/SSD) | Lanzado bajo demanda por la API como Job/CronJob de Kubernetes |

La API nunca ejecuta la simulación ella misma: al desplegar una simulación crea un `Job` (ejecución puntual) o `CronJob` (ejecución programada) de Kubernetes con la imagen `...-single-v2` o `...-multiple-v2` según el esquema tenga 1 o varios FMUs. Ese contenedor recibe toda la configuración por variables de entorno, simula y termina.

Servicios externos de los que depende el sistema:

- **MinIO** (S3): almacena los ficheros `.fmu`, su `modelDescription.xml` extraído, y los `.ssd` (SystemStructureDescription) generados para simulaciones multi-FMU. Un *bucket* por `context` (namespace lógico, normalmente el *tenant*/gemelo digital).
- **InfluxDB**: fuente opcional de valores iniciales para variables de un FMU.
- **Broker MQTT**: destino de los resultados de cada simulación, y fuente opcional de valores iniciales.
- **Kubernetes API**: para crear/listar/borrar los `Job`/`CronJob` de cada simulación.

Los esquemas de simulación se guardan en una base de datos **SQLite embebida en la propia API** (fichero local, sin servicio externo) — ver [Requisitos previos](#requisitos-previos).

## Flujo de uso

1. Subir uno o varios FMUs (`POST /fmi/fmus/{context}`).
2. (Solo si la simulación usa más de un FMU) crear un **esquema** que declare los FMUs implicados y cómo se conectan sus variables entre sí (`POST /fmi/schemas/{context}`).
3. Desplegar una simulación referenciando ese esquema, indicando tiempos de simulación y de dónde sacar el valor inicial de cada variable de entrada (`POST /fmi/simulations/{context}`).
4. La API decide, según el nº de FMUs del esquema, si crear un `Job` (ejecución única) o `CronJob` (programada) con la imagen del executer adecuado.
5. El executer descarga el/los FMU desde MinIO, resuelve los valores iniciales, simula y publica los resultados por MQTT.
6. Consultar el estado de las simulaciones en marcha, pausarlas/reanudarlas (solo las programadas) o borrarlas.

## Funcionalidades

### Gestión de FMUs

- **Subir un FMU**: se sube el fichero `.fmu` tal cual (un FMU ya es un `.zip`). El backend extrae `modelDescription.xml` de dentro y guarda tanto el `.fmu` como el `.xml` en el bucket de MinIO correspondiente al `context`.
- **Listar FMUs de un contexto**: parsea el `modelDescription.xml` de cada FMU subido y devuelve sus variables clasificadas en `inputs`, `outputs` y `other_variables` (parámetros con valor inicial fijo, `initial="exact"`).
- **Obtener la descripción de un FMU**: devuelve el `modelDescription.xml` crudo.
- **Borrar un FMU**: elimina el `.fmu` y el `.xml` de MinIO.

### Gestión de esquemas de simulación

Un *esquema* describe qué FMUs participan en una simulación y, si son varios, cómo se conectan sus variables entre sí (equivalente a un SSP `SystemStructureDescription`).

- **Crear esquema**: se guarda en la base de datos SQLite de la API. Si incluye el campo `schema` (las conexiones), además se genera un `.ssd` (XML) y se sube a MinIO (solo hace falta para simulaciones de más de un FMU).
- **Listar esquemas de un contexto.**
- **Obtener un esquema** (404 si no existe).
- **Borrar un esquema** (borra la fila de SQLite y el `.ssd` de MinIO; 404 si no existe).

### Gestión de simulaciones

- **Desplegar una simulación**: crea el `Job`/`CronJob` en Kubernetes. Rechaza la petición con 409 si ya existe una simulación con ese `id` en ese `context`.
- **Listar simulaciones en marcha** de un contexto (o de todos): para cada `Job`/`CronJob` propio (identificados por las labels `opentwins.fmi/*`) devuelve su estado y el de sus pods.
- **Consultar el detalle** de una simulación concreta (manifiesto completo del `Job`/`CronJob`).
- **Borrar** una simulación (Job o CronJob, según corresponda).
- **Pausar / reanudar** una simulación (solo aplicable a las programadas (`CronJob`); en una `Job` puntual devuelve error).

### Motor de simulación

Al arrancar, el executer (single o multiple):

1. Descarga el/los FMU (y el `.ssd` si es multi-FMU) desde MinIO.
2. Para cada variable de entrada declarada en la petición de despliegue, resuelve su valor según su `type`:
   - **`fixed`**: usa el `value` indicado literalmente.
   - **`influxdb`**: ejecuta la `query` (Flux) indicada y toma el único resultado devuelto (falla si no hay exactamente uno).
   - **`mqtt`**: se suscribe al `topic` indicado y espera hasta 10s el primer mensaje; el valor se extrae del JSON del mensaje siguiendo `mapper`, una ruta separada por puntos (p. ej. `"data.temperature"` para `{"data": {"temperature": 21.5}}`).
   - **`default`**: no se fija ningún valor; se usa el que traiga el propio FMU.
3. Simula:
   - **Single FMU executer**: usa `fmpy.simulate_fmu`, aplicando esos valores como *start values* (parámetros iniciales) del FMU.
   - **Multiple FMU executer**: motor de co-simulación paso a paso propio ([`utils/simulation.py`](Multiple%20FMU%20executer/utils/simulation.py)), que instancia cada FMU, resuelve las conexiones internas declaradas en el esquema y mantiene esos valores como entradas constantes de sistema durante toda la simulación.
4. Si `SIMULATION_LAST_VALUE` es `true`, se descarta toda la serie temporal y solo se conserva el último instante; si no, se conserva la serie completa.
5. Publica el resultado en el broker de mensajería configurado: un mensaje JSON por fila (instante simulado, o solo el último), con `SIMULATION_ID` y `SIMULATION_NAME` añadidos a cada mensaje.

**Identificadores de las entradas (`inputs[].id`):**
- En una simulación de **un solo FMU**, `id` es el nombre de la variable tal cual aparece en el `modelDescription.xml` del FMU.
- En una simulación **multi-FMU**, `id` es el nombre del **conector de sistema** declarado en el esquema (el `var` del extremo de una conexión que no lleva `id`, ver ejemplo más abajo).

## API REST

Prefijo común: `/fmi`. La API expone documentación interactiva en `/docs` (Swagger UI) y `/redoc`.

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/fmi/fmus/{context}` | Sube un FMU (`multipart/form-data`, campo `file`) |
| `GET` | `/fmi/fmus/{context}` | Lista los FMUs del contexto con sus variables |
| `GET` | `/fmi/fmus/{context}/{fmuName}` | Descripción XML (`modelDescription.xml`) de un FMU |
| `DELETE` | `/fmi/fmus/{context}/{fmuName}` | Borra un FMU |
| `POST` | `/fmi/schemas/{context}` | Crea un esquema de simulación |
| `GET` | `/fmi/schemas/{context}` | Lista los esquemas del contexto |
| `GET` | `/fmi/schemas/{context}/{schema_id}` | Obtiene un esquema |
| `DELETE` | `/fmi/schemas/{context}/{schema_id}` | Borra un esquema |
| `POST` | `/fmi/simulations/{context}` | Despliega una simulación (Job o CronJob) |
| `GET` | `/fmi/simulations/{context}` | Lista simulaciones en marcha del contexto |
| `GET` | `/fmi/simulations/{context}/{simulation_id}` | Detalle de una simulación |
| `DELETE` | `/fmi/simulations/{context}/{simulation_id}` | Borra una simulación |
| `POST` | `/fmi/simulations/{context}/{simulation_id}/pause` | Pausa una simulación programada |
| `POST` | `/fmi/simulations/{context}/{simulation_id}/resume` | Reanuda una simulación programada |

Hay una colección de Postman lista para usar en [`Postman Collection.json`](Postman%20Collection.json) con un ejemplo de cada endpoint.

### Ejemplo: crear un esquema multi-FMU

```json
POST /fmi/schemas/opentwins
{
  "id": "schema1",
  "name": "Schema 1",
  "description": "Controlador + motor",
  "fmus": [
    {
      "id": "Controller",
      "inputs": [{"id": "u_s"}, {"id": "u_m"}],
      "outputs": [{"id": "y"}]
    },
    {
      "id": "Drivetrain",
      "inputs": [{"id": "tau"}],
      "outputs": [{"id": "w"}]
    }
  ],
  "schema": [
    { "from": {"var": "w_ref"},                    "to": {"id": "Controller",  "var": "u_s"} },
    { "from": {"id": "Drivetrain", "var": "w"},     "to": {"id": "Controller",  "var": "u_m"} },
    { "from": {"id": "Controller", "var": "y"},     "to": {"id": "Drivetrain", "var": "tau"} },
    { "from": {"id": "Drivetrain", "var": "w"},     "to": {"var": "w"} }
  ]
}
```

`schema` es la lista de conexiones. Cada conexión une un `from` con un `to`; si un extremo no lleva `id`, es un conector público del sistema completo (entrada si actúa como `from`, salida si actúa como `to`). En el ejemplo, `w_ref` es una entrada de sistema y `w` una salida de sistema. `schema` es opcional: si la simulación usa un único FMU no hace falta declararlo.

### Ejemplo: desplegar una simulación

```json
POST /fmi/simulations/opentwins
{
  "id": "pruebabouncingball",
  "name": "Mi ejecución",
  "schemaId": "schema1",
  "targetConnection": {
    "BROKER_TYPE": "mqtt",
    "BROKER_IP": "mqtt.mi-cluster.local",
    "BROKER_PORT": "1883",
    "BROKER_TOPIC": "opentwins/fmi-simulations",
    "BROKER_USERNAME": "user",
    "BROKER_PASSWORD": "password"
  },
  "configuration": {
    "SIMULATION_START_TIME": 0,
    "SIMULATION_END_TIME": 7,
    "SIMULATION_STEP_SIZE": 1,
    "SIMULATION_DELAY_WARNING": 1,
    "SIMULATION_LAST_VALUE": true,
    "SIMULATION_TYPESCHEDULE": "one-time"
  },
  "inputs": [
    { "id": "w_ref", "type": "fixed",    "value": 10 },
    { "id": "u_m",   "type": "influxdb", "query": "from(bucket:\"twins\") |> range(start:-5m) |> ..." },
    { "id": "tau",   "type": "mqtt",     "topic": "twin/sensor", "mapper": "data.torque" }
  ],
  "outputs": [
    { "id": "w" }
  ]
}
```

- `targetConnection` es opcional: si se omite, la simulación publica sus resultados en el broker por defecto configurado en la API (`BROKER_*`).
- `SIMULATION_TYPESCHEDULE`: `"one-time"` crea un `Job`; cualquier otro valor se interpreta como una expresión *cron* y crea un `CronJob` con ese `schedule`.

## Puesta en marcha

### Requisitos previos

- Un clúster de Kubernetes accesible. El manifiesto [`kubernetes/deployent.yaml`](kubernetes/deployent.yaml) referencia un `ServiceAccount` llamado `ot-fmi`, con permisos para crear/listar/borrar/pausar `Job` y `CronJob` y listar `Pod` en el namespace usado; ese `ServiceAccount` y su `Role`/`RoleBinding` están definidos en [`kubernetes/rbac.yaml`](kubernetes/rbac.yaml).
- MinIO (u otro backend S3 compatible).
- No hace falta ninguna base de datos externa para los esquemas: la API usa una SQLite embebida y crea la tabla sola al arrancar (ver [`main.py`](API%20controller/main.py)). El fichero se guarda en `SQLITE_DB_PATH`; en Kubernetes, [`kubernetes/deployent.yaml`](kubernetes/deployent.yaml) ya monta un `PersistentVolumeClaim` (`opentwins-fmi-api-data`) en `/usr/src/app/data` y apunta `SQLITE_DB_PATH` ahí, para que los esquemas sobrevivan a un reinicio del pod. Si tu cluster no tiene un `StorageClass` por defecto, indícalo en la `PersistentVolumeClaim` del manifiesto.
- InfluxDB, si vas a usar inputs de tipo `influxdb`.
- Un broker MQTT, para publicar resultados (y para inputs de tipo `mqtt`).
- Docker y acceso a un registry de contenedores, para construir y publicar las 3 imágenes.

### Variables de entorno

**API controller** (ver [`dependencies.py`](API%20controller/dependencies.py) y [`kubernetes_controller.py`](API%20controller/service/kubernetes_controller.py)):

| Variable | Descripción |
|---|---|
| `KUBE_NAMESPACE` | Namespace de Kubernetes donde se crean los `Job`/`CronJob` |
| `INSIDE_CLUSTER` | `true`/`false`. `true` usa la configuración *in-cluster* (vía el `ServiceAccount` del pod); `false` usa `KUBE_HOST` + `TOKEN_KUBERNETES` (útil en desarrollo local contra un clúster remoto) |
| `KUBE_HOST`, `TOKEN_KUBERNETES` | Solo si `INSIDE_CLUSTER=false` |
| `MINIO_URL`, `MINIO_A_KEY`, `MINIO_S_KEY` | Endpoint y credenciales de MinIO |
| `SQLITE_DB_PATH` (opcional) | Ruta del fichero SQLite donde se guardan los esquemas de simulación. Por defecto `fmi_schemas.db` en el directorio de trabajo; en [`kubernetes/deployent.yaml`](kubernetes/deployent.yaml) apunta al `PersistentVolumeClaim` montado |
| `INFLUXDB_HOST`, `INFLUXDB_TOKEN`, `INFLUXDB_DB` | Valores por defecto que se inyectan a los executers desplegados |
| `BROKER_TYPE`, `BROKER_IP`, `BROKER_PORT` (opcional), `BROKER_TOPIC`, `BROKER_USERNAME`, `BROKER_PASSWORD` | Broker por defecto para publicar resultados, si la simulación no indica su propio `targetConnection` |

**Single / Multiple FMU executer**: no hace falta configurarlas a mano, la API las genera automáticamente al desplegar cada simulación (`SIMULATION_ID`, `SIMULATION_INPUTS`, `SIMULATION_FMUS`, las `BROKER_*`, `MINIO_*`, `INFLUXDB_*`, etc.). Solo son relevantes si quieres lanzar `single.py`/`multiple.py` sueltos para depurar (ver más abajo).

### Despliegue en Kubernetes

1. Construir y subir las imágenes de los executers:
   ```bash
   ./rebuild_images.sh
   ```
   Publica las imágenes en `docker.ertis.uma.es/fmi-release/opentwins-fmu-runner-single-v2` y `.../opentwins-fmu-runner-multiple-v2`; ajusta el registry en `rebuild_images.sh` (y en las referencias hardcodeadas a esas dos imágenes en [`kubernetes_controller.py`](API%20controller/service/kubernetes_controller.py)) si usas uno distinto. **Este script no construye la imagen de la API** — hay que hacerlo aparte:
   ```bash
   docker build -t docker.ertis.uma.es/fmi-release/opentwins-fmi-simulator-api-v2 "API controller/"
   docker push docker.ertis.uma.es/fmi-release/opentwins-fmi-simulator-api-v2
   ```
2. Editar [`kubernetes/deployent.yaml`](kubernetes/deployent.yaml): apuntar `image` a tu registry si usas uno distinto, descomentar el bloque `env` y rellenar cada variable (ver tabla anterior).
3. Desplegar:
   ```bash
   kubectl apply -f kubernetes/rbac.yaml
   kubectl apply -f kubernetes/deployent.yaml
   kubectl apply -f kubernetes/service.yaml
   ```
5. La API queda accesible en el `NodePort 30480` (puerto interno `8000`, ver [`kubernetes/service.yaml`](kubernetes/service.yaml)).

### Ejecución local (desarrollo)

**API controller**:
```bash
cd "API controller"
pip install -r requirements.txt
pip install python-multipart   # el Dockerfile lo instala aparte, no está en requirements.txt
# definir las variables de entorno de la tabla anterior (p.ej. con un .env + tu gestor de entorno)
./run.sh      # o run.bat en Windows
```
Sirve en `http://localhost:8000`, con Swagger en `http://localhost:8000/docs`. Aunque se ejecute en local, `deploy_simulation` necesita igualmente acceso a un clúster real (usa `INSIDE_CLUSTER=false` + `KUBE_HOST` + `TOKEN_KUBERNETES` para apuntar a uno remoto).

**Executers**: normalmente no se ejecutan a mano, los lanza la API. Para depurar uno suelto, hay que definir manualmente todas las `SIMULATION_*`/`MINIO_*`/`BROKER_*`/`INFLUXDB_*` que la API generaría (ver [`kubernetes_controller.py`](API%20controller/service/kubernetes_controller.py), método `deploy_simulation`) y luego:
```bash
cd "Single FMU executer"    # o "Multiple FMU executer"
pip install -r requirements.txt
python single.py            # o multiple.py
```

## Limitaciones conocidas

- Las transformaciones de conexión `Boolean`/`Integer`/`Enumeration` del estándar SSP (más allá de `LinearTransformation`) no están implementadas ([`utils/ssd.py`](Multiple%20FMU%20executer/utils/ssd.py)).
- No hay script de migración de base de datos incluido en el repo (ver [Requisitos previos](#requisitos-previos)).
- El input tipo `mqtt` espera un único mensaje tras suscribirse (con timeout de 10s); no soporta acumular/promediar varios mensajes ni una suscripción persistente.
