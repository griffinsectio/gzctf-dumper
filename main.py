import json
import argparse
import requests
import getpass
import os
import urllib
from urllib.parse import urljoin
from tqdm import tqdm
import utils.utils as utils

class GzctfDumper:
    def __init__(self, url, username, password, output_dir):
        self.session = self.login(url, username, password)
        self.url = url
        self.output_dir = output_dir
        self.games = self.get_games()
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
            if res.status_code == 401:
                utils.print_red("Incorrect username or password")
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
            return json.loads(res.text)['data']
        except requests.exceptions.HTTPError as e:
            print(f"An HTTP error occurred: {e}")
            self.logout()
            exit(1)

    def get_game_id(self):
        if len(self.games) == 1:
            self.game_id = self.games[0]['id']
        else:
            for i, game in enumerate(self.games, 1):
                n = f"[{i}] "
                title = game['title']
                summary = game['summary']
                utils.print_green(n, end="")
                utils.print_yellow("Title: " + title)
                utils.print_blue(" "*len(n) + "Summary: " + summary)

            utils.print_red("There are multiple games available")
            utils.print_red("Enter the number of the game you want to dump")

            while True:
                choice = input(">> ")

                try:
                    choice = int(choice)
                except:
                    utils.print_red("Please enter valid game number")
                    continue
                
                if choice < 1 or choice > len(self.games):
                    utils.print_red("Please enter valid game number")
                    continue
                
                break

            return self.games[choice-1]['id']


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
            challenges = json.loads(res.text)['challenges']
            return challenges
            
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
        utils.print_yellow("[#] Game Challenges")
        for category, challs in self.challs.items():
            utils.print_blue(f"    [#] {category}")
            for chall in challs:
                chall_info = f"       [-] {chall['title']} ({chall['score']})"
                if chall['solved']:
                    chall_info += " [SOLVED]"
                    utils.print_green(chall_info)
                else:
                    chall_info += " [NOT SOLVED]"
                    utils.print_red(chall_info)

    def download_attachment(self, url, out, size):
        with self.session.get(url, stream=True) as res:
            with tqdm(total=size, desc=out, unit='B', unit_scale=True, colour='blue', leave=False) as pb:
                try:
                    with open(out, 'wb') as f:
                        res.raise_for_status()

                        for chunk in res.iter_content(chunk_size=8192):
                            pb.update(len(chunk))
                            f.write(chunk)

                except requests.exceptions.HTTPError as e:
                    print(f"An HTTP error occurred: {e}")
                    self.logout()
                    return False
        return True

    def dump_challs(self):
        utils.print_yellow("[#] Downloading challenges attachments")
        for category, challs in self.challs.items():
            category_dir = os.path.join(self.output_dir, category)

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

                chall_dir = os.path.join(category_dir, title)
                out = os.path.join(chall_dir, att_filename)
                utils.prepare_dir(chall_dir)

                if self.download_attachment(url, out, att_size):
                    utils.print_green(f"    [-] {out} downloaded")
                else:
                    utils.print_red  (f"    [-] {out} download failed")
            

    def dump_game(self):
        utils.prepare_dir(self.output_dir)

        if not utils.is_dir_empty(self.output_dir):
            utils.print_red("The output directory is not empty")

            while True:
                choice = input("Do you want to continue? [Y/n]: ")
                choice = choice.strip()

                if (choice == "" or
                    choice.lower() == "y" or
                    choice.lower() == "yes"):
                    break
                elif (choice.lower() == "n" or
                    choice.lower() == "no"):
                    return
                else:
                    utils.print_red("Please answer with yes/no")

        self.print_challs()
        self.dump_challs()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            description="A simple python script for dumping GZ::CTF games")

    parser.add_argument('url',
                        help="The base URL of GZ::CTF instance")
    parser.add_argument('-u', '--username',
                        help="The username to login with (omit for interactive username input)")
    parser.add_argument('-p', '--password',
                        help="The password for the user (omit for interactive password input)")
    parser.add_argument('-o', '--output',
                        default="Dump",
                        help="Directory where to dump the files (default: ./Dump)")

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

    dumper.dump_game()
    dumper.logout()

