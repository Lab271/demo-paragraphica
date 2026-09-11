# paragraphica
Our remake of the paragraphica project by [Bjoern Karmann](https://bjoernkarmann.dk/project/paragraphica), now called Terra Virtualis. This codebase is setup such that it can be tested from any developer laptop without the need of a Raspberry or GPS devices. Working title is now gpt_viewmaster, our GPT pane on the world.

Be sure to set the environ variables first

To get started (needs [mise](https://mise.jdx.dev/), which pins Python and uv):
```
    cd  [this_folder]
    mise install
    make install
```

Then, for the developer loop:
```
    make dry-run LOCATION="Amsterdam" STYLE="film noir"   # description + prompt only, no image call
    make run LOCATION="Amsterdam" STYLE="film noir"       # writes output/output.png
    uv run terra options                                  # list styles, contexts, positions
```
`make help` lists everything. The Streamlit UI is legacy (`make streamlit`, removed in #10). See `docs/plan-2026-09.md` for the rebuild plan.

Be sure to have the environment variables available:
```
    export PARA_MAPBOX_API={{ MAPBOX_API }}
    export PARA_OPENWEATHERMAP_API={{ OPENWEATHERMAP_API }}
    export OPENAI_API_KEY={{ OPENAI_API_KEY }}
```
which can be found in our password tools.

## Todo
1. [DONE] raspberry pi python setup
2. api based prompt to midjourney or others
3. [DONE] location api
4. [DONE] weather api
5. rotary switches on RPI GPIO
6. [DONE] Parameter setting
7. Display controller
8. include camera?
9. wifi
10. image processing
11. [DONE] Raspberry pi headless setup


Libraries
1. Original: https://github.com/bjoernkarmann/Paragraphica/blob/main/main.py
2. Rotary encoder: https://github.com/miketeachman/micropython-rotary
3. open weathermap
4. geotimezone.com
5. mapbox api service
6. openai for ChatGPT and Dall-E
