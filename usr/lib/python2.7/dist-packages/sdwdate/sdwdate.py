#!/usr/bin/env python

import sys
import time, random

from url_to_unixtime import url_to_unixtime
from config import read_pools
from error_handler import SdwdateError

class Sdwdate():
    def __init__(self):
        self.pool_one_single, self.pool_two_single, self.pool_three_single, \
        self.pool_one_multi, self.pool_two_multi, self.pool_three_multi = read_pools()

        if len(self.pool_one_multi) > 0:
            self.pool_one = self.pool_one_multi
        else:
            self.pool_one = self.pool_one_single

        if len(self.pool_two_multi) > 0:
            self.pool_two = self.pool_two_multi
        else:
            self.pool_two = self.pool_two_single

        if len(self.pool_one_multi) > 0:
            self.pool_three = self.pool_three_multi
        else:
            self.pool_three = self.pool_three_multi

        self.number_of_pools = 3

        self.pool_one_done = False
        self.pool_two_done = False
        self.pool_three_done = False

        self.already_picked_index_pool_one = []
        self.already_picked_index_pool_two = []
        self.already_picked_index_pool_three = []

        self.url_random_pool_one = []
        self.url_random_pool_two = []
        self.url_random_pool_three = []

        self.valid_urls = []
        self.unixtimes = []

        self.invalid_urls = []
        self.url_errors = []

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
            if True:
                n = int(value)
                print 'check_remote "%s" %s, True' % (remote, value)
                return True
        except ValueError:
            print 'check_remote "%s" %s, False' % (remote, value)
            return False

    def sdwdate_loop(self):
        while len(self.valid_urls) < self.number_of_pools:
            print "MAIN LOOP"
            self.urls = []
            self.url_random = []

            if not self.pool_one_done:
                while True:
                    url_index = []
                    url_index = random.sample(range(len(self.pool_one)), 1)

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
                    url_index = random.sample(range(len(self.pool_two)), 1)

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
                    url_index = random.sample(range(len(self.pool_three)), 1)

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
                print 'returned urls "%s"' % (self.urls)
            else:
                ## Add code here.
                sys.exit(1)

            if not self.general_proxy_error(self.returned_values):
                self.valid_urls = []
                self.unixtimes = []
                for i in range(len(self.urls)):
                    if self.check_remote(self.urls[i], self.returned_values[i]):
                        self.valid_urls.append(self.urls[i])
                        self.unixtimes.append(self.returned_values[i])
                    else:
                        self.invalid_urls.append(self.urls[i])
                        self.url_errors.append(self.returned_values[i])

            if not self.pool_one_done:
                for i in range(len(self.url_random_pool_one)):
                    self.pool_one_done = self.url_random_pool_one[i] in self.valid_urls
                print 'pool_one_done %s' % (self.pool_one_done)

            if not self.pool_two_done:
                for i in range(len(self.url_random_pool_two)):
                    self.pool_two_done = self.url_random_pool_two[i] in self.valid_urls
                print 'pool_two_done %s' % (self.pool_two_done)

            if not self.pool_three_done:
                for i in range(len(self.url_random_pool_three)):
                    self.pool_three_done = self.url_random_pool_three[i] in self.valid_urls
                print 'pool_three_done %s' % (self.pool_three_done)

        print 'valid urls %s' % (self.valid_urls)
        ## Duplicates in bad urls, same url appended because pool not done.
        ## Remove duplicates
        print 'bad urls %s' % (list(set(self.invalid_urls)))

        print 'End %s' % (time.time())

def main():
    sdwdate_ = Sdwdate()
    sdwdate_.sdwdate_loop()

if __name__ == "__main__":
    main()
