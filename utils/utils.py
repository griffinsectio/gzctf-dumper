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

def makedirs(path):
    os.makedirs(path)

def is_dir_exists(path):
    return os.path.isdir(path)

def is_dir_empty(path):
    return not bool(len(os.listdir(path)))
