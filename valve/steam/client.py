# -*- coding: utf-8 -*-
# Copyright (C) 2013 Oliver Ainsworth

"""
    Provides an interface to the Steam client if present and running.

    Windows only.
"""

import itertools
import _winreg as winreg
import os

AWAY = "away"
BUSY = "busy"
OFFLINE = "offline"
ONLINE = "online"

DOWNLOADS = "downloads"
GAMES = "games"
GAMES_DETAILS = "games/details"
GAMES_GRID = "games/grid"
GAMES_LIST = "games/list"
GAMES_LIST_LARGE = "largegameslist"
GAMES_LIST_MINI = "minigameslist"
MEDIA = "media"
TOOLS = "tools"
ACTIVATE_PRODUCT = "activateproduct"
REGISTER_PRODUCT = "registerproduct"
FRIENDS = "friends"
MAIN = "main"
USER_MEDIA = "mymedia"
NEWS = "news"
SCREENSHOTS = "screenshots"
SERVERS = "servers"
SETTINGS = "settings"


class SteamClient(object):
    """
        Provides a means to interact with the current user's Steam
        client.

        It should be noted that most functionality that depends on the
        'Steam browser protocol' is completely untested, and parts
        seemingly broken. Broken parts methods will noted in their
        docstrings but left in the hopes that Valve fix/reintroduce
        them.

        https://developer.valvesoftware.com/wiki/Steam_browser_protocol
    """

    def __init__(self, **kwargs):

        # This flag is intended to be KEY_WOW64_64KEY or KEY_WOW_32KEY
        # from _winreg. I'm not entirely sure if it'd be possible to
        # detect whether this flag should be set automatically or
        # wether it needs to be here at all ...
        self.registry_access_flag = kwargs.get("registry_access_flag")

    def _get_registry_key(self, *args):
        args = list(itertools.chain(*[str(arg).split("\\") for arg in args]))
        sub_key = "Software\\Valve\Steam\\" + "\\".join(args[:-1])
        if self.registry_access_flag is not None:
            access_flag = self.registry_access_flag | winreg.KEY_QUERY_VALUE
        else:
            access_flag = winreg.KEY_QUERY_VALUE
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            sub_key, 0, access_flag) as key:
            return winreg.QueryValueEx(key, args[-1])[0]

    def _startfile(self, *args):
        args = list(itertools.chain(*[str(arg).split("/") for arg in args]))
        os.startfile("steam://" + "/".join(args))

    # TODO: def restart(self):
    #   return # HKEY_CURRENT_USER\Software\Valve\Steam\Restart = 1

    @property
    def is_offline(self):
        return self._get_registry_key("Offline")

    @property
    def path(self):
        return self._get_registry_key("SteamPath")

    @property
    def executable_path(self):
        return self._get_registry_key("SteamExe")

    @property
    def last_name(self):
        return self._get_registry_key("LastGameNameUsed")

    @property
    def language(self):
        return self._get_registry_key("Language")

    @property
    def pid(self):
        return self._get_registry_key("ActiveProcess\\pid")

    @property
    def dll(self):
        return self._get_registry_key("ActiveProcess\\SteamClientDll")

    @property
    def dll64(self):
        return self._get_registry_key("ActiveProcess\\SteamClientDll64")

    @property
    def update_available(self):
        return self._get_registry_key("Steam.exe\\UpdateAvailable")

    @property
    def update_progress(self):
        return (self._get_registry_key("Steam.exe\\UpdateBytesDownloaded"),
                self._get_registry_key("Steam.exe\\UpdateBytesToDownload"))

    def is_installed(self, appid):
        return self._get_registry_key("Apps", appid, "Installed")

    def add_non_steam_game(self):
        self._startfile("AddNonSteamGame")

    def open_store_page(self, appid):
        self._startfile("store", appid)

    def accept_gift(self, pass_):
        self._startfile("ackmessage/ackGuestPass", pass_)

    def open_news_page(self, appid, latest_only=False):

        if latest_only:
            self._startfile("updatenews", appid)
        else:
            self._startfile("appnews", appid)

    def backup_wizard(self, appid):
        self._startfile("backup", appid)

    def browse_media(self):
        self._startfile("browsemedia")

    def check_requirements(self, appid):
        self._startfile("checksysreqs", appid)

    def connect(self, host, port=None, password=None):
        args = ["connect", host]
        if port is not None:
            args[0] = args[0] + ":" + str(port)
        if password is not None:
            args.append(password)
        self._startfile(*args)

    def defragment(self, appid):
        self._startfile("defrag", appid)

    def close(self):
        self._startfile("ExitSteam")

    def opens_friends_list(self):
        self._startfile("friends")

    # TODO: def add_friend(self, steamid):
    #   return # steam://friends/add/<steamid>

    # steam://friends/friends/<id>
    # steam://friends/players

    # TODO: def join_chat(self, steamid):
    #   return # steam://friends/joinchat/<steamid>

    # TODO: def send_message(self, steamid):
    #   return # steam://friends/message/<steamid>

    def toggle_offline_friends(self):
        self._startfile("friends/settings/hideoffline")

    def toggle_friends_avatars(self):
        self._startfile("friends/settings/showavatars")

    def sort_friends(self):
        self._startfile("friends/settings/sortbyname")

    def set_status(self, status):
        self._startfile("friends/status", status)

    def flush_configs(self):
        self._startfile("flushconfig")

    def show_guest_passes(self):
        self._startfile("guestpasses")

    def install(self, appid):
        self._startfile("install", appid)

    def uninstall(self, appid):
        self._startfile("uninstall", appid)

    def install_addon(self, addon):
        self._startfile("installaddon", addon)

    def uninstall_addon(self, addon):
        self._startfile("removeaddon", addon)

    def navigate(self, component, *args, **kwargs):

        if kwargs.get("take_focus", False):
            self._startfile("open", component, *args)
        else:
            self._startfile("nav", component, *args)

    def validate(self, appid):
        self._startfile("validate", appid)

    def open_url(self, url):
        """ Broken """
        self._startfile("openurl", url)

    def preload(self, appid):
        self._startfile("preload", appid)

    def open_publisher_catalogue(self, publisher):
        self._startfile("publisher", publisher)

    def purchase(self, appid):
        self._startfile("purchase", appid)

    def subscribe(self, appid):
        self._startfile("purchase/subscription", appid)

    def run(self, appid):
        self._startfile("run", appid)


    # TODO: runsafe, rungameid, subscriptioninstall,
    # support, takesurvey, url
