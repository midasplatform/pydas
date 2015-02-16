#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#
# Library: pydas
#
# Copyright 2010 Kitware, Inc., 28 Corporate Dr., Clifton Park, NY 12065, USA.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
###############################################################################

"""API for pydas."""

import getpass
import glob
import os
import os.path
import hashlib

from core import Communicator
import session


def login(email=None, password=None, api_key=None, application='Default',
          url=None, verify_ssl_certificate=True):
    """
    Do the legwork of logging into the Midas Server instance, storing the API
    key and token.

    :param email: (optional) Email address to login with. If not set, the
        console will be prompted.
    :type email: None | string
    :param password: (optional) User password to login with. If not set and no
        'api_key' is set, the console will be prompted.
    :type password: None | string
    :param api_key: (optional) API key to login with. If not set, password
        login with be used.
    :type api_key: None | string
    :param application: (optional) Application name to be used with 'api_key'.
    :type application: string
    :param url: (optional) URL address of the Midas Server instance to login
        to. If not set, the console will be prompted.
    :type url: None | string
    :param verify_ssl_certificate: (optional) If True, the SSL certificate will
        be verified
    :type verify_ssl_certificate: bool
    :returns: API token.
    :rtype: string
    """
    try:
        input_ = raw_input
    except NameError:
        input_ = input

    if url is None:
        url = input_('Server URL: ')
    url = url.rstrip('/')
    if session.communicator is None:
        session.communicator = Communicator(url)
    else:
        session.communicator.url = url

    session.communicator.verify_ssl_certificate = verify_ssl_certificate

    if email is None:
        email = input_('Email: ')
    session.email = email

    if api_key is None:
        if password is None:
            password = getpass.getpass()
        session.api_key = session.communicator.get_default_api_key(
            session.email, password)
        session.application = 'Default'
    else:
        session.api_key = api_key
        session.application = application

    return renew_token()


def renew_token():
    """
    Renew or get a token to use for transactions with the Midas Server
    instance.

    :returns: API token.
    :rtype: string
    """
    session.token = session.communicator.login_with_api_key(
        session.email, session.api_key, application=session.application)
    if len(session.token) < 10:  # HACK to check for mfa being enabled
        one_time_pass = getpass.getpass('One-Time Password: ')
        session.token = session.communicator.mfa_otp_login(
            session.token, one_time_pass)
    return session.token


def verify_credentials():
    """
    Check if the current credentials are valid and login or renew as needed.

    :returns: API token.
    :rtype: string
    """
    if session.token is not None:
        return session.token
    elif session.api_key is not None:
        return renew_token()
    else:
        return login()


def add_item_upload_callback(callback):
    """
    Pass a function to be called when an item is created. This can be quite
    useful for performing actions such as notifications of upload progress as
    well as calling additional API functions.

    :param callback: A function that takes three arguments. The first argument
        is the communicator object of the current pydas context, the second is
        the currently active API token and the third is the id of the item that
        was created to result in the callback function's invocation.
    :type callback: (Communicator, string, int) -> unknown
    """
    session.item_upload_callbacks.append(callback)


def _create_or_reuse_item(local_file, parent_folder_id, reuse_existing=False):
    """
    Create an item from the local file in the Midas Server folder corresponding
    to the parent folder id.

    :param local_file: full path to a file on the local file system
    :type local_file: string
    :param parent_folder_id: id of parent folder on the Midas Server instance,
        where the item will be added
    :type parent_folder_id: int | long
    :param reuse_existing: (optional) whether to accept an existing item of the
        same name in the same location, or create a new one instead
    :type reuse_existing: bool
    """
    local_item_name = os.path.basename(local_file)
    item_id = None
    if reuse_existing:
        # check by name to see if the item already exists in the folder
        children = session.communicator.folder_children(
            session.token, parent_folder_id)
        items = children['items']

        for item in items:
            if item['name'] == local_item_name:
                item_id = item['item_id']
                break

    if item_id is None:
        # create the item for the subdir
        new_item = session.communicator.create_item(
            session.token, local_item_name, parent_folder_id)
        item_id = new_item['item_id']

    return item_id


def _create_or_reuse_folder(local_folder, parent_folder_id,
                            reuse_existing=False):
    """
    Create a folder from the local file in the midas folder corresponding to
    the parent folder id.

    :param local_folder: full path to a directory on the local file system
    :type local_folder: string
    :param parent_folder_id: id of parent folder on the Midas Server instance,
        where the folder will be added
    :type parent_folder_id: int | long
    :param reuse_existing: (optional) whether to accept an existing folder of
       the same name in the same location, or create a new one instead
    :type reuse_existing: bool
    """
    local_folder_name = os.path.basename(local_folder)
    folder_id = None
    if reuse_existing:
        # check by name to see if the folder already exists in the folder
        children = session.communicator.folder_children(
            session.token, parent_folder_id)
        folders = children['folders']

        for folder in folders:
            if folder['name'] == local_folder_name:
                folder_id = folder['folder_id']
                break

    if folder_id is None:
        # create the item for the subdir
        new_folder = session.communicator.create_folder(session.token,
                                                        local_folder_name,
                                                        parent_folder_id)
        folder_id = new_folder['folder_id']

    return folder_id


def _streaming_file_md5(file_path):
    """
    Create and return a hex checksum using the MD5 sum of the passed in file.
    This will stream the file, rather than load it all into memory.

    :param file_path: full path to the file
    :type file_path: string
    :returns: a hex checksum
    :rtype: string
    """
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        # iter needs an empty byte string for the returned iterator to halt at
        # EOF
        for chunk in iter(lambda: f.read(128 * md5.block_size), b''):
            md5.update(chunk)
    return md5.hexdigest()


def _create_bitstream(file_path, local_file, item_id, log_ind=None):
    """
    Create a bitstream in the given item.

    :param file_path: full path to the local file
    :type file_path: string
    :param local_file: name of the local file
    :type local_file: string
    :param log_ind: (optional) any additional message to log upon creation of
        the bitstream
    :type log_ind: None | string
    """
    checksum = _streaming_file_md5(file_path)
    upload_token = session.communicator.generate_upload_token(
        session.token, item_id, local_file, checksum)

    if upload_token != '':
        log_trace = 'Uploading bitstream from {0}'.format(file_path)
        # only need to perform the upload if we haven't uploaded before
        # in this cae, the upload token would not be empty
        session.communicator.perform_upload(
            upload_token, local_file, filepath=file_path, itemid=item_id)
    else:
        log_trace = 'Adding a bitstream link in this item to an existing ' \
                    'bitstream from {0}'.format(file_path)

    if log_ind is not None:
        log_trace += log_ind
    print(log_trace)


def _upload_as_item(local_file, parent_folder_id, file_path,
                    reuse_existing=False):
    """
    Function for doing an upload of a file as an item. This should be a
    building block for user-level functions.

    :param local_file: name of local file to upload
    :type local_file: string
    :param parent_folder_id: id of parent folder on the Midas Server instance,
        where the item will be added
    :type parent_folder_id: int | long
    :param file_path: full path to the file
    :type file_path: string
    :param reuse_existing: (optional) whether to accept an existing item of the
        same name in the same location, or create a new one instead
    :type reuse_existing: bool
    """
    current_item_id = _create_or_reuse_item(local_file, parent_folder_id,
                                            reuse_existing)
    _create_bitstream(file_path, local_file, current_item_id)
    for callback in session.item_upload_callbacks:
        callback(session.communicator, session.token, current_item_id)


def _create_folder(local_folder, parent_folder_id):
    """
    Function for creating a remote folder and returning the id. This should be
    a building block for user-level functions.

    :param local_folder: full path to a local folder
    :type local_folder: string
    :param parent_folder_id: id of parent folder on the Midas Server instance,
        where the new folder will be added
    :type parent_folder_id: int | long
    :returns: id of the remote folder that was created
    :rtype: int | long
    """
    new_folder = session.communicator.create_folder(
        session.token, os.path.basename(local_folder), parent_folder_id)
    return new_folder['folder_id']


def _upload_folder_recursive(local_folder,
                             parent_folder_id,
                             leaf_folders_as_items=False,
                             reuse_existing=False):
    """
    Function to recursively upload a folder and all of its descendants.

    :param local_folder: full path to local folder to be uploaded
    :type local_folder: string
    :param parent_folder_id: id of parent folder on the Midas Server instance,
        where the new folder will be added
    :type parent_folder_id: int | long
    :param leaf_folders_as_items: (optional) whether leaf folders should have
        all files uploaded as single items
    :type leaf_folders_as_items: bool
    :param reuse_existing: (optional) whether to accept an existing item of the
        same name in the same location, or create a new one instead
    :type reuse_existing: bool
    """
    if leaf_folders_as_items and _has_only_files(local_folder):
        print('Creating item from {0}'.format(local_folder))
        _upload_folder_as_item(local_folder, parent_folder_id, reuse_existing)
        return
    else:
        # do not need to check if folder exists, if it does, an attempt to
        # create it will just return the existing id
        print('Creating folder from {0}'.format(local_folder))
        new_folder_id = _create_or_reuse_folder(local_folder, parent_folder_id,
                                                reuse_existing)

        for entry in sorted(os.listdir(local_folder)):
            full_entry = os.path.join(local_folder, entry)
            if os.path.islink(full_entry):
                # os.walk skips symlinks by default
                continue
            elif os.path.isdir(full_entry):
                _upload_folder_recursive(full_entry,
                                         new_folder_id,
                                         leaf_folders_as_items,
                                         reuse_existing)
            else:
                print('Uploading item from {0}'.format(full_entry))
                _upload_as_item(entry,
                                new_folder_id,
                                full_entry,
                                reuse_existing)


def _has_only_files(local_folder):
    """
    Return whether a folder contains only files. This will be False if the
    folder contains any subdirectories.

    :param local_folder: full path to the local folder
    :type local_folder: string
    :returns: True if the folder contains only files
    :rtype: bool
    """
    return not any(os.path.isdir(os.path.join(local_folder, entry))
                   for entry in os.listdir(local_folder))


def _upload_folder_as_item(local_folder, parent_folder_id,
                           reuse_existing=False):
    """
    Upload a folder as a new item. Take a folder and use its base name as the
    name of a new item. Then, upload its containing files into the new item as
    bitstreams.

    :param local_folder: The path to the folder to be uploaded
    :type local_folder: string
    :param parent_folder_id: The id of the destination folder for the new item.
    :type parent_folder_id: int | long
    :param reuse_existing: (optional) whether to accept an existing item of the
        same name in the same location, or create a new one instead
    :type reuse_existing: bool
    """
    item_id = _create_or_reuse_item(local_folder, parent_folder_id,
                                    reuse_existing)

    subdir_contents = sorted(os.listdir(local_folder))
    # for each file in the subdir, add it to the item
    filecount = len(subdir_contents)
    for (ind, current_file) in enumerate(subdir_contents):
        file_path = os.path.join(local_folder, current_file)
        log_ind = '({0} of {1})'.format(ind + 1, filecount)
        _create_bitstream(file_path, current_file, item_id, log_ind)

    for callback in session.item_upload_callbacks:
        callback(session.communicator, session.token, item_id)


def upload(file_pattern, destination='Private', leaf_folders_as_items=False,
           reuse_existing=False):
    """
    Upload a pattern of files. This will recursively walk down every tree in
    the file pattern to create a hierarchy on the server. As of right now, this
    places the file into the currently logged in user's home directory.

    :param file_pattern: a glob type pattern for files
    :type file_pattern: string
    :param destination: (optional) name of the midas destination folder,
        defaults to Private
    :type destination: string
    :param leaf_folders_as_items: (optional) whether leaf folders should have
        all files uploaded as single items
    :type leaf_folders_as_items: bool
    :param reuse_existing: (optional) whether to accept an existing item of the
        same name in the same location, or create a new one instead
    :type reuse_existing: bool
    """
    session.token = verify_credentials()

    # Logic for finding the proper folder to place the files in.
    parent_folder_id = None
    user_folders = session.communicator.list_user_folders(session.token)
    if destination.startswith('/'):
        parent_folder_id = _find_resource_id_from_path(destination)
    else:
        for cur_folder in user_folders:
            if cur_folder['name'] == destination:
                parent_folder_id = cur_folder['folder_id']
    if parent_folder_id is None:
        print('Unable to locate specified destination. Defaulting to {0}.'
              .format(user_folders[0]['name']))
        parent_folder_id = user_folders[0]['folder_id']

    for current_file in glob.iglob(file_pattern):
        current_file = os.path.normpath(current_file)
        if os.path.isfile(current_file):
            print('Uploading item from {0}'.format(current_file))
            _upload_as_item(os.path.basename(current_file),
                            parent_folder_id,
                            current_file,
                            reuse_existing)
        else:
            _upload_folder_recursive(current_file,
                                     parent_folder_id,
                                     leaf_folders_as_items,
                                     reuse_existing)


def _descend_folder_for_id(parsed_path, folder_id):
    """
    Descend a path to return a folder id starting from the given folder id.

    :param parsed_path: a list of folders from top to bottom of a hierarchy
    :type parsed_path: list[string]
    :param folder_id: The id of the folder from which to start the descent
    :type folder_id: int | long
    :returns: The id of the found folder or -1
    :rtype: int | long
    """
    if len(parsed_path) == 0:
        return folder_id

    session.token = verify_credentials()

    base_folder = session.communicator.folder_get(session.token,
                                                  folder_id)
    cur_folder_id = -1
    for path_part in parsed_path:
        cur_folder_id = base_folder['folder_id']
        cur_children = session.communicator.folder_children(
            session.token, cur_folder_id)
        for inner_folder in cur_children['folders']:
            if inner_folder['name'] == path_part:
                base_folder = session.communicator.folder_get(
                    session.token, inner_folder['folder_id'])
                cur_folder_id = base_folder['folder_id']
                break
        else:
            return -1
    return cur_folder_id


def _search_folder_for_item_or_folder(name, folder_id):
    """
    Find an item or folder matching the name. A folder will be found first if
    both are present.

    :param name: The name of the resource
    :type name: string
    :param folder_id: The folder to search within
    :type folder_id: int | long
    :returns: A tuple indicating whether the resource is an item an the id of
        said resource. i.e. (True, item_id) or (False, folder_id). Note that in
        the event that we do not find a result return (False, -1)
    :rtype: (bool, int | long)
    """
    session.token = verify_credentials()

    children = session.communicator.folder_children(session.token, folder_id)
    for folder in children['folders']:
        if folder['name'] == name:
            return False, folder['folder_id']  # Found a folder
    for item in children['items']:
        if item['name'] == name:
            return True, item['item_id']  # Found an item
    return False, -1  # Found nothing


def _find_resource_id_from_path(path):
    """
    Get a folder id from a path on the server.

    Warning: This is NOT efficient at all.

    The schema for this path is:
    path := "/users/<name>/" | "/communities/<name>" , {<subfolder>/}
    name := <firstname> , "_" , <lastname>

    :param path: The virtual path on the server.
    :type path: string
    :returns: a tuple indicating True or False about whether the resource is an
        item and id of the resource i.e. (True, item_id) or (False, folder_id)
    :rtype: (bool, int | long)
    """
    session.token = verify_credentials()

    parsed_path = path.split('/')
    if parsed_path[-1] == '':
        parsed_path.pop()
    if path.startswith('/users/'):
        parsed_path.pop(0)  # remove '' before /
        parsed_path.pop(0)  # remove 'users'
        name = parsed_path.pop(0)  # remove '<firstname>_<lastname>'
        firstname, lastname = name.split('_')
        end = parsed_path.pop()
        user = session.communicator.get_user_by_name(firstname, lastname)
        leaf_folder_id = _descend_folder_for_id(parsed_path, user['folder_id'])
        return _search_folder_for_item_or_folder(end, leaf_folder_id)
    elif path.startswith('/communities/'):
        print(parsed_path)
        parsed_path.pop(0)  # remove '' before /
        parsed_path.pop(0)  # remove 'communities'
        community_name = parsed_path.pop(0)  # remove '<community>'
        end = parsed_path.pop()
        community = session.communicator.get_community_by_name(community_name)
        leaf_folder_id = _descend_folder_for_id(parsed_path,
                                                community['folder_id'])
        return _search_folder_for_item_or_folder(end, leaf_folder_id)
    else:
        return False, -1


def _download_folder_recursive(folder_id, path='.'):
    """
    Download a folder to the specified path along with any children.

    :param folder_id: The id of the target folder
    :type folder_id: int | long
    :param path: (optional) the location to download the folder
    :type path: string
    """
    session.token = verify_credentials()

    cur_folder = session.communicator.folder_get(session.token, folder_id)
    folder_path = os.path.join(path, cur_folder['name'])
    print('Creating folder at {0}'.format(folder_path))
    os.mkdir(folder_path)
    cur_children = session.communicator.folder_children(
        session.token, folder_id)
    for item in cur_children['items']:
        _download_item(item['item_id'], folder_path)
    for folder in cur_children['folders']:
        _download_folder_recursive(folder['folder_id'], folder_path)


def _download_item(item_id, path='.'):
    """
    Download the requested item to the specified path.

    :param item_id: The id of the item to be downloaded
    :type item_id: int | long
    :param path: (optional) the location to download the item
    :type path: string
    """
    session.token = verify_credentials()

    filename, content_iter = session.communicator.download_item(
        item_id, session.token)
    item_path = os.path.join(path, filename)
    print('Creating file at {0}'.format(item_path))
    out_file = open(item_path, 'wb')
    for block in content_iter:
        out_file.write(block)
    out_file.close()


def download(server_path, local_path='.'):
    """
    Recursively download a file or item from the Midas Server instance.

    :param server_path: The location on the server to find the resource to
        download
    :type server_path: string
    :param local_path: The location on the client to store the downloaded data
    :type local_path: string
    """
    session.token = verify_credentials()

    is_item, resource_id = _find_resource_id_from_path(server_path)
    if resource_id == -1:
        print('Unable to locate {0}'.format(server_path))
    else:
        if is_item:
            _download_item(resource_id, local_path)
        else:
            _download_folder_recursive(resource_id, local_path)
