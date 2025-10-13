#!/bin/sh

if [ ! -z "${FACTORYAL_TRUST_CA_PATH}" ]; then
  echo "Trusting CA certificate as requested in ${FACTORYAL_TRUST_CA_PATH}"
  cp "${FACTORYAL_TRUST_CA_PATH}" /usr/local/share/ca-certificates/new-ca.crt
  update-ca-certificates
fi

if [ ! -z "${FACTORYAL_SECOND_TRUST_CA_PATH}" ]; then
  echo "Trusting second CA certificate as requested in ${FACTORYAL_SECOND_TRUST_CA_PATH}"
  cp "${FACTORYAL_SECOND_TRUST_CA_PATH}" /usr/local/share/ca-certificates/new-ca2.crt
  update-ca-certificates
fi

if [ ! -z "${FACTORYAL_UPDATE_CA_CERTIFICATES_ON_BOOT}" ]; then
  update-ca-certificates
fi

echo
python src/corvina_model_manager.py "$@"
