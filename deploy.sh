#/bin/bash

echo "Deploying to raspberry..."

if ! git remote | grep -q piku; then
  echo "No piku remote found, maybe you need to run $(git remote add piku piku@192.168.10.223:1030/naptaled)"
  exit 1
fi

curl -X POST -F "script=deployment" http://192.168.10.223:8042/scripts/change --connect-timeout 10
git push piku --force
curl -X POST -F "script=display_screensaver" http://192.168.10.223:8042/scripts/change --connect-timeout 10
