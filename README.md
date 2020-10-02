# BemaniBot
A Discord Bot hoping to serve functions based around the Bemani series.

# Setup

Clone the repository, and create a Python virtual environment folder called venv through:
` python -m venv venv `
Activate the venv through`. venv/bin/activate` or `venv/scripts/activate.bat` on Windows.
pip install the requirements through `pip install -r requirements.txt`.

You can access **sdvx.db** using SQLite3. The database has four schemas: 1 for general song information, 1 for song difficulty information, and 1 for song difficulty image URLS. 

# Usage and Commands
All commands start with an asterisk (*). 

> *ss | search | songsearch* [Song Name] 
>    - (Search for a song using title name (or artist).)

> *sd | searchdiff* [Difficulty and/or Number] 
>    - (Use level and/or number (ex: exh 18) to find a song.)

> *random* [lowerNumber - upperNumber]
>    - (Provides a random song for you to play!)
  
> *help*
>    - You're already here!
