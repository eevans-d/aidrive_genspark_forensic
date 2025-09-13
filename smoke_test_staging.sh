#!/bin/bash
# Smoke test de endpoints críticos en Staging
# Ampliado para robustez y detección de edge cases

# Reemplazar con el token JWT obtenido en login
JWT_TOKEN="<COPIA_AQUI_TU_TOKEN>"

# URLs
DEPOSITO_URL="http://localhost:8001"
NEGOCIO_URL="http://localhost:8002"
ML_URL="http://localhost:8003"

# Test sin autenticación
for url in "$DEPOSITO_URL/productos" "$NEGOCIO_URL/health" "$ML_URL/models"; do
  echo "Testing $url SIN TOKEN (debe dar 401):"
  curl -s -o /dev/null -w "Status: %{http_code}\n" "$url"
done

# Test con autenticación
for url in "$DEPOSITO_URL/productos" "$NEGOCIO_URL/health" "$ML_URL/models"; do
  echo "Testing $url CON TOKEN (debe dar 200):"
  curl -s -o /dev/null -w "Status: %{http_code}\n" -H "Authorization: Bearer $JWT_TOKEN" "$url"
done

# Test con token inválido
for url in "$DEPOSITO_URL/productos" "$NEGOCIO_URL/health" "$ML_URL/models"; do
  echo "Testing $url con TOKEN INVÁLIDO (debe dar 401):"
  curl -s -o /dev/null -w "Status: %{http_code}\n" -H "Authorization: Bearer INVALIDTOKEN" "$url"
done

# Test con token expirado (simulado)
for url in "$DEPOSITO_URL/productos" "$NEGOCIO_URL/health" "$ML_URL/models"; do
  echo "Testing $url con TOKEN EXPIRADO (debe dar 401):"
  curl -s -o /dev/null -w "Status: %{http_code}\n" -H "Authorization: Bearer EXPIREDTOKEN" "$url"
done

# Test edge cases: parámetros extremos
echo "Testing parámetros extremos en /productos (Depósito):"
curl -s -o /dev/null -w "Status: %{http_code}\n" "$DEPOSITO_URL/productos?nombre=$(printf 'A%.0s' {1..256})" -H "Authorization: Bearer $JWT_TOKEN"
curl -s -o /dev/null -w "Status: %{http_code}\n" "$DEPOSITO_URL/productos?nombre="" -H "Authorization: Bearer $JWT_TOKEN"
curl -s -o /dev/null -w "Status: %{http_code}\n" "$DEPOSITO_URL/productos?nombre=<script>alert('xss')</script>" -H "Authorization: Bearer $JWT_TOKEN"

# Test rate limiting
for i in {1..12}; do
  curl -s -o /dev/null -w "Request $i Status: %{http_code}\n" "$DEPOSITO_URL/health" -H "Authorization: Bearer $JWT_TOKEN" &
done
wait

echo "Smoke test finalizado. Verifica los resultados y los logs de los servicios."
