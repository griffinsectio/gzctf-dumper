import os
import colorama
import json

def print_red(text, *args, **kwargs):
    print(colorama.Fore.RED + text + colorama.Style.RESET_ALL, *args, **kwargs)

def print_green(text, *args, **kwargs):
    print(colorama.Fore.GREEN + text + colorama.Style.RESET_ALL, *args, **kwargs)

def print_blue(text, *args, **kwargs):
    print(colorama.Fore.BLUE + text + colorama.Style.RESET_ALL, *args, **kwargs)

def print_yellow(text, *args, **kwargs):
    print(colorama.Fore.YELLOW + text + colorama.Style.RESET_ALL, *args, **kwargs)

def p_json(j):
    print(json.dumps(j, indent=2))

def prepare_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)

def is_dir_empty(path):
    if len(os.listdir(path)):
        return False
    else:
        return True

