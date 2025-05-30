#!/bin/bash

PYTHON_SCRIPT="/Volumes/RVC/Projects/argotek_odoo/read_gmail_and_post_as_lead.py"
LOGFILE="/Volumes/RVC/Projects/argotek_odoo/logs/read_gmail_and_post.log"
/opt/anaconda3/envs/argotek_odoo/bin/python "$PYTHON_SCRIPT" >> "$LOGFILE" 2>&1

