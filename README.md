# FestFriendServer
ID Server for festfriend to create and join groups


# Setup
Clone the project with Git and cd into the directory
```sh
git clone https://github.com/Rasteplads/FestFriendServer.git
cd FestFriendServer
```

Create and activate a virtual environment (Optional).
## Windows
```sh
python -m venv .venv
.venv/Scripts/Activate.ps1
```

## Linux / Mac
```sh
python -m venv .venv
source .venv/bin/activate
```

Install the FestFriendServer package with pip
```sh
pip install -e .
```

Run the server
```sh
ffserver
```