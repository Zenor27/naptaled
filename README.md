# naptaled

## How to install

```
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python src/display_image.py
```

## Run FastAPI locally

> Make sure you have the virtual environment activated

```bash
fastapi dev app.py --port 8042
```

## Run Client locally

```bash
cd client/
pnpm install
pnpm dev
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

And you need to add the following to your `~/.ssh/config`:

```
Host 192.168.128.175
 Hostname 192.168.128.175
 Port 1030
```

You are good to go, you can now deploy to the raspberry

```bash
cd client && pnpm build
git add <your changes>
git commit -m "your message"
./deploy.sh
```

To see logs running on the raspberry:

```bash
ssh 192.168.128.175 -p 1030 -l piku logs naptaled
```
