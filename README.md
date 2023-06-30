# SNCRS

## Because Making SmashNights Extra Doesn't Mean Extra Work

This repo is to facilitate the glory that is SNCRS, via the challonge api and our own Django project. This repo will be hosted as a full web application with a sqlite backend.

## Installation

To be able to use this script, you will likely want a linux or mac instance, but I'm sure there is some way to do it on Windows also. The guide following is for linux.

#### Step 1: Clone from GitHub

Hey! You're already here, so that's great! To clone this repo, just open a terminal and navigate to whatever directory you want this in. Then copy and paste the command below:

`git clone https://github.com/Jyckle/sncrs.git`

Then you should have a directory called sncrs! You can then run:

`cd sncrs`

#### Step 2: Create and Activate a Virtual Environment

You will want a virtual environment to keep this all in so that things don't get messy on your system. You can run:

`python3 -m venv env`

To create the virtual environment. This only needs to be done once.
Then, whenever you want to activate it, make sure you are in the SNCRS directory, and run:

`source env/bin/activate` for POSIX
`source env/Scripts/activate` for git bash

Which should then make a (env) appear before your terminal prompt.

#### Step 3: Run the Makefile to get all the Dependencies

This one is super easy but might take a minute. Just run:

`make`

Congratulations! You now have everything you need installed!

## Running a local instance of Django

To use this instance locally, you first need to run the following commands:

`cd sncrs`
`python manage.py runserver`

Then you should be able to access the instance at the url provided and the admin interface at the url with /admin at the end

To run the main code that updates all scores and everything, select the SmashNight in question in the admin panel, and then from the Action bar, select "Get all data associated with the selected SmashNights and update scores" and then hit go. Take note, this will update the overall status for each person, so only run this once everything is in order!

Then, the magic happens! Voila!

## Long Live SmashNights!
