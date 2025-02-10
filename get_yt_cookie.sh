yt-dlp --cookies-from-browser chrome --cookies cookies.txt https://www.youtube.com/watch?v=FZQisikpBEM
rm *.mp4
rm cookies.txt
grep youtube.com cookies.txt > www.youtube.com_cookies.txt