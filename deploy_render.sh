#!/bin/bash
set -e

# Render CLI deployment script.
# Run this on your local machine with render-cli installed and authenticated.

# 1) login
# render login

SERVICE_NAME=mcp-server

# 2) create service if not exists
# render services create web $SERVICE_NAME --region oregon --service-branch main --branch main --plan free --git-repo https://github.com/confidential0294-debug/LOG

# 3) set settings via render.yaml (preferred) and environment variable
render services update $SERVICE_NAME --env-vars RENDER_SERVICE_NAME=$SERVICE_NAME

# 4) trigger deploy
render deploy --service $SERVICE_NAME

# 5) check status
render services list | grep $SERVICE_NAME

echo "Run: curl -I https://$SERVICE_NAME.onrender.com/sse" 
