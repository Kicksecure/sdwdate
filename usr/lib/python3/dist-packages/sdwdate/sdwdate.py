#!/usr/bin/python3 -u

# Copyright (C) 2017 - 2020 ENCRYPTED SUPPORT LP <adrelanos@riseup.net>
# See the file COPYING for copying conditions.

from __future__ import print_function
from pathlib import Path
import re
import json
import subprocess
from subprocess import Popen
from random import randint
import random
from datetime import datetime
import time
import glob
import os
import signal
import logging
import sys
import sdnotify
from guimessages.translations import _translations
from sdwdate.proxy_settings import proxy_settings
from sdwdate.timesanitycheck import time_consensus_sanity_check
from sdwdate.timesanitycheck import static_time_sanity_check
from sdwdate.config import read_pools
from sdwdate.remote_times import get_time_from_servers

sys.dont_write_bytecode = True


os.environ["LC_TIME"] = "C"
os.environ["TZ"] = "UTC"
time.tzset()

SDNOTIFY_OBJECT = sdnotify.SystemdNotifier()
SDNOTIFY_OBJECT.notify("READY=1")
SDNOTIFY_OBJECT.notify("STATUS=Starting...")


class TimeSourcePool(object):
    def __init__(self, pool):
        self.url, self.comment = read_pools(pool, "production")
        self.url_random_pool = []
        self.already_picked_index = []
        self.done = False


class Sdwdate(object):
    def __init__(self):
        self.failure_ratio_from_config = self.allowed_failures_config()

        self.iteration = 0
        self.number_of_pools = 3
        pool_range = range(self.number_of_pools)
        self.pools = []
        for pool_i in pool_range:
            self.pools.append(TimeSourcePool(pool_i))

        total_number_pool_member = 0
        for pool_temp in self.pools:
            total_number_pool_member += len(pool_temp.url)

        self.allowed_failures = self.allowed_failures_calculate(
            self.failure_ratio_from_config,
            self.number_of_pools,
            total_number_pool_member)

        self.list_of_urls_returned = []
        self.list_of_url_random_requested = []
        self.valid_urls = []
        self.list_of_stdout = []
        self.list_of_stderr = []
        self.list_of_exit_codes = []
        self.list_of_timeout_status = []

        self.request_unixtimes = {}
        self.request_took_times = {}
        self.list_of_took_time = []
        self.half_took_time_float = {}
        self.time_diff_lag_cleaned_float = {}

        self.unixtimes = []
        self.pools_raw_diff = []
        self.pools_lag_cleaned_diff = []
        self.failed_urls = []

        self.median_diff_raw_in_seconds = 0
        self.median_diff_lag_cleaned_in_seconds = 0
        self.range_nanoseconds = 999999999
        self.new_diff_in_seconds = 0
        self.new_diff_in_nanoseconds = 0
        self.unixtime_before_sleep = 0
        self.sleep_time_seconds = 0

        self.sleep_process = []
        self.sclockadj_process = []

        home_folder = str(Path.home())
        home_folder_split = os.path.split(Path.home())

        if home_folder_split[0] == "/home":
            # Required for support of running as users other than sdwdate.
            sdwdate_status_files_folder = home_folder + "/sdwdate"
            sdwdate_persistent_files_folder = sdwdate_status_files_folder
            # example sdwdate_status_files_folder:
            # /home/user/sdwdate
        else:
            # home folder for user "sdwdate" is set to /run/sdwdate
            sdwdate_status_files_folder = home_folder
            sdwdate_persistent_files_folder = "/var/lib/sdwdate"
            # example sdwdate_status_files_folder:
            # /run/sdwdate

        # Sanity test.
        sdwdate_status_files_folder_split = os.path.split(
            sdwdate_status_files_folder)
        if not sdwdate_status_files_folder_split[-1] == "sdwdate":
            print("ERROR: home folder does not end with /sdwdate")
            print("ERROR: home_folder_split: " + str(home_folder_split))
            print(
                "ERROR: sdwdate_status_files_folder_split: "
                + str(sdwdate_status_files_folder_split)
            )
            print(
                "ERROR: sdwdate_status_files_folder: " +
                sdwdate_status_files_folder)
            #reason = "home folder does not end with /sdwdate"
            exit_code = 1
            # Not available at this point.
            # sdwdate.exit_handler(EXIT_CODE, reason)
            sys.exit(exit_code)

        Path(sdwdate_status_files_folder).mkdir(parents=True, exist_ok=True)
        # Sanity test. Should be already created by systemd-tmpfiles.
        Path(sdwdate_persistent_files_folder).mkdir(
            parents=True, exist_ok=True)

        # Workaround for an apparmor issue.
        # See /etc/apparmor.d/usr.bin.sdwdate
        # for /run/sdwdate/forbidden-temp
        sdwdate_forbidden_temp_files_folder = (
            sdwdate_status_files_folder + "/forbidden-temp"
        )
        # Sanity test. Should be already created by systemd-tmpfiles.
        Path(sdwdate_forbidden_temp_files_folder).mkdir(
            parents=True, exist_ok=True)
        # Without this python-requests (url_to_unixtime) would try to write to
        # for example "/xb2e9wyl" instead of
        # "/run/sdwdate/forbidden-temp/xb2e9wyl"
        # which looks even worse in logs and cannot be deny'd in the apparmor
        # profile.
        os.chdir(sdwdate_forbidden_temp_files_folder)

        self.status_first_success_path = \
            sdwdate_status_files_folder + "/first_success"
        self.status_success_path = sdwdate_status_files_folder + "/success"
        self.status_file_path = sdwdate_status_files_folder + "/status"
        self.sleep_long_file_path = \
            sdwdate_status_files_folder + "/sleep_long"
        self.fail_file_path = sdwdate_status_files_folder + "/fail"
        self.clock_jump_do_once_file = (
            sdwdate_status_files_folder + "/clock_jump_do_once"
        )
        # Read by systemcheck.
        self.msg_path = sdwdate_status_files_folder + "/msg"

        self.sdwdate_time_replay_protection_utc_unixtime = (
            sdwdate_persistent_files_folder +
            "/time-replay-protection-utc-unixtime")
        self.sdwdate_time_replay_protection_utc_humanreadable = (
            sdwdate_persistent_files_folder
            + "/time-replay-protection-utc-humanreadable"
        )

        self.status = {"icon": "", "message": ""}

        translations_path = "/usr/share/translations/sdwdate.yaml"
        translation = _translations(translations_path, "sdwdate")
        self.translate_object = translation.gettext

        self.proxy_ip, self.proxy_port = proxy_settings()

        self.time_replay_protection_minium_unixtime_int, \
            self.time_replay_protection_minium_unixtime_human_readable = (
                self.time_replay_protection_file_read()
            )

        self.time_replay_protection_minium_unixtime_human_readable = \
            self.time_replay_protection_minium_unixtime_human_readable.strip()

        self.time_replay_protection_minium_unixtime_str = str(
            self.time_replay_protection_minium_unixtime_int
        )

    @staticmethod
    def allowed_failures_config():
        failure_ratio = None
        if os.path.exists("/etc/sdwdate.d/"):
            files = sorted(glob.glob("/etc/sdwdate.d/*.conf"))
            for file_item in files:
                with open(file_item) as conf:
                    lines = conf.readlines()
                for line in lines:
                    if line.startswith("MAX_FAILURE_RATIO"):
                        failure_ratio = re.search(r"=(.*)", line).group(1)
        if failure_ratio is None:
            failure_ratio = 0.34
        return failure_ratio

    @staticmethod
    def allowed_failures_calculate(
            failure_ratio,
            pools_total_number,
            number_of_pool_members):
        temp = float(number_of_pool_members) * float(failure_ratio)
        allowed_failures_value = temp / pools_total_number
        allowed_failures_value = int(allowed_failures_value)
        return allowed_failures_value

    def signal_handler(self, signum, frame):
        message = self.translate_object("sigterm")
        stripped_message = self.strip_html(message)
        LOGGER.info(stripped_message)
        reason = "signal_handler called"
        exit_code = 143
        self.exit_handler(exit_code, reason)

    def exit_handler(self, exit_code, reason):
        SDNOTIFY_OBJECT.notify("STATUS=Shutting down...")
        SDNOTIFY_OBJECT.notify("WATCHDOG=1")
        SDNOTIFY_OBJECT.notify("STOPPING=1")

        message = (
            "Exiting with exit_code '"
            + str(exit_code)
            + "' because or reason '"
            + reason
            + "'."
        )
        LOGGER.info(message)

        icon = "error"
        message = "sdwdate stopped by user or system."
        stripped_message = self.strip_html(message)
        self.write_status(icon, message)

        self.kill_sclockadj()
        self.kill_sleep_process()

        # use missing_ok=True in python 3.8
        if os.path.isfile(self.sleep_long_file_path):
            os.remove(self.sleep_long_file_path)

        LOGGER.info(stripped_message)
        sys.exit(exit_code)

    @staticmethod
    def strip_html(message):
        # New line for log.
        tmp_message = re.sub("<br>", "\n", message)
        # Strip remaining HTML.
        return re.sub("<[^<]+?>", "", tmp_message)

    def write_status(self, icon, msg):
        self.status["icon"] = icon
        self.status["message"] = msg
        try:
            with open(self.status_file_path, "w") as file_object:
                json.dump(self.status, file_object)
                file_object.close()
        except BaseException:
            error_msg = "Unexpected error: " + str(sys.exc_info()[0])
            print(error_msg)
            return

        with open(self.msg_path, "w") as msgf:
            msgf.write(msg)
            msgf.close()

    @staticmethod
    def time_human_readable(unixtime):
        human_readable_unixtime = datetime.strftime(
            datetime.fromtimestamp(unixtime), "%Y-%m-%d %H:%M:%S"
        )
        return human_readable_unixtime

    def preparation(self):
        message = ""
        previous_messsage = ""
        loop_counter = 0
        loop_max = 10000
        preparation_sleep_seconds = 0
        while True:
            SDNOTIFY_OBJECT.notify("WATCHDOG=1")
            if loop_counter >= loop_max:
                loop_counter = 0
            loop_counter += 1
            msg = (
                "STATUS=Running sdwdate preparation loop. \
                preparation_sleep_seconds: " +
                str(preparation_sleep_seconds) +
                " iteration: " +
                str(loop_counter) +
                " / " +
                str(loop_max))
            SDNOTIFY_OBJECT.notify(msg)

            # Wait one second after first failure. Two at second failure etc.
            # Up to a maximum of ten seconds wait between attempts.
            # The rationale behind this is to be quick at boot time while not
            # stressing the system.
            preparation_sleep_seconds += 1
            if preparation_sleep_seconds >= 10:
                preparation_sleep_seconds = 10

            preparation_path = "/usr/lib/helper-scripts/onion-time-pre-script"
            preparation_status = subprocess.Popen(
                preparation_path, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)

            stdout, stderr = preparation_status.communicate()
            preparation_status.kill()
            output_stdout = stdout.decode("UTF-8")
            output_stderr = stderr.decode("UTF-8")
            joint_message = output_stderr + "\n" + output_stdout

            if preparation_status.returncode == 0:
                LOGGER.info("PREPARATION:")
                message = joint_message.strip()
                LOGGER.info(self.strip_html(message))
                LOGGER.info("PREPARATION RESULT: SUCCESS.")
                LOGGER.info("\n")
                return True

            if joint_message == previous_messsage:
                # No new message. No status changes.
                # Therefore do not reset wait counter and wait
                # preparation_sleep_seconds.
                time.sleep(preparation_sleep_seconds)
                continue

            previous_messsage = joint_message

            LOGGER.info("PREPARATION:")
            message = joint_message.strip()
            LOGGER.info(self.strip_html(joint_message))

            if preparation_status.returncode == 1:
                icon = "error"
                LOGGER.info("PREPARATION RESULT: (known) ERROR.")
            elif preparation_status.returncode == 2:
                icon = "busy"
                LOGGER.info("PREPARATION RESULT: WAIT.")
            else:
                icon = "error"
                LOGGER.info("PREPARATION RESULT: (unknown) ERROR.")

            LOGGER.info("\n")
            # https://phabricator.whonix.org/T534#15429
            main_message = "Preparation not done yet. More more information, \
            see: sdwdate-gui -> right click -> Open sdwdate's log"

            self.write_status(icon, main_message)

            # Different message. Probably progress was made.
            # More progress to be expected.
            # Therefore reset wait counter to just wait a short time.
            preparation_sleep_seconds = 1
            time.sleep(preparation_sleep_seconds)

    @staticmethod
    def general_timeout_error(pools):
        """
        This error occurs (at least) when internet connection is down.
        """
        returned_error = "timeout"
        if (
                pools[0] == returned_error
                and pools[1] == returned_error
                and pools[2] == returned_error
        ):
            return True
        return False

    def check_remote(self, remote, stdout, stderr, took_time, comment, i):
        """
        Check returned stdout. True if numeric.
        """
        remote_number = str(i)
        message = "remote " + remote_number + ": " + remote
        LOGGER.info(message)

        message = "* comment: " + comment
        LOGGER.info(message)

        half_took_time_float = float(took_time) / 2
        # Round took_time to two digits for better readability.
        # No other reason for rounding.
        half_took_time_float = round(half_took_time_float, 2)

        try:
            remote_unixtime = int(stdout)
            old_unixtime = time.time()
            remote_time = self.time_human_readable(remote_unixtime)
            time_diff_raw_int = int(remote_unixtime) - int(old_unixtime)

            # 1. User's sdwdate sends request to remote time source.
            # 2. Server creates reply (HTTP DATE header).
            # 3. Server sends reply back to user's sdwdate.
            # Therefore assume that half of the time required to get the time
            # reply has to be deducted from the raw time diff.
            time_diff_lag_cleaned_float = (
                float(time_diff_raw_int) - half_took_time_float
            )
            time_diff_lag_cleaned_float = \
                round(time_diff_lag_cleaned_float, 2)
        except BaseException:
            message = "* status: False"
            LOGGER.info(message)
            message = "* took_time     : " + str(took_time) + " second(s)"
            LOGGER.info(message)
            message = "* stdout: " + str(stdout)
            LOGGER.info(message)
            message = "* stderr: " + str(stderr)
            LOGGER.info(message)
            LOGGER.info("")
            time_diff_lag_cleaned_float = 0.0
            return False, half_took_time_float, time_diff_lag_cleaned_float

        timesanitycheck_status_static, \
            timesanitycheck_error_static = \
            static_time_sanity_check(remote_unixtime)

        consensus_status, \
            consensus_error, \
            consensus_valid_after_str, \
            consensus_valid_until_str = \
            time_consensus_sanity_check(remote_unixtime)

        message = "* took_time     : " + str(took_time) + " second(s)"
        LOGGER.info(message)
        message = "* half_took_time: " + \
            str(half_took_time_float) + " second(s)"
        LOGGER.info(message)
        message = "* stderr: " + str(stderr)
        LOGGER.info(message)

        message = (
            "* replay_protection_unixtime: "
            + self.time_replay_protection_minium_unixtime_str
        )
        LOGGER.info(message)
        message = "* remote_unixtime           : " + str(remote_unixtime)
        LOGGER.info(message)

        message = "* consensus/valid-after           : " + \
            consensus_valid_after_str
        LOGGER.info(message)
        message = (
            "* replay_protection_time          : "
            + self.time_replay_protection_minium_unixtime_human_readable
        )
        LOGGER.info(message)
        message = "* remote_time                     : " + remote_time
        LOGGER.info(message)
        message = "* consensus/valid-until           : " + \
            consensus_valid_until_str
        LOGGER.info(message)

        message = "* time_diff_raw        : " + \
            str(time_diff_raw_int) + " second(s)"
        LOGGER.info(message)
        message = (
            "* time_diff_lag_cleaned: "
            + str(time_diff_lag_cleaned_float)
            + " second(s)"
        )
        LOGGER.info(message)

        # Fallback.
        remote_status = "fallback"

        if timesanitycheck_status_static == "sane":
            message = "* Time Replay Protection         : sane"
            LOGGER.info(message)
        elif timesanitycheck_status_static == "slow":
            message = "* Time Replay Protection         : slow"
            LOGGER.info(message)
            remote_status = "False"
        elif timesanitycheck_status_static == "fast":
            message = "* Time Replay Protection         : fast"
            LOGGER.info(message)
            remote_status = "False"
        elif timesanitycheck_status_static == "error":
            message = (
                "* Static Time Sanity Check       : error:"
                + timesanitycheck_error_static
            )
            LOGGER.info(message)
            remote_status = "False"

        if consensus_status == "ok":
            message = "* Tor Consensus Time Sanity Check: sane"
            LOGGER.info(message)
            if not remote_status == "False":
                remote_status = "True"
        elif consensus_status == "slow":
            message = "* Tor Consensus Time Sanity Check: slow"
            LOGGER.info(message)
            remote_status = "False"
        elif consensus_status == "fast":
            message = "* Tor Consensus Time Sanity Check: fast"
            LOGGER.info(message)
            remote_status = "False"
        elif consensus_status == "error":
            message = "* Tor Consensus Time Sanity Check: error: " + \
                consensus_error
            LOGGER.info(message)
            remote_status = "False"

        message = "* remote_status: " + str(remote_status)
        LOGGER.info(message)
        LOGGER.info("")

        if remote_status == "True":
            return True, half_took_time_float, time_diff_lag_cleaned_float

        return False, half_took_time_float, time_diff_lag_cleaned_float

    def get_comment(self, remote):
        """ For logging the comments, get the index of the url
            to get it from pool.comment.
        """
        url_comment = "unknown-comment"
        for pool in self.pools:
            try:
                url_index = pool.url.index(remote)
                url_comment = pool.comment[url_index]
                break
            except BaseException:
                pass
        return url_comment

    def build_median(self):
        """
        Get the median (not average) from the list of values.
        """
        sorted_request_took_times = sorted(self.request_took_times.values())
        sorted_request_half_took_times = sorted(
            self.half_took_time_float.values())
        diffs_raw = sorted(self.pools_raw_diff)
        diffs_lag_cleaned = sorted(self.pools_lag_cleaned_diff)
        message = "     request_took_times, sorted: %s" % \
            sorted_request_took_times
        LOGGER.info(message)
        message = "request_half_took_times, sorted: %s" % \
            sorted_request_half_took_times
        LOGGER.info(message)
        message = "          time_diff_raw, sorted: %s" % \
            diffs_raw
        LOGGER.info(message)
        message = "      diffs_lag_cleaned, sorted: %s" % \
            diffs_lag_cleaned
        LOGGER.info(message)
        median_took_times = sorted_request_took_times[
            (len(sorted_request_took_times) // 2)
        ]
        median_half_took_times = sorted_request_half_took_times[
            (len(sorted_request_half_took_times) // 2)
        ]
        self.median_diff_raw_in_seconds = diffs_raw[(len(diffs_raw) // 2)]
        self.median_diff_lag_cleaned_in_seconds = diffs_lag_cleaned[
            (len(diffs_lag_cleaned) // 2)
        ]
        message = "median          request_took_times: %+.9f" % \
            median_took_times
        LOGGER.info(message)
        message = "median     half_request_took_times: %+.9f" % \
            median_half_took_times
        LOGGER.info(message)
        message = (
            "median         raw time difference: %+.9f"
            % self.median_diff_raw_in_seconds
        )
        LOGGER.info(message)
        message = (
            "median lag_cleaned time difference: %+.9f"
            % self.median_diff_lag_cleaned_in_seconds
        )
        LOGGER.info(message)

    @staticmethod
    def time_replay_protection_file_read():
        process = subprocess.Popen(
            "/usr/bin/minimum-unixtime-show",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate()
        unixtime = int(stdout)
        time_human_readable = stderr.decode("utf-8")
        # Relay check to avoid false-positives due to sdwdate inaccuracy.
        unixtime = unixtime - 100
        return unixtime, time_human_readable

    def time_replay_protection_file_write(self):
        time_now_utc_unixtime = time.time()
        # Example time_now_utc_unixtime:
        # 1611095028.9596722
        # This is more difficult to work with.
        # Hence rounding and converting to integer.
        time_now_utc_unixtime = round(time_now_utc_unixtime)
        time_now_utc_unixtime = int(time_now_utc_unixtime)
        # Example time_now_utc_unixtime:
        # 1611095028
        with open(self.sdwdate_time_replay_protection_utc_unixtime, "w") \
                as trpuu:
            message = (
                "Time Replay Protection: write "
                + str(time_now_utc_unixtime)
                + " to file: "
                + self.sdwdate_time_replay_protection_utc_unixtime
            )
            LOGGER.info(message)
            trpuu.write(str(time_now_utc_unixtime))
            trpuu.close()
        with open(
            self.sdwdate_time_replay_protection_utc_humanreadable, "w"
        ) as trpuh:
            time_now_utc_human_readable = self.time_human_readable(
                time_now_utc_unixtime
            )
            message = (
                "Time Replay Protection: write "
                + str(time_now_utc_human_readable)
                + " to file: "
                + self.sdwdate_time_replay_protection_utc_humanreadable
            )
            LOGGER.info(message)
            trpuh.write(str(time_now_utc_human_readable))
            trpuh.close()

    def set_new_time(self):
        status_first_success = os.path.exists(self.status_first_success_path)
        clock_jump_do = os.path.exists(self.clock_jump_do_once_file)

        old_unixtime_float = time.time()
        old_unixtime_int = round(old_unixtime_float)
        old_unixtime_int = int(old_unixtime_int)
        old_unixtime_str = format(old_unixtime_float, ".9f")

        new_unixtime_float = float(
            old_unixtime_float) + float(self.new_diff_in_seconds)
        new_unixtime_int = round(new_unixtime_float)
        new_unixtime_int = int(new_unixtime_int)
        new_unixtime_str = format(new_unixtime_float, ".9f")

        old_unixtime_human_readable = self.time_human_readable(
            old_unixtime_int)
        new_unixtime_human_readable = self.time_human_readable(
            new_unixtime_int)

        message = ("replay_protection_unixtime: " +
                   self.time_replay_protection_minium_unixtime_str)
        LOGGER.info(message)
        message = "old_unixtime              : " + old_unixtime_str
        LOGGER.info(message)
        message = "new_unixtime              : " + new_unixtime_str
        LOGGER.info(message)
        message = (
            "replay_protection_time          : "
            + self.time_replay_protection_minium_unixtime_human_readable
        )
        LOGGER.info(message)
        message = "old_unixtime_human_readable     : " + \
            old_unixtime_human_readable
        LOGGER.info(message)
        message = "new_unixtime_human_readable     : " + \
            new_unixtime_human_readable
        LOGGER.info(message)

        if new_unixtime_int < self.time_replay_protection_minium_unixtime_int:
            message = "Time Replay Protection: ERROR. \
            See above. new_unixtime earlier than \
            time_replay_protection_minium_unixtime_int."
            LOGGER.error(message)
            message = "Time Replay Protection: ERROR. More more information, \
            see: sdwdate-gui -> right click -> Open sdwdate's log"
            return False, message

        if not status_first_success:
            self.set_time_using_date(new_unixtime_str)
        elif clock_jump_do:
            self.set_time_using_date(new_unixtime_str)
        else:
            self.run_sclockadj()

        if not status_first_success:
            file_object = open(self.status_first_success_path, "w")
            file_object.close()

        if clock_jump_do:
            # use missing_ok=True in python 3.8
            if os.path.isfile(self.clock_jump_do_once_file):
                os.remove(self.clock_jump_do_once_file)

        file_object = open(self.status_success_path, "w")
        file_object.close()
        message = "ok"
        return True, message

    @staticmethod
    def randomize_time_config():
        status = False
        if not os.path.exists("/etc/sdwdate.d/"):
            return status
        files = sorted(glob.glob("/etc/sdwdate.d/*.conf"))
        for file_item in files:
            with open(file_item) as conf:
                lines = conf.readlines()
                for line in lines:
                    if line.startswith("RANDOMIZE_TIME=true"):
                        status = True
                    if line.startswith("RANDOMIZE_TIME=false"):
                        status = False
        return status

    def add_or_subtract_nanoseconds(self):
        if self.randomize_time_config():
            LOGGER.info("Randomizing nanoseconds.")
            nanoseconds = randint(0, self.range_nanoseconds)
            sign = randint(0, 1)
            seconds_to_add_or_subtract = (
                float(nanoseconds) / 1000000000
            )
            if sign == 1:
                seconds_to_add_or_subtract = seconds_to_add_or_subtract * -1
            message = (
                "randomize                         : %+.9f" %
                seconds_to_add_or_subtract)
            LOGGER.info(message)
        else:
            LOGGER.info("Not randomizing nanoseconds.")
            # nanoseconds = 0
            seconds_to_add_or_subtract = 0

        # Consumed by set_time_using_date.
        self.new_diff_in_seconds = (
            self.median_diff_raw_in_seconds + seconds_to_add_or_subtract
        )
        # self.new_diff_in_seconds = (
        # self.median_diff_lag_cleaned_in_seconds + \
        # seconds_to_add_or_subtract
        # )

        # Consumed by run_sclockadj.
        self.new_diff_in_nanoseconds = self.new_diff_in_seconds * 1000000000
        self.new_diff_in_nanoseconds = int(self.new_diff_in_nanoseconds)

        message = "new time difference               : %+.9f" % \
            self.new_diff_in_seconds
        LOGGER.info(message)

    def run_sclockadj(self):
        if self.new_diff_in_seconds == 0:
            message = "Time difference = 0. Not setting time."
            LOGGER.info(message)
            return
        sclockad_cmd = ('/usr/lib/sdwdate/sclockadj "' +
                        str(self.new_diff_in_nanoseconds) + '"')
        message = (
            "Gradually adjusting the time by running sclockadj using command: %s" %
            sclockad_cmd)
        LOGGER.info(message)
        # Run sclockadj in a subshell.
        self.sclockadj_process = Popen(sclockad_cmd, shell=True)
        message = (
            "Launched sclockadj into the background. PID: %s"
            % self.sclockadj_process.pid
        )
        LOGGER.info(message)

    def kill_sclockadj(self):
        try:
            self.sclockadj_process.kill()
            message = "Terminated sclockadj process."
            LOGGER.info(message)
        except BaseException:
            message = "sclockadj process not running, ok."
            LOGGER.info(message)

    def kill_sleep_process(self):
        try:
            self.sleep_process.kill()
            message = "Terminated sleep process."
            LOGGER.info(message)
        except BaseException:
            message = "sleep process not running, ok."
            LOGGER.info(message)

    def set_time_using_date(self, new_unixtime_str):
        if self.new_diff_in_seconds == 0:
            message = "Time difference = 0. Not setting time."
            LOGGER.info(message)
            return

        # Set new time.
        cmd = (
            '/bin/date --utc "+%Y-%m-%d %H:%M:%S" --set "@'
            + str(new_unixtime_str)
            + '"'
        )
        message = "Instantly setting the time by using command: %s" % cmd
        LOGGER.info(message)

        bin_date_status = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = bin_date_status.communicate()
        bin_date_status.kill()
        output_stdout = stdout.decode("UTF-8")
        output_stderr = stderr.decode("UTF-8")
        joint_message = output_stdout + " " + output_stderr
        message = "/bin/date output: %s" % joint_message
        LOGGER.info(message)

        if bin_date_status.returncode != 0:
            message = "/bin/date returncode: %s" % str(
                bin_date_status.returncode)
            LOGGER.error(message)
            reason = "bin_date_status non-zero exit code"
            exit_code = 1
            self.exit_handler(exit_code, reason)

    def sdwdate_fetch_loop(self):
        """
        Check remotes.
        Pick a random url in each pool, check the returned stdout.
        Append valid urls if time is returned, otherwise restart a cycle
        with a new random url, until every pool has a time value.
        returns:
        icon, status, message
        """
        message = "Start fetching remote times."
        LOGGER.info(message)

        fetching_msg = self.translate_object("fetching")
        restricted_msg = self.translate_object("restricted")

        # message = "restricted_msg: " + restricted_msg
        # LOGGER.info(message)
        # restricted_msg: Initial time fetching in progress...

        status_first_success = os.path.exists(self.status_first_success_path)

        if not status_first_success:
            icon = "busy"
            self.write_status(icon, restricted_msg)
            message = self.strip_html(restricted_msg)
            LOGGER.info(message)
        else:
            icon = "success"
            self.write_status(icon, fetching_msg)
            message = self.strip_html(fetching_msg)
            LOGGER.info(message)

        while True:
            self.iteration += 1
            message = "Running sdwdate fetch loop. iteration: %s" % self.iteration
            LOGGER.info(message)

            # Clear the lists.
            self.list_of_urls_returned[:] = []
            self.list_of_url_random_requested[:] = []

            for pool in self.pools:
                if pool.done:
                    continue
                pool_size = len(pool.url)
                while True:
                    url_index = random.randrange(0, pool_size)
                    # print("pool_size: " + str(pool_size))
                    if url_index not in pool.already_picked_index:
                        # print("AAA str(len(pool.already_picked_index)): " \
                        # + \
                        # str(len(pool.already_picked_index)))
                        pool.already_picked_index.append(url_index)
                        break
                    if len(pool.already_picked_index) >= pool_size:
                        # print("BBB str(len(pool.already_picked_index)): " \
                        # + \
                        # str(len(pool.already_picked_index)))
                        pool_number = self.pools.index(pool)
                        message = (
                            "pool "
                            + str(pool_number)
                            + ": "
                            + self.translate_object("no_valid_time")
                            + self.translate_object("restart")
                        )
                        icon = "error"
                        status = "error"
                        return icon, status, message
                    # if url_index in pool.already_picked_index:
                        # print("CCC str(len(pool.already_picked_index)): " \
                        # + \
                        # str(len(pool.already_picked_index)))
                already_picked_number = len(pool.already_picked_index)

                message = (
                    "pool "
                    + str(self.pools.index(pool))
                    + ": pool_size: "
                    + str(pool_size)
                    + " url_index: "
                    + str(url_index)
                    + " already_picked_number: "
                    + str(already_picked_number)
                    + " already_picked_index: "
                    + str(pool.already_picked_index)
                )
                LOGGER.info(message)

                pool.url_random_pool.append(pool.url[url_index])
                self.list_of_url_random_requested.append(pool.url[url_index])

            if len(self.list_of_url_random_requested) <= 0:
                message = self.translate_object(
                    "list_not_built") + self.translate_object("restart")
                icon = "error"
                status = "error"
                return icon, status, message

            message = "requested urls %s" % self.list_of_url_random_requested
            LOGGER.info(message)

            self.list_of_urls_returned, \
                self.list_of_stdout, \
                self.list_of_stderr, \
                self.list_of_took_time, \
                self.list_of_timeout_status, \
                self.list_of_exit_codes, \
                = get_time_from_servers(
                    self.list_of_url_random_requested,
                    self.proxy_ip,
                    self.proxy_port
                )

            if self.list_of_urls_returned == []:
                message = self.translate_object(
                    "no_value_returned") + self.translate_object("restart")
                icon = "error"
                status = "error"
                return icon, status, message

            message = 'returned urls "%s"' % self.list_of_urls_returned
            LOGGER.info(message)
            LOGGER.info("")

            for i in range(len(self.list_of_urls_returned)):
                returned_url_item_url = self.list_of_urls_returned[i]
                returned_url_item_stdout = self.list_of_stdout[i]
                returned_url_item_stderr = self.list_of_stderr[i]
                returned_url_item_took_time = self.list_of_took_time[i]
                # returned_url_item_took_timeout_status = \
                #     self.list_of_timeout_status[i]
                returned_url_item_comment = self.get_comment(
                    returned_url_item_url)

                # Example returned_url_item_url:
                # http://tinhat233xymse34.onion

                status_from_check_remote, \
                    took_time_half_float, \
                    lag_cleaned_time_diff_float = \
                    self.check_remote(
                        returned_url_item_url,
                        returned_url_item_stdout,
                        returned_url_item_stderr,
                        returned_url_item_took_time,
                        returned_url_item_comment,
                        i,
                    )

                if status_from_check_remote:
                    self.request_unixtimes[
                        returned_url_item_url
                    ] = returned_url_item_stdout
                    self.request_took_times[
                        returned_url_item_url
                    ] = returned_url_item_took_time
                    self.valid_urls.append(returned_url_item_url)
                    self.unixtimes.append(returned_url_item_stdout)
                    self.half_took_time_float[returned_url_item_url] = took_time_half_float
                    self.time_diff_lag_cleaned_float[returned_url_item_url] \
                        = \
                        lag_cleaned_time_diff_float
                else:
                    self.failed_urls.append(returned_url_item_url)

            if self.iteration >= 2:
                if len(self.list_of_stdout) >= 3:
                    if self.general_timeout_error(self.list_of_timeout_status):
                        message = self.translate_object(
                            "general_timeout_error")
                        icon = "error"
                        status = "error"
                        return icon, status, message

            message = ""
            message += "failed_urls: "
            message += str(len(self.failed_urls))
            message += " allowed_failures: "
            message += str(self.allowed_failures)
            LOGGER.info(message)
            if len(self.failed_urls) > self.allowed_failures:
                message = "Maximum allowed number of failures. Giving up."
                icon = "error"
                status = "error"
                return icon, status, message

            old_unixtime = time.time()

            for pool in self.pools:
                if pool.done:
                    continue
                for url in pool.url_random_pool:
                    pool.done = url in self.valid_urls
                    if pool.done:
                        pool_number = self.pools.index(pool)

                        # Values are returned randomly. Get the index of the
                        # url.
                        web_unixtime = self.request_unixtimes[url]
                        web_unixtime = int(web_unixtime)
                        request_took_time_item = self.request_took_times[url]
                        web_time = self.time_human_readable(web_unixtime)

                        pool_diff = int(web_unixtime) - int(old_unixtime)
                        self.pools_raw_diff.append(pool_diff)

                        # Rounding. Nanoseconds accuracy is impossible.
                        # It is unknown if the time (seconds) reported by
                        # remote servers was a
                        # "early second" (0.000000000) or
                        # "late second" (0.999999999).
                        time_diff_lag_cleaned_int = round(
                            self.time_diff_lag_cleaned_float[url]
                        )
                        self.pools_lag_cleaned_diff.append(
                            time_diff_lag_cleaned_int)

                        message = ""
                        message += "pool " + str(pool_number)
                        message += ": " + url + ", "
                        message += "web_time: " + web_time + ","
                        message += " took_time: "
                        message += str(request_took_time_item)
                        message += " seconds,"
                        message += " time_diff_raw: " + str(pool_diff)
                        message += " seconds,"
                        message += " time_diff_lag_cleaned: "
                        message += str(time_diff_lag_cleaned_int) + " seconds"
                        LOGGER.info(message)

            # message = "len(self.valid_urls): " + str(len(self.valid_urls))
            # LOGGER.info(message)
            if len(self.valid_urls) >= self.number_of_pools:
                break

        message = "End fetching remote times."
        LOGGER.info(message)
        LOGGER.info("")

        message = self.translate_object("success")
        icon = "success"
        status = "success"
        return icon, status, message

    def wait_sleep(self, icon, message):
        # If we make the sleep period configurable one day, we need to
        # advice the user to also adjust WatchdogSec= in sdwdate's systemd
        # unit file.
        # minimum sleep time: 60 minutes
        sleep_time_minimum_seconds = 60 * 60
        # maximum sleep time: 180 minutes
        sleep_time_maximum_seconds = 180 * 60
        self.sleep_time_seconds = randint(
            sleep_time_minimum_seconds, sleep_time_maximum_seconds
        )
        sleep_time_minutes = self.sleep_time_seconds / 60
        sleep_time_minutes_rounded = round(sleep_time_minutes)

        message = (
            message
            + " "
            + self.translate_object("sleeping")
            + str(sleep_time_minutes_rounded)
            + self.translate_object("minutes")
        )

        stripped_message = self.strip_html(message)
        self.write_status(icon, message)

        if icon == "success":
            # LOGGER.info("wait_sleep: icon: success")
            LOGGER.info(stripped_message)
        elif icon == "busy":
            LOGGER.error("wait_sleep: icon: busy")
            LOGGER.error(stripped_message)
        elif icon == "error":
            # LOGGER.info("wait_sleep: icon: error")
            LOGGER.error(stripped_message)
        else:
            LOGGER.error("wait_sleep: icon:else")
            LOGGER.error(stripped_message)

        SDNOTIFY_OBJECT.notify("WATCHDOG=1")

        nanoseconds = randint(0, self.range_nanoseconds)

        if self.sleep_time_seconds >= 10:
            file_object = open(self.sleep_long_file_path, "w")
            file_object.close()

        self.unixtime_before_sleep = int(time.time())

        # Using sh sleep in place of
        # python's time.sleep(self.sleep_time_seconds).
        # The latter uses the system clock for its inactive state time.
        # It becomes utterly confused when sclockadj is running.
        sleep_cmd = ("sleep" +
                     " " +
                     str(self.sleep_time_seconds) +
                     "." +
                     str(nanoseconds))
        message = "running command: " + sleep_cmd
        LOGGER.info(message)
        self.sleep_process = Popen(sleep_cmd, shell=True)
        self.sleep_process.wait()

    def check_clock_skew(self):
        unixtime_after_sleep = int(time.time())
        time_delta = unixtime_after_sleep - self.unixtime_before_sleep
        time_passed = self.sleep_time_seconds - time_delta

        if time_passed > 2:
            time_no_unexpected_change = False
        elif time_passed < -2:
            time_no_unexpected_change = False
        else:
            time_no_unexpected_change = True

        if time_no_unexpected_change:
            message = "Slept for about " + str(time_delta) + " seconds."
            LOGGER.info(message)
        else:
            message = (
                "Clock got changed by something other than sdwdate. \
                sleep_time_seconds: " +
                str(
                    self.sleep_time_seconds) +
                " time_delta: " +
                str(time_delta) +
                " time_passed: " +
                str(time_passed))
            LOGGER.warning(message)


def main():
    global LOGGER
    LOGGER = logging.getLogger("sdwdate")
    LOGGER.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    LOGGER.addHandler(console_handler)

    my_pid = os.getpid()
    pid_message = "sdwdate started. PID: %s" % my_pid
    LOGGER.info(pid_message)

    sdwdate = Sdwdate()

    if os.geteuid() == 0:
        do_not_run_as_root_message = "Exit error... \
        sdwdate should not be run as root!"
        LOGGER.error(do_not_run_as_root_message)
        reason = "sdwdate should not be run as root."
        exit_code = 1
        sdwdate.exit_handler(exit_code, reason)

    signal.signal(signal.SIGTERM, sdwdate.signal_handler)
    signal.signal(signal.SIGINT, sdwdate.signal_handler)

    proxy_message = "Tor socks host: %s Tor socks port: %s" % (
        sdwdate.proxy_ip,
        sdwdate.proxy_port,
    )
    LOGGER.info(proxy_message)

    loop_counter = 0
    loop_max = 10000

    while True:
        if loop_counter >= loop_max:
            loop_counter = 0
        loop_counter += 1

        msg = (
            "Running sdwdate main loop. iteration: "
            + str(loop_counter)
            + " / "
            + str(loop_max)
        )
        LOGGER.info(msg)

        sdwdate.preparation()

        msg_for_sdnotify = "STATUS=" + msg
        SDNOTIFY_OBJECT.notify(msg_for_sdnotify)
        SDNOTIFY_OBJECT.notify("WATCHDOG=1")

        # use missing_ok=True in python 3.8
        if os.path.isfile(sdwdate.sleep_long_file_path):
            os.remove(sdwdate.sleep_long_file_path)
        if os.path.isfile(sdwdate.fail_file_path):
            os.remove(sdwdate.fail_file_path)

        sdwdate = Sdwdate()

        # Debugging.
        # pool = TimeSourcePool(0)
        # x = pool.allowed_failures()
        # print("main allowed_failures: " + str(x))
        # sys.exit(0)

        sdwdate_icon_fl, sdwdate_status_fl, sdwdate_message_fl = (
            sdwdate.sdwdate_fetch_loop()
        )

        SDNOTIFY_OBJECT.notify("WATCHDOG=1")

        if sdwdate_status_fl == "success":
            sdwdate.build_median()
            sdwdate.add_or_subtract_nanoseconds()
            status_set_net_time, message_set_new_time = sdwdate.set_new_time()
            if status_set_net_time:
                sdwdate.time_replay_protection_file_write()
            else:
                sdwdate_icon_fl = "error"
                sdwdate_message_fl = message_set_new_time

        if sdwdate_icon_fl == "error":
            file_object = open(sdwdate.fail_file_path, "w")
            file_object.close()

        sdwdate.wait_sleep(
            sdwdate_icon_fl,
            sdwdate_message_fl
        )
        sdwdate.check_clock_skew()
        sdwdate.kill_sclockadj()


if __name__ == "__main__":
    main()
