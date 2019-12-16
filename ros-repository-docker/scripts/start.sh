#!/bin/sh
sign=`grep -w 'SignWith' /var/www/building/ubuntu/conf/distributions`
echo ${SIGNKEY}
if [ -z "$sign" ]
then
	echo "SignWith: ${SIGNKEY}"
	echo "SignWith: ${SIGNKEY}" >> /var/www/building/ubuntu/conf/distributions
fi
cat /var/www/building/ubuntu/conf/distributions
gpg --batch --import /home/public.key /home/signing.key
service nginx start
