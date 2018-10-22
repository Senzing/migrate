#! /usr/bin/env python

import json
import os
import time
import unittest

from migrate import transform_add_list_unique_elements


class Test_01(unittest.TestCase):

    def setUp(self):
        self.test_directory = "tests/test-01"

        with open(self.test_directory + "/data/original.json") as original_file:
            self.original_dictionary = json.load(original_file)
        with open(self.test_directory + "/data/template.json") as template_file:
            self.template_dictionary = json.load(template_file)
        with open(self.test_directory + "/data/final.json") as final_file:
            self.final_dictionary = json.load(final_file)

    def test_transform_add_list_unique_elements_01(self):

        # Create output directory.

        output_directory = "{0}/results".format(self.test_directory)
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        # Run test.

        result_dictionary = transform_add_list_unique_elements(self.original_dictionary, self.template_dictionary)

        # Output result_dictionary.

        output_filename = "{0}/test-transform-add-list-unique-elements-01-{1}.json".format(output_directory, int(time.time()))
        with open(output_filename, "w") as output_file:
            json.dump(result_dictionary, output_file, sort_keys=True, indent=4)

        # Check results.

        self.assertDictEqual(result_dictionary, self.final_dictionary, "Dictionaries are not equal")


if __name__ == '__main__':
    unittest.main()
