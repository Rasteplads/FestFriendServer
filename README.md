# FestFriendServer
ID Server for festfriend to create and join groups

# Setup
```sh
python -m venv .venv
.venv/Scripts/Activate.ps1
python -m pip install -r requirements.txt
```

Activate script to use depends on the operating system and shell

# Run Server in development
```sh
uvicorn server:app --reload
```