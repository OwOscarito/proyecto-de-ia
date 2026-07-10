# Podman image

## Build images

```sh
podman build -t localhost/smartlight-front -f SmartLight-Front.Dockerfile https://github.com/OwOscarito/proyecto-de-ia.git#fastapi_back_rewrite

podman build -t localhost/smartlight-back -f SmartLight-Back.Dockerfile https://github.com/OwOscarito/proyecto-de-ia.git#fastapi_back_rewrite
```

## Podman quadlets

```sh
cp containers/. ~/.config/containers/systemd/.

systemctl --user start smartlight-front
systemctl --user start smartlight-back
```
