#!/bin/bash
/bin/date >> /tmp/sh_log_read_gmail.txt
echo $(date)
/opt/anaconda3/envs/argotek_odoo/bin/python /Volumes/RVC/Projects/argotek_odoo/read_gmail_and_post_as_lead.py >> /Volumes/RVC/Projects/argotek_odoo/logs/read_gmail_and_post.log 2>&1

