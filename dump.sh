#!/bin/sh

$pass = `cat creds.txt`

mysqldump -h DBHOST.HERE -u $user -p $pass deepmac > deepmac.sql
