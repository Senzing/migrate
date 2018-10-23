#! /usr/bin/env python

import json
import os
import time
import unittest

from migrate import transform_add_list_unique_elements, transform_add_dsrc_etype, transform_add_keys, transform_add_list_elements

# -----------------------------------------------------------------------------
# Test_01 - test transform_add_list_unique_elements()
# -----------------------------------------------------------------------------


class Test_01(unittest.TestCase):

    @classmethod
    def setUpClass(self):

        # Create input and output directories.

        self.test_input_directory = "tests/test-01"
        self.test_output_directory = "test-results/test-01"
        if not os.path.exists(self.test_output_directory):
            os.makedirs(self.test_output_directory)

    def setUp(self):

        # Load dictionaries.

        with open("{0}/data/original.json".format(self.test_input_directory)) as original_file:
            self.original_dictionary = json.load(original_file)
        with open("{0}/data/template.json".format(self.test_input_directory)) as template_file:
            self.template_dictionary = json.load(template_file)
        with open("{0}/data/final.json".format(self.test_input_directory)) as final_file:
            self.final_dictionary = json.load(final_file)

    def test_transform_add_list_unique_elements_01(self):

        # Run test.

        result_dictionary = transform_add_list_unique_elements(self.original_dictionary, self.template_dictionary)

        # Output result_dictionary.

        output_filename = "{0}/test-transform-add-list-unique-elements-01-{1}.json".format(self.test_output_directory, int(time.time()))
        with open(output_filename, "w") as output_file:
            json.dump(result_dictionary, output_file, sort_keys=True, indent=4)

        # Check results.

        self.assertDictEqual(result_dictionary, self.final_dictionary, "Dictionaries are not equal")

# -----------------------------------------------------------------------------
# Test_02 - test transform_add_dsrc_etype()
# -----------------------------------------------------------------------------


class Test_02(unittest.TestCase):

    @classmethod
    def setUpClass(self):

        # Create input and output directories.

        self.test_input_directory = "tests/test-02"
        self.test_output_directory = "test-results/test-02"
        if not os.path.exists(self.test_output_directory):
            os.makedirs(self.test_output_directory)

    def setUp(self):

        # Load dictionaries.

        with open("{0}/data/original.json".format(self.test_input_directory)) as original_file:
            self.original_dictionary = json.load(original_file)
        with open("{0}/data/template.json".format(self.test_input_directory)) as template_file:
            self.template_dictionary = json.load(template_file)
        with open("{0}/data/final.json".format(self.test_input_directory)) as final_file:
            self.final_dictionary = json.load(final_file)

    def test_transform_add_dsrc_etype_01(self):

        # Run test.

        result_dictionary = transform_add_dsrc_etype(self.original_dictionary, self.template_dictionary)

        # Output result_dictionary.

        output_filename = "{0}/test-transform-add-dsrc-etype-01-{1}.json".format(self.test_output_directory, int(time.time()))
        with open(output_filename, "w") as output_file:
            json.dump(result_dictionary, output_file, sort_keys=True, indent=4)

        # Check results.

        self.assertDictEqual(result_dictionary, self.final_dictionary, "Dictionaries are not equal")

# -----------------------------------------------------------------------------
# Test_03 - test transform_add_keys()
# -----------------------------------------------------------------------------


class Test_03(unittest.TestCase):

    @classmethod
    def setUpClass(self):

        # Create input and output directories.

        self.test_input_directory = "tests/test-03"
        self.test_output_directory = "test-results/test-03"
        if not os.path.exists(self.test_output_directory):
            os.makedirs(self.test_output_directory)

    def setUp(self):

        # Load dictionaries.

        with open("{0}/data/original.json".format(self.test_input_directory)) as original_file:
            self.original_dictionary = json.load(original_file)
        with open("{0}/data/template.json".format(self.test_input_directory)) as template_file:
            self.template_dictionary = json.load(template_file)
        with open("{0}/data/final.json".format(self.test_input_directory)) as final_file:
            self.final_dictionary = json.load(final_file)

    def test_transform_add_keys_01(self):

        # Run test.

        result_dictionary = transform_add_keys(self.original_dictionary, self.template_dictionary)

        # Output result_dictionary.

        output_filename = "{0}/test-transform-add-keys-01-{1}.json".format(self.test_output_directory, int(time.time()))
        with open(output_filename, "w") as output_file:
            json.dump(result_dictionary, output_file, sort_keys=True, indent=4)

        # Check results.

        self.assertDictEqual(result_dictionary, self.final_dictionary, "Dictionaries are not equal")

# -----------------------------------------------------------------------------
# Test_04 - test transform_add_list_elements()
# -----------------------------------------------------------------------------


class Test_04(unittest.TestCase):

    @classmethod
    def setUpClass(self):

        # Create input and output directories.

        self.test_input_directory = "tests/test-04"
        self.test_output_directory = "test-results/test-04"
        if not os.path.exists(self.test_output_directory):
            os.makedirs(self.test_output_directory)

    def setUp(self):

        # Load dictionaries.

        with open("{0}/data/original.json".format(self.test_input_directory)) as original_file:
            self.original_dictionary = json.load(original_file)
        with open("{0}/data/template.json".format(self.test_input_directory)) as template_file:
            self.template_dictionary = json.load(template_file)
        with open("{0}/data/final.json".format(self.test_input_directory)) as final_file:
            self.final_dictionary = json.load(final_file)

    def test_transform_add_list_elements_01(self):

        # Run test.

        result_dictionary = transform_add_list_elements(self.original_dictionary, self.template_dictionary)

        # Output result_dictionary.

        output_filename = "{0}/test-transform-add-list-elements-01-{1}.json".format(self.test_output_directory, int(time.time()))
        with open(output_filename, "w") as output_file:
            json.dump(result_dictionary, output_file, sort_keys=True, indent=4)

        # Check results.

        self.assertDictEqual(result_dictionary, self.final_dictionary, "Dictionaries are not equal")

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


if __name__ == '__main__':
    unittest.main()
