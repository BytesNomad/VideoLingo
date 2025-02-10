yt-dlp --cookies-from-browser chrome --cookies cookies.txt https://www.youtube.com/watch?v=FZQisikpBEM
rm *.mp4
echo "# Netscape HTTP Cookie File" > www.youtube.com_cookies.txt
echo "# http://curl.haxx.se/rfc/cookie_spec.html\n" >> www.youtube.com_cookies.txt

grep youtube.com cookies.txt >> www.youtube.com_cookies.txt

rm cookies.txt
