```
cd functions/A_FUNCTION/
# if env doesnt exist yet
virtualenv env 
source env/bin/activate
pip install -r requirement.txt
# deploy to dev
zappa deploy dev
# leave the virtualenv
deactivate
```
