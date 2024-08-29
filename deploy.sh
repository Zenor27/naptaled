#/bin/bash

echo "Deploying to raspberry..."

if ! git remote | grep -q piku; then
  echo "No piku remote found, maybe you need to run $(git remote add piku piku@192.168.128.175:naptaled)"
  exit 1
fi

git push piku --force
