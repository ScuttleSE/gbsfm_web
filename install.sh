echo "are we in a virtualenv already?"
if [[ "$VIRTUAL_ENV" == "" ]]
then
  echo "no, let's create one..."
  virtualenv --no-site-packages ./
  if [ $? -eq 0 ]
  then
    echo "...done"
  else
    echo "virtualenv creation failed"
    exit $?
  fi
else
  echo "yes we are!"
fi
source bin/activate
echo "installing missing dependencies..."
pip install -r requirements.txt
if [ $? -eq 0 ]
then
  echo "done!"
  echo "don't forget to type 'source bin/activate' to activate virtualenv before using manage.py"
else
  echo "dependency installation failed!"
  exit $?
fi
echo "finally, enter the SA account details used for validation and a longish secret key"
read -p 'SA Username: ' sa_username
read -sp 'SA Password: ' sa_password
echo
read -p 'Secret Key: ' secret_key
echo "# DO NOT CHECK THIS FILE INTO SOURCE CONTROL" > other_settings.py
echo "SA_USERNAME = '$sa_username'" >> other_settings.py
echo "SA_PASSWORD = '$sa_password'" >> other_settings.py
echo "SECRET_KEY = '$secret_key'" >> other_settings.py
echo "all done! run restart.sh to start the server!"
deactivate