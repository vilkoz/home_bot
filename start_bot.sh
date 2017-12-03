PWD=`dirname "$0"`
cd ${PWD}
git pull
. ./PASSWORDS
source ./venv3/bin/activate
python3 ./bot.py
