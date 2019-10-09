# HumbleBundleTroveLoader

HumbleBundleTroveLoader is used for downloading and making a complete back-up of your entire trove library from Humble Bundle.
It will download everything: games, books, music etc and try to group them together in folders based on the names (which isn't perfect unfortunately).


## Create the cookie string
Got [HumbleBundle.com](https://www.humblebundle.com), sign in to your library.  
  
The cookie string is tricky to get.
You need to get the value of the cookie named `_simpleauth_sess`.
Open the developer tools in your browser, go to storage and locate the cookie there.
Copy paste the value from `_simpleauth_sess`.

- In Firefox, open the [Storage Inspector](https://developer.mozilla.org/en-US/docs/Tools/Storage_Inspector) first click the row with `_simpleauth_sess`, then on `_simpleauth_sess` in the other menu far to the right under data, press <kbd>Ctrl</kbd>+<kbd>C</kbd> or <kbd>CMD</kbd>+<kbd>C</kbd> to copy. You'll get a string with `_simpleauth_sess:"eyJfc...9"`, just remove the first `_simpleauth_sess:` part and keep the rest as the cookie string.).
- In Chrome, open the [Resource Panel](https://developer.chrome.com/devtools/docs/resource-panel#cookies) and simply tripple-click the appropriate cell in the table to mark it and use <kbd>Ctrl</kbd>+<kbd>C</kbd> or <kbd>CMD</kbd>+<kbd>C</kbd> to copy. When pasting, be sure to surround the string in quotation marks ("") and remove trailing blank spaces.
- In Safari, open the _Storage Tab_ of the [Web Inspector](https://developer.apple.com/safari/tools/) (Context menu on the page, click _Inspect page_) click the _Storage_ tab, select _Cookies_ on the sidebar, select the `_simpleauth_sess` cookie, and press <kbd>Ctrl</kbd>+<kbd>C</kbd> or <kbd>Ctrl</kbd>+<kbd>C</kbd> to copy it. It will copy the hole line, so just keep the second part of it.  There is a `safari_cookie_extractor.py` tool which you can edit to aid you in the that process.   
Do not share your private data with anyone!


## Downloading missing games
The cookie string are timed-based and they will expire after a while (a couple of days).
When that happens, you have to grab the cookie again.
The previously downloaded files will not be downloaded again if.
