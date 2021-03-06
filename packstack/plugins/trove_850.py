# -*- coding: utf-8 -*-

"""
Installs and configures Trove
"""

from packstack.installer import utils
from packstack.installer import validators
from packstack.installer import processors
from packstack.modules.shortcuts import get_mq
from packstack.modules.ospluginutils import (getManifestTemplate,
                                             appendManifestFile,
                                             createFirewallResources)


# ------------------ Trove Packstack Plugin initialization ------------------

PLUGIN_NAME = "OS-Trove"
PLUGIN_NAME_COLORED = utils.color_text(PLUGIN_NAME, 'blue')


# NOVA_USER, NOVA_TENANT, NOVA_PW

def process_trove_nova_pw(param, param_name, config=None):
    if (param == 'PW_PLACEHOLDER' and
            config['CONFIG_TROVE_NOVA_USER'] == 'admin'):
        return config['CONFIG_KEYSTONE_ADMIN_PW']
    else:
        return param


def initConfig(controller):
    parameters = [
        {"CONF_NAME": "CONFIG_TROVE_DB_PW",
         "CMD_OPTION": "trove-db-passwd",
         "PROMPT": "Enter the password to use for Trove to access the DB",
         "USAGE": "The password to use for the Trove DB access",
         "OPTION_LIST": [],
         "VALIDATORS": [validators.validate_not_empty],
         "DEFAULT_VALUE": "PW_PLACEHOLDER",
         "PROCESSORS": [processors.process_password],
         "MASK_INPUT": True,
         "LOOSE_VALIDATION": False,
         "USE_DEFAULT": False,
         "NEED_CONFIRM": True,
         "CONDITION": False},

        {"CONF_NAME": "CONFIG_TROVE_KS_PW",
         "CMD_OPTION": "trove-ks-passwd",
         "USAGE": ("The password to use for Trove to authenticate "
                   "with Keystone"),
         "PROMPT": "Enter the password for Trove Keystone access",
         "OPTION_LIST": [],
         "VALIDATORS": [validators.validate_not_empty],
         "DEFAULT_VALUE": "PW_PLACEHOLDER",
         "PROCESSORS": [processors.process_password],
         "MASK_INPUT": True,
         "LOOSE_VALIDATION": False,
         "USE_DEFAULT": False,
         "NEED_CONFIRM": True,
         "CONDITION": False},

        {"CONF_NAME": "CONFIG_TROVE_NOVA_USER",
         "CMD_OPTION": "trove-nova-user",
         "USAGE": "The user to use when Trove connects to Nova",
         "PROMPT": "Enter the user for Trove to use to connect to Nova",
         "OPTION_LIST": [],
         "VALIDATORS": [validators.validate_not_empty],
         "DEFAULT_VALUE": "admin",
         "MASK_INPUT": False,
         "LOOSE_VALIDATION": False,
         "USE_DEFAULT": True,
         "NEED_CONFIRM": True,
         "CONDITION": False},

        {"CONF_NAME": "CONFIG_TROVE_NOVA_TENANT",
         "CMD_OPTION": "trove-nova-tenant",
         "USAGE": "The tenant to use when Trove connects to Nova",
         "PROMPT": "Enter the tenant for Trove to use to connect to Nova",
         "OPTION_LIST": [],
         "VALIDATORS": [validators.validate_not_empty],
         "DEFAULT_VALUE": "services",
         "MASK_INPUT": False,
         "LOOSE_VALIDATION": False,
         "USE_DEFAULT": True,
         "NEED_CONFIRM": True,
         "CONDITION": False},

        {"CONF_NAME": "CONFIG_TROVE_NOVA_PW",
         "CMD_OPTION": "trove-nova-passwd",
         "USAGE": "The password to use when Trove connects to Nova",
         "PROMPT": "Enter the password for Trove to use to connect to Nova",
         "OPTION_LIST": [],
         "VALIDATORS": [validators.validate_not_empty],
         "DEFAULT_VALUE": "PW_PLACEHOLDER",  # default is admin pass
         "PROCESSORS": [process_trove_nova_pw],
         "MASK_INPUT": True,
         "LOOSE_VALIDATION": False,
         "USE_DEFAULT": False,
         "NEED_CONFIRM": True,
         "CONDITION": False},
    ]

    group = {"GROUP_NAME": "Trove",
             "DESCRIPTION": "Trove config parameters",
             "PRE_CONDITION": "CONFIG_TROVE_INSTALL",
             "PRE_CONDITION_MATCH": "y",
             "POST_CONDITION": False,
             "POST_CONDITION_MATCH": True}

    controller.addGroup(group, parameters)


def initSequences(controller):
    config = controller.CONF
    if config['CONFIG_TROVE_INSTALL'] != 'y':
        return

    steps = [
        {'title': 'Adding Trove Keystone manifest entries',
         'functions': [create_keystone_manifest]},
        {'title': 'Adding Trove manifest entries',
         'functions': [create_manifest]},
    ]

    controller.addSequence("Installing Trove", [], [], steps)

# ------------------------ step functions --------------------------


def create_keystone_manifest(config, messages):
    manifestfile = "%s_keystone.pp" % config['CONFIG_CONTROLLER_HOST']
    manifestdata = getManifestTemplate("keystone_trove.pp")
    appendManifestFile(manifestfile, manifestdata)


def create_manifest(config, messages):
    if (config['CONFIG_TROVE_NOVA_USER'] == 'admin' and
            config['CONFIG_TROVE_NOVA_PW'] == ''):
        config['CONFIG_TROVE_NOVA_PW'] = config['CONFIG_KEYSTONE_ADMIN_PW']

    manifestfile = "%s_trove.pp" % config["CONFIG_CONTROLLER_HOST"]
    manifestdata = getManifestTemplate(get_mq(config, "trove"))
    manifestdata += getManifestTemplate('trove.pp')

    fw_details = dict()
    key = "trove"
    fw_details.setdefault(key, {})
    fw_details[key]['host'] = "ALL"
    fw_details[key]['service_name'] = "trove api"
    fw_details[key]['chain'] = "INPUT"
    fw_details[key]['ports'] = ['8779']
    fw_details[key]['proto'] = "tcp"
    config['FIREWALL_TROVE_API_RULES'] = fw_details

    manifestdata += createFirewallResources('FIREWALL_TROVE_API_RULES')
    appendManifestFile(manifestfile, manifestdata, marker='trove')
