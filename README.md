# SNCRS

## Because Making SmashNights Extra Doesn't Mean Extra Work

This repo is to facilitate the glory that is SNCRS, via the challonge api and our own Django project. This repo will be hosted as a full web application with a sqlite backend.

## Installation

To be able to use this script, you will likely want a linux or mac instance, but I'm sure there is some way to do it on Windows also. The guide following is for linux.

### Step 1: Clone from GitHub

Hey! You're already here, so that's great! To clone this repo, just open a terminal and navigate to whatever directory you want this in. Then copy and paste the command below:

`git clone https://github.com/Jyckle/sncrs.git`

Then you should have a directory called sncrs! You can then run:

`cd sncrs`

### Step 2: Make sure docker is installed

Try

`docker --version`

If there is no version installed, follow the instructions to install it [here](https://docs.docker.com/engine/install/)

### Step 3: Run qs to start the dev container

This one is super easy but might take a minute. Just run:

```bash
./qs run dev
```

Congratulations! You now have everything you need installed!

You should be able to access the instance at the url provided and the admin interface at the url with /admin at the end

To run the main code that updates all scores and everything, select the SmashNight in question in the admin panel, and then from the Action bar, select "Get all data associated with the selected SmashNights and update scores" and then hit go. Take note, this will update the overall status for each person, so only run this once everything is in order!

Then, the magic happens! Voila!

## Other commands

### Production deployment

```bash
./qs run prod
```

### Stop Dev or Prod

```bash
./qs stop dev
./qs stop prod
```

### Set up backups

```bash
./qs backup install <prod|dev>
```

### Update the backup script without changing the cron job

```bash
./qs backup update <prod|dev>
```

### Back up immediately

```bash
./qs backup now <prod|dev> [local_file_location]
```

If local_file_location is provided, the backup file will be placed in that location. This is ideal for local testing

### Restore from a backup

```bash
./qs backup restore <prod|dev> [file_location]
```

The backup will be restored to the specified container (prod|dev). Note that this includes media files and all database info.
This will clear out existing data, so be careful!

## Long Live SmashNights!
