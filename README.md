# Salmonia

Download JSON from Nintendo and Upload SalmonStats automatically.

## Requirements

- Python3.7 and above

## Installation

```zsh
python3 -m pip install -r requirements.txt
python3 main.py
```

Now, Salmonia support to upload the latest result.

### Features

- [x] Authorization for SplatNet2
- [x] Update X-Product Version automatically
- [x] Save credential files
- [ ] Standalone
  - [ ] Check the latest result id
  - [x] Upload a result from SplatNet2
  - [ ] Upload results saved from SplatNet2
  - [ ] Save a result

### Environment

This Salmonia is currently available for local environment only. If you change the variable of environment in following line.

https://github.com/tkgstrator/Salmonia/blob/c4373d95121781259a30a1b8134223bf8d4b6e08/salmonia.py#L98

### Salmon Stats Server

Launch the owned salmon stats server.

```zsh
git clone https://github.com/SalmonStats/api salmon-stats-sever
cd salmon-stats-server
make init
```

edit `docker-compose.yml` and `.env`.

and open another console window, type `make migrate` and `make up`
