# naptaled

## How to install

```
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python src/display_image.py
```


## How to deploy

You first need to add your ssh public key on the raspberry

```bash
ssh 192.168.128.175 -p 1030 -l napta
sudo su - piku
touch /tmp/<mysshkey>.pub
python3 piku.py setup:ssh /tmp/<mysshkey>.pub
```

Then on your machine you need to add the remote

```bash
git remote add piku piku@192.168.128.175:naptaled
```

You are good to go, you can now deploy to the raspberry

```bash
git add <your changes>
git commit -m "your message"
./deploy.sh
```