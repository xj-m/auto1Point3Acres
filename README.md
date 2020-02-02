# auto1point3Acres

## Summary

An automated script to get the daily reward in 1point3auto (一亩三分地). The deployment is based on Heroku.

## Deployment

### step1: setup `username.json`

Input your account username and password into `username.json`

### step2: run command

First install required packages:
1. Make sure your python environment meet the `requirement`, you can in case run `pip3 install -r requirements.txt`
2. You need `chromedriver`

Then run `python main.py`

## Credit

- [1p3a_python_script](https://github.com/VividLau/1p3a_python_script)

The code is forked from this project, which automated the process of login to 1point3acres and gets the daily reward. One thing to point out is that it uses `pytesseract` for authentication code recognition, which makes it fully automated.

- [1point3auto](https://github.com/CryoliteZ/1point3auto)

I followed this project's idea and instructions to deploy the script to Heroku, which simplified the deployment to almost one click.
