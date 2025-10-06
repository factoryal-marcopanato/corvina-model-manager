#!/bin/bash

# https://app.corvina.cloud/svc/mappings/swagger-ui/swagger.json

rm -fr corvina_api/generated_files/

docker run \
  --rm \
  -it \
  -v "$(pwd):/local" \
  openapitools/openapi-generator-cli:v7.16.0 \
  generate \
  -i /local/corvina_api/swagger_20251006_fixed.json \
  -g python \
  -o /local/corvina_api/generated_files \
  --additional-properties=generateSourceCodeOnly=True,library=asyncio,packageName=corvina_mapping_api

touch corvina_api/generated_files/__init__.py
echo "Fixing import paths in generated code"
find corvina_api/generated_files/corvina_mapping_api/ -type f -name "*.py" -exec sed -i 's/from\ corvina_mapping_api\./from\ \.\./' {} +
find corvina_api/generated_files/corvina_mapping_api/models/ -type f -name "*.py" -exec sed -i 's/from\ corvina_mapping_api/from\ \.\./' {} +

sed -i 's/\.\./\./' corvina_api/generated_files/corvina_mapping_api/api_client.py
sed -i 's/corvina_mapping_api\.models/resources\.corvina_api\.generated_files\.corvina_mapping_api\.models/' corvina_api/generated_files/corvina_mapping_api/api_client.py
sed -i 's/from\ corvina_mapping_api\ import\ rest/import\ resources\.corvina_api\.generated_files\.corvina_mapping_api\.rest\ as\ rest/' corvina_api/generated_files/corvina_mapping_api/api_client.py
sed -i 's/from\ dateutil\.parser\ import\ parse/# from\ dateutil\.parser\ import\ parse/' corvina_api/generated_files/corvina_mapping_api/api_client.py
sed -i 's/return\ parse(string)/return\ datetime\.datetime\.fromisoformat\(string\)/' corvina_api/generated_files/corvina_mapping_api/api_client.py

sed -i 's/\.\./\./' corvina_api/generated_files/corvina_mapping_api/__init__.py

# sed -i 's/if\ not\ re\.match/#\ if\ not\ re\.match/' corvina_api/generated_files/corvina_mapping_api/models/model_in_dto.py
# sed -i 's/",\ value/#\ ",\ value/' corvina_api/generated_files/corvina_mapping_api/models/model_in_dto.py
# sed -i 's/raise\ ValueError/#\ raise\ ValueError/' corvina_api/generated_files/corvina_mapping_api/models/model_in_dto.py
# sed -i 's/\/")/# \/"\)/' corvina_api/generated_files/corvina_mapping_api/models/model_in_dto.py

sed -i 's/from\ ..exceptions/from\ \.exceptions/' corvina_api/generated_files/corvina_mapping_api/rest.py
