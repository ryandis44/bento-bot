import os
def sanitize_name(name) -> str:
    return str(name).replace("'", "''")

def get_audio(url):
    os.system("rm audio.opus")
    os.system(f"youtube-dl -f bestaudio --audio-format opus --no-playlist -x -o audio.opus {url}")