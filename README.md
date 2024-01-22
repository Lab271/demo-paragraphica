# paragraphica
Our remake of the paragraphica project by [Bjoern Karmann](https://bjoernkarmann.dk/project/paragraphica). This codebase is setup such that it can be tested from any developer laptop without the need of a Raspberry or GPS devices.

Be sure to set the environ variables first


To get started run
``` 
    cd  [this_folder]
    virtualenv .para
    source .para/bin/activate 
    make dev
```

Visual studio code plugins are such that they recognize the virtualenv ./.para immediately

## Todo
1. raspberry pi python setup
2. api based prompt to midjourney or others
3. location api
4. weather api
5. rotary switches on RPI GPIO
6. Parameter setting
7. Display controller
8. include camera?
9. wifi
10. image processing
11. Raspberry pi headless setup




Libraries
1. Original: https://github.com/bjoernkarmann/Paragraphica/blob/main/main.py
2. Rotary encoder: https://github.com/miketeachman/micropython-rotary
3. open weathermap
4. mapbox api service