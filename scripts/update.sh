#!/bin/bash
cd $REPO_DIR
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
systemctl restart chatumba
echo "Chatumba обновлен и перезапущен"
