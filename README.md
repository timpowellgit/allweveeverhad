# allweveeverhad

### main web UI (for testing)

`http://67.205.150.194:28473/`

### digital ocean server notes

- env vars are defined in `/var/www/allweveeverhad/src/2_web/envvars`

- repo is installed under `/var/www/allweveeverhad`

- restart commands:

```
systemctl restart hash_proximity_server
systemctl restart img_hashing_find_proxim
systemctl restart nginx
```

- to see logs:

```
journalctl -f -u hash_proximity_server
journalctl -f -u img_hashing_find_proxim
```

- to locally (on server) test hash proximity service:

```
curl localhost:5000/?ahash=ffffffc3c3c3c081
```

### digital ocean server ports

- PORT 48809
```
/mnt/volume image server
http://67.205.150.194:48809/2fee9d62-66cf-4ae3-af4c-e3b2a1f1b32e/artsy/
http://67.205.150.194:48809/2fee9d62-66cf-4ae3-af4c-e3b2a1f1b32e/met/
http://67.205.150.194:48809/2fee9d62-66cf-4ae3-af4c-e3b2a1f1b32e/allpainters/
http://67.205.150.194:48809/2fee9d62-66cf-4ae3-af4c-e3b2a1f1b32e/moma/
```

- localhost:5000
```
internal hashing service
```

- PORT 28473
```
main hashing UI port
http://67.205.150.194:28473/
```

### installation from scratch on Ubuntu

```
# generate ssh key
ssh-keygen -t rsa -b 4096 -C "me@example.com"
eval "$(ssh-agent -s)"
# get ssh key, copy to clipboard
cat .ssh/id_rsa.pub
# add key to github project's deploy keys
# clone repo
git clone git@github.com:gregsadetsky/allweveeverhad.git
# install python, pip, virtualenv
sudo apt-get update
sudo apt-get install python2.7
sudo apt-get install python-setuptools python-dev build-essential
sudo easy_install pip
sudo pip install --upgrade virtualenv
# create virtualenv, activate it, install packages
virtualenv --no-site-packages venv
source venv/bin/activate
pip install -r requirements.txt
````

### service configuration files

config files for the `img_hashing_find_proxim` and `hash_proximity_server` services are located under `/etc/systemd/system/`

### nginx configuration

`/etc/nginx/sites-enabled/default` for the public paths to the images

`systemctl restart nginx`

### TODO

- (related to below) cleanup duplicated models and model_utils...!!!!!

- create directories under src/1_ingest_data to separate py files by source (artsy, met, etc.)
currently not doing it to be able to do 'from models import ...' which would not work if models
is subdirectory level up...


### cleanup

delete files:
- <repo>/scikit-image directory
- src/4_realtime_calibration/lines.py
