#!/bin/sh

KIOSKURL=$(cat ~/.kiosk-url)

if [ -z "$KIOSKURL" ]; then
    KIOSKURL="http://localhost:8501/"
fi

if [ -e '/boot/alwayson' ] || [ -e '$HOME/.kiosk-alwayson' ] ; then
  xset -dpms
  xset s off
fi

# clean up if like me you just yank the power or ssh in and poweroff
rm -rf ~/.config/chromium/Singleton*

sleep 15

# Launch chromium in kiosk mode, incognito with a reputable, well-designed url
DISPLAY=:0 chromium-browser --kiosk --incognito --force-device-scale-factor=1  $KIOSKURL