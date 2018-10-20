#! /usr/bin/env python

# -----------------------------------------------------------------------------
# migrate.py Migration tool for Senzing
# -----------------------------------------------------------------------------

import argparse
import collections
import copy
import json
import os.path
import sys
import time

list_element_unique_keys = {  
    "a": ["b"],
    "c": ["d", "e"],
    "f": ["g", "h", "i"]
}

# -----------------------------------------------------------------------------
# Define argument parser
# -----------------------------------------------------------------------------


def get_parser():
    '''Parse commandline arguments.'''
    parser = argparse.ArgumentParser(prog="migrate", description="Migrate Senzing configuration")
    subparsers = parser.add_subparsers(dest='subcommand', help='sub-command help')

    subparser_1 = subparsers.add_parser('add-dscr-etype', help='Add existing G2_CONFIG.CFG_DSCR and G2_CONFIG.CFG_ETYPE to a new g2config.json template')
    subparser_1.add_argument("--existing-g2config-file", dest="existing_filename", required=True, help="Input file pathname for existing g2config.json configuration file")
    subparser_1.add_argument("--template-g2config-file", dest="template_filename", required=True, help="Input file pathname for the g2config.json configuration template")
    subparser_1.add_argument("--output-file", dest="output_filename", help="Output file pathname")

    subparser_2 = subparsers.add_parser('json-add-keys', help='Add missing JSON keys to a JSON file from a JSON template file')
    subparser_2.add_argument("--existing-file", dest="existing_filename", required=True, help="Input file pathname for existing JSON file")
    subparser_2.add_argument("--template-file", dest="template_filename", required=True, help="Input file pathname for template JSON file")
    subparser_2.add_argument("--output-file", dest="output_filename", help="Output file pathname")

    subparser_3 = subparsers.add_parser('json-add-list-elements', help='Add elements to existing lists')
    subparser_3.add_argument("--existing-file", dest="existing_filename", required=True, help="Input file pathname for existing JSON file")
    subparser_3.add_argument("--template-file", dest="template_filename", required=True, help="Input file pathname for template JSON file")
    subparser_3.add_argument("--output-file", dest="output_filename", help="Output file pathname")

    subparser_4 = subparsers.add_parser('json-pretty-print', help='Sort and pretty print a file of JSON')
    subparser_4.add_argument("--input-file", dest="input_filename", required=True, help="Input file pathname")
    subparser_4.add_argument("--output-file", dest="output_filename", help="Output file pathname")

    subparser_5 = subparsers.add_parser('migrate-g2config-1', help='Migrate g2config.json')
    subparser_5.add_argument("--existing-g2config-file", dest="existing_filename", required=True, help="Input file pathname for existing g2config.json configuration file")
    subparser_5.add_argument("--template-g2config-file", dest="template_filename", required=True, help="Input file pathname for the g2config.json configuration template")
    subparser_5.add_argument("--output-file", dest="output_filename", help="Output file pathname")

    return parser

# -----------------------------------------------------------------------------
# Utility functions
# -----------------------------------------------------------------------------

def keyed_needle_in_haystack(key, needle, haystack):
    result = False
    default_for_missing_value = "!no-key-value!"
    
    # Get the keys that represent the "compound unique key".
    
    needle_keys = list_element_unique_keys.get(key, [])
    
    # Go through the haystack to see if anything matches the "needle".
    
    for haystack_element in haystack:
        
        # Determine if an element from the haystack matches the needle.
        # Assume it matches until a difference is found.
        
        matches = True
        for needle_key in needle_keys:
            needle_key_value = needle.get(needle_key, default_for_missing_value)
            haystack_element_key_value = haystack_element.get(needle_key, default_for_missing_value)
            if needle_key_value != haystack_element_key_value:
                matches = False
        if matches:
            return True
    
    return result

# -----------------------------------------------------------------------------
# transform_* functions
#   Common function signature: result_dictionary = transform_XXX(original, update)
# -----------------------------------------------------------------------------


def transform_add_escr_etype(original_dictionary, update_dictionary):
    ''' Insert G2_CONFIG.CFG_DSRC and G2_CONFIG.CFG_ETYPE into original dictionary.'''
    result_dictionary = copy.deepcopy(original_dictionary)
    result_dictionary["G2_CONFIG"]["CFG_DSRC"] = update_dictionary.get("G2_CONFIG", {}).get("CFG_DSRC", {})
    result_dictionary["G2_CONFIG"]['CFG_ETYPE'] = update_dictionary.get("G2_CONFIG", {}).get("CFG_ETYPE", {})
    return result_dictionary


def transform_add_keys(original_dictionary, update_dictionary):
    ''' The dictionary returned is the original_dictionary
        plus any new default values from the update_dictionary.
        Note: update_dictionary is modified by this function. '''
    for key, value in original_dictionary.items():
        if isinstance(value, collections.Mapping):
            update_dictionary[key] = transform_add_keys(update_dictionary.get(key, {}), value)
        else:
            if key not in update_dictionary:
                update_dictionary[key] = value
    return update_dictionary


def transform_add_list_elements(original_dictionary, update_dictionary):
    ''' Note: the original_directory is modified by this function. '''
    for key, value in update_dictionary.items():
        if isinstance(value, collections.Mapping):
            original_dictionary[key] = transform_add_list_elements(original_dictionary.get(key, {}), value)
        elif isinstance(value, list):
            for list_element in value:
                if list_element not in original_dictionary[key]:
                    original_dictionary[key].append(list_element)
        else:
            original_dictionary[key] = value
    return original_dictionary

def transform_add_list_unique_elements(original_dictionary, update_dictionary):
    ''' Note: the original_directory is modified by this function. '''
    for key, value in update_dictionary.items():
        
        # If a sub-dictionary, recurse.
        
        if isinstance(value, collections.Mapping):
            original_dictionary[key] = transform_add_list_elements(original_dictionary.get(key, {}), value)
        
        # If a list, add missing elements for unique compound keys.
        
        elif isinstance(value, list):
            if key not in original_dictionary:
                original_dictionary[key] = []
            for list_element in value:
                if list_element not in original_dictionary[key]:
                    if not keyed_needle_in_haystack(key, list_element, original_dictionary[key]):
                        original_dictionary[key].append(list_element)
        
        # Else fill in any missing keys.  Do not over-write values.
        
        else:
            if key not in original_dictionary:            
                original_dictionary[key] = value
    return original_dictionary


def transform_replace_values(original_dictionary, update_dictionary):
    ''' The dictionary returned is the original_dictionary
        with values updated from the update_dictionary.
        Note: update_dictionary is modified by this function. '''
    for key, value in original_dictionary.items():
        if isinstance(value, collections.Mapping):
            update_dictionary[key] = transform_add_keys(update_dictionary.get(key, {}), value)
        else:
            update_dictionary[key] = value
    return update_dictionary

# -----------------------------------------------------------------------------
# do_* functions
#   Common function signature: do_XXX(args)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# add-dscr-etype subcommand
# -----------------------------------------------------------------------------


def do_add_dscr_etype(args):

    # Parse command line arguments.

    existing_filename = args.existing_filename
    template_filename = args.template_filename
    output_filename = args.output_filename or "migrate-add-dscr-etype-{0}.json".format(int(time.time()))

    # Verify existence of files.

    if not os.path.isfile(existing_filename):
        print("Error: --existing-g2config-file {0} does not exist".format(existing_filename))
        sys.exit(1)

    if not os.path.isfile(template_filename):
        print("Error: --template-g2config-file {0} does not exist".format(template_filename))
        sys.exit(1)

    # Load the existing configuration.

    with open(existing_filename) as existing_file:
        existing_dictionary = json.load(existing_file)

    # Load the configuration template.

    with open(template_filename) as template_file:
        template_dictionary = json.load(template_file)

    # Do the transformation.

    result_dictionary = transform_add_escr_etype(existing_dictionary, template_dictionary)

    # Write output.

    with open(output_filename, "w") as output_file:
        json.dump(result_dictionary, output_file, sort_keys=True, indent=4)

    # Epilog.

    print("add-dscr-etype output file: {0}".format(output_filename))

# -----------------------------------------------------------------------------
# json-add-keys subcommand
# -----------------------------------------------------------------------------


def do_json_add_keys(args):

    # Parse command line arguments.

    existing_filename = args.existing_filename
    template_filename = args.template_filename
    output_filename = args.output_filename or "migrate-json-add-keys-{0}.json".format(int(time.time()))

    # Verify existence of files.

    if not os.path.isfile(existing_filename):
        print("Error: --existing-file {0} does not exist".format(existing_filename))
        sys.exit(1)

    if not os.path.isfile(template_filename):
        print("Error: --template-file {0} does not exist".format(template_filename))
        sys.exit(1)

    # Load the existing JSON.

    with open(existing_filename) as existing_file:
        existing_dictionary = json.load(existing_file)

    # Load the JSON template.

    with open(template_filename) as template_file:
        template_dictionary = json.load(template_file)

    # Do the transformation.

    result_dictionary = transform_add_keys(existing_dictionary, template_dictionary)

    # Write output.

    with open(output_filename, "w") as output_file:
        json.dump(result_dictionary, output_file, sort_keys=True, indent=4)

    # Epilog.

    print("json-add-keys output file: {0}".format(output_filename))

# -----------------------------------------------------------------------------
# add-json-keys subcommand
# -----------------------------------------------------------------------------


def do_json_add_list_elements(args):

    # Parse command line arguments.

    existing_filename = args.existing_filename
    template_filename = args.template_filename
    output_filename = args.output_filename or "migrate-json-add-list-elements-{0}.json".format(int(time.time()))

    # Verify existence of files.

    if not os.path.isfile(existing_filename):
        print("Error: --existing-file {0} does not exist".format(existing_filename))
        sys.exit(1)

    if not os.path.isfile(template_filename):
        print("Error: --template-file {0} does not exist".format(template_filename))
        sys.exit(1)

    # Load the existing JSON.

    with open(existing_filename) as existing_file:
        existing_dictionary = json.load(existing_file)

    # Load the JSON template.

    with open(template_filename) as template_file:
        template_dictionary = json.load(template_file)

    # Do the transformation.

    result_dictionary = transform_add_list_elements(existing_dictionary, template_dictionary)

    # Write output.

    with open(output_filename, "w") as output_file:
        json.dump(result_dictionary, output_file, sort_keys=True, indent=4)

    # Epilog.

    print("json-add-list-elements output file: {0}".format(output_filename))

# -----------------------------------------------------------------------------
# json-pretty-print subcommand
# -----------------------------------------------------------------------------


def do_json_pretty_print(args):

    # Parse command line arguments.

    input_filename = args.input_filename
    output_filename = args.output_filename or "migrate-json-pretty-print-{0}.json".format(int(time.time()))

    # Verify existence of file.

    if not os.path.isfile(input_filename):
        print("Error: --input-file {0} does not exist".format(input_filename))
        sys.exit(1)

    # Load the JSON file.

    with open(input_filename) as input_file:
        input_dictionary = json.load(input_file)

    # Write the output JSON file.

    with open(output_filename, "w") as output_file:
        json.dump(input_dictionary, output_file, sort_keys=True, indent=4)

    # Epilog.

    print("json-pretty-print output file: {0}".format(output_filename))

# -----------------------------------------------------------------------------
# migrate-g2config-1 subcommand
# -----------------------------------------------------------------------------


def do_migrate_g2config_1(args):

    # Parse command line arguments.

    existing_filename = args.existing_filename
    template_filename = args.template_filename
    output_filename = args.output_filename or "migrate-migrate-g2config-1-{0}.json".format(int(time.time()))

    # Verify existence of files.

    if not os.path.isfile(existing_filename):
        print("Error: --existing-g2config-file {0} does not exist".format(existing_filename))
        sys.exit(1)

    if not os.path.isfile(template_filename):
        print("Error: --template-g2config-file {0} does not exist".format(template_filename))
        sys.exit(1)

    # Load the existing configuration.

    with open(existing_filename) as existing_file:
        existing_dictionary = json.load(existing_file)

    # Load the new configuration template.

    with open(template_filename) as template_file:
        template_dictionary = json.load(template_file)

    # Do the transformation.
    
#   result_dictionary = transform_add_keys(existing_dictionary, copy.deepcopy(template_dictionary))
    result_dictionary = transform_add_list_unique_elements(existing_dictionary, template_dictionary)

    # Write output.

    with open(output_filename, "w") as output_file:
        json.dump(result_dictionary, output_file, sort_keys=True, indent=4)

    # Epilog.

    print("migrate-g2config-1 output file: {0}".format(output_filename))

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


if __name__ == "__main__":

    # Parse the command line arguments.

    parser = get_parser()
    args = parser.parse_args()
    subcommand = args.subcommand

    # Work-around for issue in python 3.6.

    if not subcommand:
        parser.print_help()
        sys.exit(1)

    # Transform subcommand from CLI parameter to function name string.

    subcommand_function_name = "do_{0}".format(subcommand.replace('-', '_'))

    # Tricky code for calling function based on string.

    globals()[subcommand_function_name](args)
