import json, requests, time, os, datetime, sys, signal
import string, random
import selenium.webdriver as webdriver
import argparse, shlex
import concurrent.futures
from selenium.webdriver.chrome.options import Options

class CreateCookies:
    def __init__(self, save_path: str, qty: int = 10, max_threads: int = 3) -> None:
        self.folderCookie = save_path
        self.qty = int(qty)
        self.max_threads = int(max_threads)

    def _random_string_name(self):
        random_char = string.ascii_letters + string.digits
        random_string = ''.join((random.choice(random_char) for i in range(12)))
        return random_string
    
    def _create_single_cookie(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(options=chrome_options)
        start_url = 'https://twitter.com/elonmusk'
        try:
            while True:
                driver.get(start_url)
                all_cookies = driver.get_cookies()
                if len(all_cookies) >= 5 and 'gt' in [Data['name'] for Data in all_cookies]:
                    break
                time.sleep(3)
            fileName = self._random_string_name()
            with open(os.path.join(self.folderCookie, f'{fileName}.json'), 'w') as json_file:
                json.dump(all_cookies, json_file, indent=4)
            print(f"Cookie created: {fileName}")
        except Exception as e:
            print(f"Error creating cookie: {str(e)}")
        finally:
            driver.quit()

    def create_new_cookie(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = [executor.submit(self._create_single_cookie) for _ in range(self.qty)]
            concurrent.futures.wait(futures)
        print(f"Finished creating {self.qty} cookies")
        
class CheckTwitterAccount:
    def __init__(self, usernames_file_path: str, cookie_folder_path: str, max_threads: int = 3) -> None:
        self.usernames_file_path = usernames_file_path
        self.max_threads = int(max_threads)
        self.index = 0
        self.cookiesIndex = 0
        self.cookieStatus = ""
        self.allCookie = []
        self.folderCookie = cookie_folder_path
        self.die = 0
        self.live = 0
        self.cookies = {}
        self.token = ""
        self.username = []
        self.output_path = os.getcwd()

    def _read_cookie_files(self):
        for filename in os.listdir(self.folderCookie):
            if filename.endswith(".json"):
                self.allCookie.append(filename)

    def _read_username_files(self):
        with open(self.usernames_file_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                username = line.strip()
                self.username.append(username)

    def _write_to_output(self, content):
        file_name = datetime.datetime.now().strftime('%Y%m%d%H_output.txt')
        file_path = os.path.join(self.output_path, file_name)
        with open(file_path, 'a', encoding='utf-8') as file:
            if isinstance(content, dict):
                file.write(json.dumps(content, ensure_ascii=False) + '\n')
            else:
                file.write(str(content) + '\n')

    def _check_single_account(self, username):
        max_loop_times = 0
        while True:
            try:
                if self.cookiesIndex >= len(self.allCookie):
                    print("Out of cookies")
                    self._write_to_output(f"@{username}: status=error, reason=Out of cookies")
                    break
                
                filePath = os.path.join(self.folderCookie, self.allCookie[self.cookiesIndex])
                Cookie = {}
                allData = json.loads(open(filePath, 'r', encoding='utf-8').read())
                for Data in allData:
                    Cookie.update({Data['name']: Data['value']})
                    if Data['name'] == 'ct0':
                        token = {'x-csrf-token': Data['value']}
                    elif Data['name'] == 'gt':
                        token = {'x-guest-token': Data['value']}
                self.cookies = Cookie
                self.token = token

                self.headers = {'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA'}
                self.headers.update(self.token)
                params = {'variables': '{"screen_name":"' + username.replace('@', '').replace('https://twitter.com/', '').lower().strip() + '","withSafetyModeUserFields":true,"withSuperFollowsUserFields":true}', 'features': '{"responsive_web_twitter_blue_verified_badge_is_enabled":false,"verified_phone_label_enabled":false,"responsive_web_graphql_timeline_navigation_enabled":true}'}
                response = requests.get('https://twitter.com/i/api/graphql/ptQPCD7NrFS_TW71Lq07nw/UserByScreenName', params=params, headers=self.headers, cookies=self.cookies)
                try:                   
                    response_data = json.loads(response.text)

                    if len(response_data["data"]) == 0:
                        print(f"{username} wrong username")
                        self.die += 1
                        self._write_to_output({f"@{username}": {'status': 'wrong username', 'friends_count': '', 'followers_count': '', 'statuses_count': '', 'profile_image_url_https': '', 'profile_banner_url': '', 'location': '', 'name': '', 'description': '', 'created_at': '', 'cookie': self.allCookie[self.index]}})
                        break

                    if 'data' in response_data and 'user' in response_data['data']:
                        check = response_data['data']['user']['result']['__typename']
                        if check == 'User':
                            user_data = response_data['data']['user']['result']['legacy']
                            if user_data.get('profile_interstitial_type') == 'fake_account':
                                self.die += 1
                                user_info = {
                                        'status': 'die',
                                        'friends_count': '',
                                        'followers_count': '',
                                        'statuses_count': '',
                                        'profile_image_url_https':  '',
                                        'profile_banner_url': '',
                                        'location':'',
                                        'name': '',
                                        'description':  '',
                                        'created_at': '',
                                        'cookie': self.allCookie[self.index]
                                    }
                                self._write_to_output(f"{username}: {user_info}")
                                print(f"username: {username} status: die")
                                self.cookiesIndex += 1
                                break
                            else:
                                self.live += 1
                                user_info = {
                                    'status': 'live',
                                    'friends_count': user_data.get('friends_count', ''),
                                    'followers_count': user_data.get('followers_count', ''),
                                    'statuses_count': user_data.get('statuses_count', ''),
                                    'profile_image_url_https': user_data.get('profile_image_url_https', ''),
                                    'profile_banner_url': user_data.get('profile_banner_url', ''),
                                    'location': user_data.get('location', ''),
                                    'name': user_data.get('name', ''),
                                    'description': user_data.get('description', ''),
                                    'created_at': user_data.get('created_at', ''),
                                    'cookie': self.allCookie[self.index]
                                }
                                self._write_to_output({f"@{username}": user_info})
                                print(f"username: {username} status: live")
                                self.cookiesIndex += 1
                        elif check == 'UserUnavailable':
                            self.die += 1
                            self._write_to_output({f"@{username.replace('@', '').replace('https://twitter.com/', '')}": {'status': 'suspend', 'friends_count': '', 'followers_count': '', 'statuses_count': '', 'profile_image_url_https': '', 'profile_banner_url': '', 'location': '', 'name': '', 'description': '', 'created_at': '', 'cookie': self.allCookie[self.index]}})
                            print(f"username: {username} status: suspend")
                            self.cookiesIndex += 1
                        break
                except:
                    if str(response.text).find('limit') > -1:
                        self.index += int(self.max_threads)
                        self._write_to_output({f"@{username}": {'status': 'limit, change token', 'friends_count': '', 'followers_count': '', 'statuses_count': '', 'profile_image_url_https': '', 'profile_banner_url': '', 'location': '', 'name': '', 'description': '', 'created_at': '', 'cookie': self.allCookie[self.index]}})
                        time.sleep(1000)
                    elif str(response.text).find('Could not authenticate you') > -1 or str(response.text).find('Bad guest token') > -1:
                        self.index += int(self.max_threads)
                        self._write_to_output({f"@{username}": {'status': 'token expire, change token', 'friends_count': '', 'followers_count': '', 'statuses_count': '', 'profile_image_url_https': '', 'profile_banner_url': '', 'location': '', 'name': '', 'description': '', 'created_at': '', 'cookie': self.allCookie[self.index]}})
                        time.sleep(1000)
                    elif str(response.text).find('Denied by access control') > -1:
                        self._write_to_output({f"@{username}": {'status': 'lock Account', 'friends_count': '', 'followers_count': '', 'statuses_count': '', 'profile_image_url_https': '', 'profile_banner_url': '', 'location': '', 'name': '', 'description': '', 'created_at': '', 'cookie': self.allCookie[self.index]}})                        
                        time.sleep(1000)

                    self.cookiesIndex += 1
            except IndexError:
                self._write_to_output( {f"@{username}": {'status': 'lock Account', 'friends_count': '', 'followers_count': '', 'statuses_count': '', 'profile_image_url_https': '', 'profile_banner_url': '', 'location': '', 'name': '', 'description': '', 'created_at': '', 'cookie': 'Out of Cookie'}})
                self.cookiesIndex += 1
                break
            except Exception as e:
                print(str(e))
                self._write_to_output( {f"@{username}": {'status': 'not found', 'friends_count': '', 'followers_count': '', 'statuses_count': '', 'profile_image_url_https': '', 'profile_banner_url': '', 'location': '', 'name': '', 'description': '', 'created_at': '', 'cookie': 'Out of Cookie'}})
                self.cookiesIndex += 1
                if max_loop_times >= 10:
                    break
                max_loop_times += 1
                continue
            time.sleep(1000)  

    def check_account(self):
        # get cookie name
        self._read_username_files()
        self._read_cookie_files()

        def check_account_wrapper(username):
            self._check_single_account(username)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = [executor.submit(check_account_wrapper, username) for username in self.username]
            concurrent.futures.wait(futures)
    
        print(f"Finished check {len(self.username)} accounts")

def create_new_cookies_command(args):
    cookies = CreateCookies(args.savepath, args.qty, args.create_threads)
    cookies.create_new_cookie()
    print("Cookies creation completed.")

def check_account_command(args):
    check = CheckTwitterAccount(args.userpath, args.cookiespath, args.check_threads)
    check.check_account()
    print("Account checking completed.")

def signal_handler(sig, frame):
    print('\nApplication closing...')
    sys.exit(0)

def main_menu():
    parser = argparse.ArgumentParser(description="Twitter Account Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Parser for createnewcookies
    create_parser = subparsers.add_parser("createcookies", help="Create new cookies")
    create_parser.add_argument("--savepath", required=True, help="Path to save cookies")
    create_parser.add_argument("--qty", required=False, help="Cookies quantity")
    create_parser.add_argument("--create_threads", required=False, help="Thread quantity")

    # Parser for checkaccount
    check_parser = subparsers.add_parser("twitteraccount", help="Check Twitter X accounts")
    check_parser.add_argument("--userpath", required=True, help="Path to file containing usernames")
    check_parser.add_argument("--cookiespath", required=True, help="Path to folder containing cookies")
    check_parser.add_argument("--check_threads", required=False, help="Thread quantity")

    while True:
        print("\n--- MENU ---")
        print("Available commands:")
        print("createcookies --savepath D:/test/cookies --qty 10 --create_threads 4")
        print("twitteraccount --userpath D:/test/usercheck.txt --cookiespath D:/test/cookies --check_threads 4")
        print("exit (to quit the program)")
        
        command = input("Enter your command: ")
        
        if command.lower() == "exit":
            print("Thank you for using the program. Goodbye!")
            break

        try:
            args = parser.parse_args(shlex.split(command))
            if args.command == "createcookies":
                create_new_cookies_command(args)
            elif args.command == "twitteraccount":
                check_account_command(args)
            else:
                print("Invalid command. Please try again.")
        except SystemExit:
            # Catch the SystemExit exception to prevent the program from closing
            print("Invalid command or missing arguments. Please try again.")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    try:
        main_menu()
    except KeyboardInterrupt:
        print('\nApplication closing...')
        sys.exit(0)
