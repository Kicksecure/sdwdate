#!/usr/bin/env python

import sys
import time
import random
from random import randint
from subprocess import Popen, call, PIPE

from url_to_unixtime import url_to_unixtime
from config import read_pools
#from error_handler import SdwdateError


class Sdwdate():
    def __init__(self):
        self.pool_one, self.pool_two, self.pool_three = read_pools()

        self.range_pool_one = len(self.pool_one)
        self.range_pool_two = len(self.pool_two)
        self.range_pool_three = len(self.pool_three)

        self.number_of_pools = 3

        self.pool_one_done = False
        self.pool_two_done = False
        self.pool_three_done = False

        self.already_picked_index_pool_one = []
        self.already_picked_index_pool_two = []
        self.already_picked_index_pool_three = []

        self.urls = []
        self.url_random = []

        self.url_random_pool_one = []
        self.url_random_pool_two = []
        self.url_random_pool_three = []

        self.valid_urls = []
        self.unixtimes = []
        self.pools_diff = []

        self.invalid_urls = []
        self.url_errors = []

        self.median = 0
        self.range_nanoseconds = 999999999
        self.new_diff = 0
        self.newdiff_nanoseconds = 0

        self.sclockadj_pid = 0

        print 'Start %s' % (time.time())

    def general_proxy_error(self, pools):
        if (pools[0] == 'Connection closed unexpectedly' and
            pools[1] == 'Connection closed unexpectedly' and
            pools[2] == 'Connection closed unexpectedly'):
                ## Raise error, log, user warning.
                print 'General Proxy Error'
                sys.exit(1)

        return False

    def check_remote(self, remote, value):
        try:
            n = int(value)
            print 'check_remote "%s" %s, True' % (remote, value)
            return True
        except ValueError:
            print 'check_remote "%s" %s, False' % (remote, value)
            return False

    def sdwdate_loop(self):
        while len(self.valid_urls) < self.number_of_pools:
            print "MAIN LOOP"
            print 'valid_urls %s' % len(self.valid_urls)
            print 'number_of_pools %s' % self.number_of_pools
            ## Clear the list.
            self.urls[:] = []
            self.url_random[:] = []

            if not self.pool_one_done:
                while True:
                    url_index = []
                    url_index = random.sample(range(self.range_pool_one), 1)
                    index = url_index[0]

                    if len(self.already_picked_index_pool_one) == len(self.pool_one):
                        self.already_picked_index_pool_one = []
                        self.url_random_pool_one = []

                    if url_index not in self.already_picked_index_pool_one:
                        self.already_picked_index_pool_one.append(url_index)
                        print 'pool 1 added %s' % (self.pool_one[url_index[0]])
                        self.url_random_pool_one.append(self.pool_one[url_index[0]])
                        self.url_random.append(self.pool_one[url_index[0]])
                        break

            if not self.pool_two_done:
                while True:
                    url_index = []
                    url_index = random.sample(range(self.range_pool_two), 1)
                    index = url_index[0]

                    if len(self.url_random_pool_two) == len(self.pool_two):
                        self.already_picked_index_pool_two = []
                        self.url_random_pool_two = []

                    if url_index not in self.already_picked_index_pool_two:
                        self.already_picked_index_pool_two.append(url_index)
                        print 'pool 2 added %s' % (self.pool_two[url_index[0]])
                        self.url_random_pool_two.append(self.pool_two[url_index[0]])
                        self.url_random.append(self.pool_two[url_index[0]])
                        break

            if not self.pool_three_done:
                while True:
                    url_index = []
                    url_index = random.sample(range(self.range_pool_three), 1)
                    index = url_index[0]

                    if len(self.url_random_pool_three) == len(self.pool_three):
                        self.already_picked_index_pool_three = []
                        self.url_random_pool_three = []

                    if url_index not in self.already_picked_index_pool_three:
                        self.already_picked_index_pool_three.append(url_index)
                        print 'pool 3 added %s' % (self.pool_three[url_index[0]])
                        self.url_random_pool_three.append(self.pool_three[url_index[0]])
                        self.url_random.append(self.pool_three[url_index[0]])
                        break

            ## Fetch remotes.
            if len(self.url_random) > 0:
                print 'random urls %s' % (self.url_random)
                self.urls, self.returned_values = url_to_unixtime(self.url_random)
                if len(self.urls) == 0:
                    ## Most likely, internet connection is down.
                    ## Raise eror, log.
                    print('No values returned from url_to_unixtime.')
                    sys.exit()
                print 'returned urls "%s"' % (self.urls)
            else:
                ## Add code here.
                sys.exit(1)

            if not self.general_proxy_error(self.returned_values):
                #self.valid_urls = []
                #self.unixtimes = []
                for i in range(len(self.urls)):
                    if self.check_remote(self.urls[i], self.returned_values[i]):
                        self.valid_urls.append(self.urls[i])
                        self.unixtimes.append(self.returned_values[i])

                    else:
                        self.invalid_urls.append(self.urls[i])
                        self.url_errors.append(self.returned_values[i])

            old_unixtime = (time.time())
            print 'old_unixtime %s' % old_unixtime

            if not self.pool_one_done:
                for i in range(len(self.url_random_pool_one)):
                    self.pool_one_done = self.url_random_pool_one[i] in self.valid_urls
                    if self.pool_one_done:
                        valid_url = self.url_random_pool_one[i]
                        ## Values are teturned randomly. Get the index of the url.
                        index = self.valid_urls.index(valid_url)
                        ## Pool matching web time.
                        web_time = self.unixtimes[index]
                        self.pools_diff.append(int(web_time) - int(old_unixtime))
                        print 'pool_one: last_url %s, web_time %s' % (valid_url, web_time)
                print 'pool_one_done %s' % (self.pool_one_done)

            if not self.pool_two_done:
                for i in range(len(self.url_random_pool_two)):
                    self.pool_two_done = self.url_random_pool_two[i] in self.valid_urls
                    if self.pool_two_done:
                        valid_url = self.url_random_pool_two[i]
                        index = self.valid_urls.index(valid_url)
                        web_time = self.unixtimes[index]
                        self.pools_diff.append(int(web_time) - int(old_unixtime))
                        print 'pool_two: last_url %s, web_time %s' % (valid_url, web_time)
                print 'pool_two_done %s' % (self.pool_two_done)

            if not self.pool_three_done:
                for i in range(len(self.url_random_pool_three)):
                    self.pool_three_done = self.url_random_pool_three[i] in self.valid_urls
                    if self.pool_three_done:
                        valid_url = self.url_random_pool_three[i]
                        index = self.valid_urls.index(valid_url)
                        web_time = self.unixtimes[index]
                        self.pools_diff.append(int(web_time) - int(old_unixtime))
                        print 'pool_three: last_url %s, web_time %s' % (valid_url, web_time)
                print 'pool_three_done %s' % (self.pool_three_done)

            print 'valid urls %s' % (self.valid_urls)
        #print 'pools diff %s' % self.pools_diff
        ### Duplicates in bad urls, same url appended because pool not done.
        ### Remove duplicates
        #print 'bad urls %s' % (list(set(self.invalid_urls)))

        print 'End %s' % (time.time())

    def build_median(self):
        diffs = sorted(self.pools_diff)
        print 'sorted %s' % (diffs)
        ## We can have more than three values in valid_urls / pools_diff.
        if len(diffs) % 2 == 0:
            ## Even number of values. Median = sum(2 middle values) / 2
            self.median = (diffs[(len(diffs) / 2) - 1] + diffs[len(diffs) / 2]) / 2
        else:
            ## Odd number of values. Median = middle value.
            self.median = diffs[(len(diffs) / 2)]

    def maybe_set_new_time(self):
        if self.median == 0:
            print('Time difference = 0. Not setting time')
            return False
        else:
            return True

    def add_subtract_nanoseconds(self):
        sign = randint(0, 1)
        nanoseconds = randint(0, self.range_nanoseconds)
        seconds = float(nanoseconds) / 1000000000

        if sign == 0:
            self.new_diff = self.median + seconds
        else:
            self.new_diff = self.median - seconds

        self.newdiff_nanoseconds = int(self.new_diff * 1000000000)

        print 'nanoseconds %s' % nanoseconds
        print 'seconds %s' % seconds
        print 'sign %s' % sign
        print 'median %s' % self.median
        print 'new_diff %s' % self.new_diff

        return True

    def run_sclockadj(self):
        if self.newdiff_nanoseconds > 0:
            add_subtract = "--add"
        else:
            add_subtract = "--subtract"
        cmd = [
            "sudo",
            "INLINEDIR=/var/cache/sdwdate/sclockadj",
            "/usr/lib/sdwdate/sclockadj",
            "--no-debug",
            "--no-verbose",
            "--no-systohc",
            "--no-first-wait",
            "--move-min", "5000000",
            "--move-max", "5000000",
            "--wait-min", "1000000000",
            "--wait-max", "1000000000",
            add_subtract, str(abs(self.newdiff_nanoseconds))]

        ## Run sclockadj in a subshell.
        sclockadj = Popen(cmd)
        self.sclockadj_pid = sclockadj.pid

        ## Running sclockadj_debug_helper, in case...
        ## May be read the last line to ensure sclockadj is running.
        #cmd = ["sudo", "/usr/lib/sdwdate/sclockadj_debug_helper"]
        ### Pipe stdout in subprocess.
        #helper = Popen(cmd, stdout=PIPE)
        ### Read the output.
        #line = helper.stdout.read()
        #print line

    def kill_sclockadj(self):
        cmd = 'sudo /usr/lib/sdwdate/sclockadj_kill_helper ' + str(self.sclockadj_pid)
        call(cmd, shell=True)

    def set_time_using_date(self):
        old_unixtime = time.time()
        print 'Old time %.9f' % (old_unixtime)
        new_unixtime = '%.9f' % (old_unixtime + self.new_diff)
        print 'New time %s' % str(new_unixtime)
        ## Debug: print old date.
        cmd = '/bin/date'
        call(cmd, shell=True)
        ## Set new time.
        cmd = '/bin/date --set @' + str(new_unixtime)
        print cmd
        call(cmd, shell=True)

def main():
    while True:
        sdwdate_ = Sdwdate()
        sdwdate_.sdwdate_loop()
        sdwdate_.build_median()

        if sdwdate_.maybe_set_new_time():
            sdwdate_.add_subtract_nanoseconds()
            sdwdate_.set_time_using_date()

        print 'sleeping..\n\n\n'
        time.sleep(30)

if __name__ == "__main__":
    main()
