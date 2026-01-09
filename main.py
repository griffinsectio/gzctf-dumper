import json
import argparse
import requests
import getpass
import os
import colorama
import urllib
from urllib.parse import urljoin

def p_json(j):
    print(json.dumps(j, indent=2))

def prepare_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)

def is_dir_empty(path):
    try:
        return next(os.scandir(path))
    except StopIteration:
        return True

class GzctfDumper:
    def __init__(self, url, username, password, output_dir):
        self.session = self.login(url, username, password)
        self.url = url
        self.output_dir = output_dir
        self.game_id = self.get_game_id()
        self.challs = self.get_game_challs()

    def login(self, url, username, password):
        endpoint = urljoin(url, "/api/account/login")
        headers = {
                "Content-Type": "application/json"
        }
        json = {
            "challenge": None,
            "userName": username,
            "password": password
        }

        session = requests.Session()
        res = session.post(endpoint, headers=headers, json=json)

        try:
            res.raise_for_status()
            return session
        except requests.exceptions.HTTPError as e:
            print(f"An HTTP error occurred: {e}")
            self.logout()
            exit(1)

    def logout(self):
        self.session.close()

    def get_games(self):
        endpoint = urljoin(self.url, "/api/game")
        params = {
                "count": 50,
                "skip": 0
        }
        res = self.session.get(endpoint, params=params)
        
        try:
            res.raise_for_status()
            return json.loads(res.text)
        except requests.exceptions.HTTPError as e:
            print(f"An HTTP error occurred: {e}")
            self.logout()
            exit(1)

    def get_game_id(self):
        games = self.get_games()['data']
        if len(games) == 1:
            self.game_id = games[0]['id']
        else:
            for i, game in enumerate(games, 1):
                n = f"[{i}] "
                title = game['title']
                summary = game['summary']
                print(colorama.Fore.GREEN + n, end="")
                print(colorama.Fore.BLUE + "Title: " + title)
                print(colorama.Fore.YELLOW + " "*len(n) + "Summary: " + summary)

            print(colorama.Fore.LIGHTRED_EX + colorama.Style.BRIGHT + "There are multiple games available")
            print("Enter the number of the game you want to dump")
            print(colorama.Style.RESET_ALL, end="")

            while True:
                choice = input(">> ")

                try:
                    choice = int(choice)
                except:
                    print(colorama.Fore.RED + "Please enter valid game number")
                    print(colorama.Style.RESET_ALL, end="")
                    continue
                
                if choice < 1 or choice > len(games):
                    print(colorama.Fore.RED + "Please enter valid game number")
                    print(colorama.Style.RESET_ALL, end="")
                    continue
                
                break

            return games[choice-1]['id']


    def get_game_info(self, game_id):
        endpoint = urljoin(self.url, f"/api/game/{game_id}")
        res = self.session.get(endpoint)
        
        try:
            res.raise_for_status()
            return json.loads(res.text)
        except requests.exceptions.HTTPError as e:
            print(f"An HTTP error occurred: {e}")
            self.logout()
            exit(1)

    def get_game_challs(self):
        endpoint = urljoin(self.url, f"/api/game/{self.game_id}/details")
        res = self.session.get(endpoint)
        
        try:
            res.raise_for_status()
            res = json.loads(res.text)
            return res['challenges']
            
        except requests.exceptions.HTTPError as e:
            print(f"An HTTP error occurred: {e}")
            self.logout()
            exit(1)

    def get_chall_info(self, chall_id):
        endpoint = urljoin(self.url, f"/api/game/{self.game_id}/challenges/{chall_id}")
        res = self.session.get(endpoint)
        
        try:
            res.raise_for_status()
            return json.loads(res.text)
        except requests.exceptions.HTTPError as e:
            print(f"An HTTP error occurred: {e}")
            self.logout()
            exit(1)

    def print_challs(self):
        for category, challs in self.challs.items():
            print(colorama.Style.BRIGHT + colorama.Fore.BLUE + category)
            for chall in challs:
                if chall['solved']:
                    print(colorama.Fore.GREEN + "[SOLVED] ".ljust(11, " "), end="")
                else:
                    print(colorama.Fore.RED + "[UNSOLVED] ", end="")

                print(f"{chall['title']} ({chall['score']})")

        print(colorama.Style.RESET_ALL, end="")

    def download_attachment(self, url, out):
        with urllib.request.urlopen(url) as res:
            with open(out, 'wb') as f:
                f.write(res.read())
        print(f"{out} downloaded")

    def dump_challs(self):
        for category, challs in self.challs.items():
            category_dir = os.path.join(self.output_dir, category)
            prepare_dir(category_dir)

            for chall in challs:
                info = self.get_chall_info(chall['id'])
                title = info['title']
                desc = info['content']
                hints = info['hints']
                score = info['score']
                # attachment
                att_url = info['context']['url']
                att_filename = att_url.split('/')[-1]
                att_size = info['context']['fileSize']

                url = urljoin(self.url, att_url)
                out = os.path.join(category_dir, att_filename)

                prepare_dir(category_dir)
                self.download_attachment(url, out)
            

    def dump_game(self):
        prepare_dir(self.output_dir)

        if not is_dir_empty(self.output_dir):
            print("The output directory is not empty")

            while True:
                choice = input("Do you want to continue? [Y/n]: ")
                choice = choice.strip()

                if (choice == "" or
                    choice.lower() == "y" or
                    choice.lower() == "yes"):
                    break
                elif (choice.lower() == "n" or
                    choice.lower() == "no"):
                    exit()
                else:
                    print("Please answer with yes/no")

        self.dump_challs()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            description="A simple python script for dumping gzctf games")

    parser.add_argument('url',
                        help="The base URL to gzctf instance")
    parser.add_argument('-u', '--username',
                        help="The username to login with (omit for interactive username input)")
    parser.add_argument('-p', '--password',
                        help="The password for the user (omit for interactive password input)")
    parser.add_argument('-o', '--output',
                        default="Dump",
                        help="Directory where to dump the files")

    args = parser.parse_args()

    url = args.url
    username = args.username
    password = args.password
    output_dir = args.output

    if not args.username:
        username = input("Username: ")
    if not args.password:
        password = getpass.getpass(prompt="Password: ")

    dumper = GzctfDumper(url, username, password, output_dir)

    dumper.print_challs()
    dumper.dump_game()

