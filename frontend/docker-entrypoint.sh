#!/bin/sh

# The service name is 'backend' and the internal port is 8000.
BACKEND_HOST="backend"
BACKEND_PORT="8000"
TIMEOUT=5

echo "--- Waiting for $BACKEND_HOST:$BACKEND_PORT to be ready... ---"

# Loop until the curl command succeeds (i.e., the backend is listening)
# It tries every 5 seconds until the health check passes.
until curl --output /dev/null --silent --head --fail http://$BACKEND_HOST:$BACKEND_PORT; do
    echo -n "."
    sleep $TIMEOUT
done

echo ""
echo "Backend is ready! Starting Next.js server."

# Execute the main application command (npm start)
exec npm start