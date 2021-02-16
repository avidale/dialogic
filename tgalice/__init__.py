# -*- coding: utf-8 -*-
from __future__ import print_function

from tgalice import dialog, dialog_manager, interfaces, storage, nlu, nlg, testing, utils, dialog_connector, criteria
from tgalice.server import flask_server
from tgalice.storage import session_storage, message_logging
from tgalice.dialog_manager.base import COMMANDS
from tgalice.nlu import basic_nlu

from tgalice.dialog.names import COMMANDS, REQUEST_TYPES, SOURCES
