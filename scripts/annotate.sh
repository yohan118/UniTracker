#!/bin/bash
# turns stdin into one warning annotation in github actions
# (so logs show up on the run page). usage: cmd | ./annotate.sh "title"
text=$(cat)
text=${text//'%'/'%25'}
text=${text//$'\r'/'%0D'}
text=${text//$'\n'/'%0A'}
echo "::warning title=$1::$text"
