#! /usr/bin/env python

# -----------------------------------------------------------------------------
# migrate.py Migration tool for Senzing
# -----------------------------------------------------------------------------

import argparse
import collections
import copy
import filecmp
import json
import logging
import os
import os.path
import re
from shutil import copyfile, copytree
import sys
import time

# This is a dictionary of a list of lists.  Each inner list specifies
# JSON keys whose values, together, must be unique.

list_element_unique_keys = {
    "CFG_ATTR": [["ATTR_CODE"]],
    "CFG_CFBOM": [["CFCALL_ID", "FTYPE_ID", "FELEM_ID"]],
    "CFG_CFCALL": [["CFCALL_ID"], ["FTYPE_ID", "CFUNC_ID"]],
    "CFG_CFRTN": [["CFRTN_ID"], ["CFUNC_ID", "CFUNC_RTNVAL"]],
    "CFG_CFUNC": [["CFUNC_ID"], ["CFUNC_CODE"]],
    "CFG_DFBOM": [["DFCALL_ID", "FTYPE_ID", "FELEM_ID"]],
    "CFG_DFCALL": [["DFCALL_ID"]],
    "CFG_DFUNC": [["DFUNC_ID"], ["DFUNC_CODE"]],
    "CFG_DSRC": [["DSRC_ID"], ["DSRC_CODE"]],
    "CFG_EBOM": [["ETYPE_ID", "EXEC_ORDER"]],
    "CFG_ECLASS": [["ECLASS_ID"], ["ECLASS_CODE"]],
    "CFG_EFBOM": [["EFCALL_ID", "FTYPE_ID", "FELEM_ID"]],
    "CFG_EFCALL": [["EFCALL_ID"]],
    "CFG_EFUNC": [["EFUNC_ID"], ["EFUNC_CODE"]],
    "CFG_ERFRAG": [["ERFRAG_ID"], ["ERFRAG_CODE"]],
    "CFG_ERRULE": [["ERRULE_ID"], ["ERRULE_CODE"]],
    "CFG_ESCORE": [["BEHAVIOR_CODE"]],
    "CFG_ETYPE": [["ETYPE_ID"], ["ETYPE_CODE"]],
    "CFG_FBOM": [["FTYPE_ID", "FELEM_ID"]],
    "CFG_FBOVR": [["FTYPE_ID", "ECLASS_ID", "UTYPE_CODE"]],
    "CFG_FCLASS": [["FCLASS_ID"], ["FCLASS_CODE"]],
    "CFG_FELEM": [["FELEM_ID"], ["FELEM_CODE"]],
    "CFG_FTYPE": [["FTYPE_ID"], ["FTYPE_CODE"]],
    "CFG_GENERIC_THRESHOLD": [["GPLAN_ID", "BEHAVIOR", "FTYPE_ID"]],
    "CFG_GPLAN": [["GPLAN_ID"], ["GPLAN_CODE"]],
    "CFG_LENS": [["LENS_ID"], ["LENS_CODE"]],
    "CFG_RCLASS": [["RCLASS_ID"], ["RCLASS_CODE"]],
    "CFG_RTYPE": [["RTYPE_ID"], ["RTYPE_CODE"]],
    "CFG_SFCALL": [["SFCALL_ID"], ["FTYPE_ID", "SFUNC_ID"]],
    "CFG_SFUNC": [["SFUNC_ID"], ["SFUNC_CODE"]],
    "COMPATIBILITY_VERSION": [],
    "SYS_OOM": [["OOM_TYPE", "OOM_LEVEL", "LENS_ID", "LIB_FEAT_ID", "FELEM_ID", "LIB_FELEM_ID"]]
}

log_file_diff_template = "DiffFile: {0} {1}"

# -----------------------------------------------------------------------------
# Define argument parser
# -----------------------------------------------------------------------------


def get_parser():
    '''Parse commandline arguments.'''
    parser = argparse.ArgumentParser(prog="migrate.py", description="Migrate Senzing configuration")
    subparsers = parser.add_subparsers(dest='subcommand', help='Subcommands:')

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

    subparser_5 = subparsers.add_parser('migrate-g2config', help='Migrate g2config.json')
    subparser_5.add_argument("--existing-g2config-file", dest="existing_filename", required=True, help="Input file pathname for existing g2config.json configuration file")
    subparser_5.add_argument("--template-g2config-file", dest="template_filename", required=True, help="Input file pathname for the g2config.json configuration template")
    subparser_5.add_argument("--output-file", dest="output_filename", help="Output file pathname")

    subparser_6 = subparsers.add_parser('migrate-opt-senzing', help='Migrate /opt/senzing directory by creating a proposal')
    subparser_6.add_argument("--old-opt-senzing", dest="old_senzing_directory", required=True, help="Path to existing /opt/senzing")
    subparser_6.add_argument("--new-opt-senzing", dest="new_senzing_directory", required=True, help="Path to newly created /opt/new-senzing")
    subparser_6.add_argument("--proposed-opt-senzing", dest="proposed_senzing_directory", help="Path to proposed /opt/proposed-senzing")

    return parser

# -----------------------------------------------------------------------------
# Utility functions
# -----------------------------------------------------------------------------


def copy_directory(old, new):
    ''' Copy a complete directory.'''
    if os.path.exists(old):
        logging.info("CopyTree: {0} {1}".format(old, new))
        copytree(old, new)
    else:
        logging.info("Directory {0} does not exist".format(old))


def copy_file(old_file, new_file):
    ''' Copy a file.  Create sub-directories if needed.'''

    if os.path.exists(old_file):

        # Ensure directory exists for proposed file.

        new_file_directory = os.path.dirname(new_file)
        if not os.path.exists(new_file_directory):
            os.makedirs(new_file_directory)

        # Copy file.

        logging.info("CopyFile: {0} {1}".format(old_file, new_file))

        copyfile(old_file, new_file)
    else:
        logging.info("File {0} does not exist".format(old_file))


def handle_directory_diff(directory_diff, old_directory, new_directory, proposed_directory):

    # Copy old file into the proposed directory.

    merged_lists = directory_diff.diff_files + directory_diff.left_only
    for name in merged_lists:
        old_file = "{0}/{1}".format(directory_diff.left, name)
        new_path = re.sub(new_directory, '', directory_diff.right)
        new_file = "{0}/{1}{2}".format(proposed_directory, new_path, name)
        copy_file(old_file, new_file)

    # Recurse into next level of subdirectories.

    for sub_directory_diff in directory_diff.subdirs.values():
        handle_directory_diff(sub_directory_diff, old_directory, new_directory, proposed_directory)


def keyed_needle_in_haystack(key, needle, haystack):
    ''' Determine if a "needle" is in the "haystack". The needle
        is determined by "key" as an index into list_element_unique_keys.'''
    result = False
    default_for_missing_value = "!no-key-value!"

    # Get the keys that represent the "compound unique key".

    unique_keys_list = list_element_unique_keys.get(key, [])
    for unique_keys in unique_keys_list:

        # Go through the haystack to see if anything matches the "needle".

        for haystack_element in haystack:

            # Determine if an element from the haystack matches the needle.
            # Assume it matches until a difference is found.

            matches = True
            for unique_key in unique_keys:
                unique_key_value = needle.get(unique_key, default_for_missing_value)
                haystack_element_key_value = haystack_element.get(unique_key, default_for_missing_value)
                if unique_key_value != haystack_element_key_value:
                    matches = False
            if matches:
                return True

    return result


def safe_list_get (the_list, list_index, default):
    ''' Since a list does not have a list.get() function,
        this is a safe alternative. '''
    try:
        return the_list[list_index]
    except IndexError:
        return default


def files_from_list(files_list, old_directory, new_directory, proposed_directory):
    ''' This is a python generator. '''
    for files in files_list:
        old = safe_list_get(files, 0, "").format(old_directory, new_directory, proposed_directory)
        new = safe_list_get(files, 1, "").format(old_directory, new_directory, proposed_directory)
        proposed = safe_list_get(files, 2, "").format(old_directory, new_directory, proposed_directory)
        yield old, new, proposed


def log_directory_diff(directory_diff):
    ''' Recursively log file difference found.'''

    for name in directory_diff.diff_files:
        old_filename = "{0}/{1}".format(directory_diff.left, name)
        new_filename = "{0}/{1}".format(directory_diff.right, name)
        logging.info(log_file_diff_template.format(old_filename, new_filename))

    for sub_directory_diff in directory_diff.subdirs.values():
        log_directory_diff(sub_directory_diff)


def log_directory_new(directory_diff):
    ''' Recursively log file difference found.'''

    for name in directory_diff.right_only:
        filename = "{0}/{1}".format(directory_diff.right, name)
        logging.info("New-File: {}".format(filename))

    for sub_directory_diff in directory_diff.subdirs.values():
        log_directory_new(sub_directory_diff)


def log_directory_old(directory_diff):
    ''' Recursively log file difference found.'''

    for name in directory_diff.left_only:
        filename = "{0}/{1}".format(directory_diff.left, name)
        logging.info("Old-File: {}".format(filename))

    for sub_directory_diff in directory_diff.subdirs.values():
        log_directory_old(sub_directory_diff)


def log_file(filename, title):
    lines = [line.strip() for line in open(filename)]
    for line in lines:
        logging.info("{0}: {1}: {2}".format(title, filename, line))

# -----------------------------------------------------------------------------
# log_* functions
#   Common function signature: log_XXX(files_list, old_dir, new_dir)
# -----------------------------------------------------------------------------


def log_file_differences(files_list, old_directory, new_directory):
    for old, new, _ in files_from_list(files_list, old_directory, new_directory, "") :
        if not filecmp.cmp(old, new, shallow=False):
            logging.info(log_file_diff_template.format(old, new))


def log_directory_differences(directories_list, old_directory, new_directory, proposed_directory):
    for old, new, proposed in files_from_list(directories_list, old_directory, new_directory, proposed_directory):
        if os.path.exists(old):
            directory_diff = filecmp.dircmp(old, new)
            log_directory_old(directory_diff)
            log_directory_new(directory_diff)
            log_directory_diff(directory_diff)

# -----------------------------------------------------------------------------
# propose_* functions
#   Common function signature: propose_XXX(list, old_dir, new_dir, propose_dir)
# -----------------------------------------------------------------------------


def propose_copy_directories_from_old(directories_list, old_directory, new_directory, proposed_directory):
    for old, new, proposed in files_from_list(directories_list, old_directory, new_directory, proposed_directory):
        copy_directory(old, proposed)


def propose_copy_files_from_old(files_list, old_directory, new_directory, proposed_directory):
    for old, new, proposed in files_from_list(files_list, old_directory, new_directory, proposed_directory):
        copy_file(old, proposed)


def propose_diff_and_copy_directories_from_old(directories_list, old_directory, new_directory, proposed_directory):
    for old, new, proposed in files_from_list(directories_list, old_directory, new_directory, proposed_directory):
        if os.path.exists(old):
            directory_diff = filecmp.dircmp(old, new)
            handle_directory_diff(directory_diff, old, new, proposed)
        else:
            logging.info("Directory {0} does not exist".format(old))


def propose_diff_and_copy_files_from_old(files_list, old_directory, new_directory, proposed_directory):
    for old, new, proposed in files_from_list(files_list, old_directory, new_directory, proposed_directory):
        if not os.path.exists(old):
            pass
        elif not os.path.exists(new):
            copy_file(old, proposed)
        elif not filecmp.cmp(old, new, shallow=False):
            copy_file(old, proposed)


def propose_opt_senzing_g2_python_g2config_json(old_directory, new_directory, proposed_directory):

    # Construct filenames.

    existing_filename = "{0}/g2/python/g2config.json".format(old_directory)
    template_filename = "{0}/g2/data/g2config.json".format(new_directory)
    output_filename = "{0}/g2/python/g2config.json".format(proposed_directory)

    # Create output directory.

    output_directory = "{0}/g2/python".format(proposed_directory)
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Verify existence of files.

    if not os.path.isfile(existing_filename):
        print("Error: {0} does not exist".format(existing_filename))
        sys.exit(1)

    if not os.path.isfile(template_filename):
        print("Error: {0} does not exist".format(template_filename))
        sys.exit(1)

    # Load the existing configuration.

    with open(existing_filename) as existing_file:
        existing_dictionary = json.load(existing_file)

    # Load the new configuration template.

    with open(template_filename) as template_file:
        template_dictionary = json.load(template_file)

    # Do the transformation.

    result_dictionary = transform_add_list_unique_elements(existing_dictionary, template_dictionary)

    # Write output.

    with open(output_filename, "w") as output_file:
        json.dump(result_dictionary, output_file, sort_keys=True, indent=4)

# -----------------------------------------------------------------------------
# transform_* functions
#   Common function signature: result_dictionary = transform_XXX(original, update)
# -----------------------------------------------------------------------------


def transform_add_dsrc_etype(original_dictionary, update_dictionary):
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
    ''' If a list element appears in the update_dictionary, but not in the
        original_dictioary, add it to the original dictionary.
        Note: the original_directory is modified by this function. '''
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
    ''' If a value or list element is in the update dictionary, but not in the
        original_dictionary, determine if it should be added to the original_dictionary.
        Note: the original_directory is modified by this function. '''
    for key, value in update_dictionary.items():

        # If a sub-dictionary, recurse.

        if isinstance(value, collections.Mapping):
            original_dictionary[key] = transform_add_list_unique_elements(original_dictionary.get(key, {}), value)

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

    result_dictionary = transform_add_dsrc_etype(existing_dictionary, template_dictionary)

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
# migrate-g2config subcommand
# -----------------------------------------------------------------------------


def do_migrate_g2config(args):

    # Parse command line arguments.

    existing_filename = args.existing_filename
    template_filename = args.template_filename
    output_filename = args.output_filename or "migrate-migrate-g2config-{0}.json".format(int(time.time()))

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

    result_dictionary = transform_add_list_unique_elements(existing_dictionary, template_dictionary)

    # Write output.

    with open(output_filename, "w") as output_file:
        json.dump(result_dictionary, output_file, sort_keys=True, indent=4)

    # Epilog.

    print("migrate-g2config output file: {0}".format(output_filename))

# -----------------------------------------------------------------------------
# migrate-opt-senzing
# -----------------------------------------------------------------------------


def do_migrate_opt_senzing(args):

    # Parse command line arguments.

    old_directory = args.old_senzing_directory
    new_directory = args.new_senzing_directory
    proposed_directory = args.proposed_senzing_directory or "{0}/proposed-opt-senzing-{1}".format(os.getcwd(), int(time.time()))

    # Verify existence of directories.

    if not os.path.isdir(old_directory):
        print("Error: --old-opt-senzing {0} does not exist".format(old_directory))
        sys.exit(1)

    if not os.path.isdir(new_directory):
        print("Error: --new-opt-senzing {0} does not exist".format(new_directory))
        sys.exit(1)

    if not os.path.exists(proposed_directory):
        os.makedirs(proposed_directory)

    # Log versions

    log_file("{0}/g2/data/g2BuildVersion.txt".format(old_directory), "Old--Dir")
    log_file("{0}/g2/data/g2BuildVersion.txt".format(new_directory), "New--Dir")

    # Log differences

    log_directory_list = [["{0}", "{1}", "{2}"]]
    log_directory_differences(log_directory_list, old_directory, new_directory, proposed_directory)

    # Directory proposals.

#   copy_directories_list = [ ]
#   propose_copy_directories_from_old(copy_directories_list, old_directory, new_directory, proposed_directory)

    diff_directories_list = [
        ["{0}/g2/python/demo", "{1}/g2/python/demo", "{2}/g2/python/demo"]
    ]

    propose_diff_and_copy_directories_from_old(diff_directories_list, old_directory, new_directory, proposed_directory)

    # File proposals

#   copy_files_list = []
#   propose_copy_files_from_old(copy_files_list, old_directory, new_directory, proposed_directory)

    diff_files_list = [
        ["{0}/g2/setupEnv", "{1}/g2/setupEnv", "{2}/g2/setupEnv"],
        ["{0}/g2/python/G2Module.ini", "{1}/g2/python/G2Module.ini", "{2}/g2/python/G2Module.ini"],
        ["{0}/g2/python/G2Project.ini", "{1}/g2/python/G2Project.ini", "{2}/g2/python/G2Project.ini"],
        ["{0}/g2/data/g2.lic", "{1}/g2/data/g2.lic", "{2}/g2/data/g2.lic"],
        ["{0}/g2/sqldb/G2C.db", "{0}/g2/data/G2C.db", "{2}/g2/sqldb/G2C.db"]
    ]

    propose_diff_and_copy_files_from_old(diff_files_list, old_directory, new_directory, proposed_directory)

    # File specific proposals

    propose_opt_senzing_g2_python_g2config_json(old_directory, new_directory, proposed_directory)

    # Epilog.

    logging.info("Proposal: {0}.".format(proposed_directory))

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


if __name__ == "__main__":

    # Configure logging.

    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.DEBUG)

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
