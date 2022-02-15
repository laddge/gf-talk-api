import shutil
import os
import neologdn
import re
import emoji
import MeCab

def normalize(path):
    shutil.move(path, path + ".org")
    with open(path + ".org") as f:
        for line in f:
            line = line.replace(" ", "")
            line = neologdn.normalize(line)
            line = "".join(["" if c in emoji.UNICODE_EMOJI["en"].keys() else c for c in line])
            tmp = re.sub(r"(\d)([,.])(\d+)", r"\1\3", line)
            line = re.sub(r"\d+", "0", tmp)
            tmp = re.sub(r"[!-/:-@[-`{-~]", r" ", line)
            line = re.sub(u"[■-♯]", " ", tmp)
            wakati = MeCab.Tagger("-Owakati")
            line = wakati.parse(line)
            with open(path, "a") as f:
                f.write(line)
    os.remove(path + ".org")


normalize("./data/input.txt")
normalize("./data/output.txt")
