"""
Python module for communicating with a midas server
"""
__all__ = ['drivers', 'core', 'exceptions']

import getpass
import glob
import os
import os.path
import pydas.core

pydas.communicator = None
pydas.email = None
pydas.api_key = None
pydas.token = None

def login(email=None, password=None, api_key=None, url=None):
    """
    Do the legwork of logging into Midas, storing the api_key and token
    """
    if url is None:
        url = raw_input('Server URL: ')
    pydas.communicator = pydas.core.Communicator(url)

    if email is None:
        pydas.email = raw_input('Email: ')
    else:
        pydas.email = email
    if api_key is None:
        if password is None:
            pydas.password = getpass.getpass('Password: ')
        else:
            pydas.password = password
        pydas.api_key = pydas.communicator.get_default_api_key(pydas.email,
                                                               pydas.password)
    else:
        pydas.api_key = api_key

    return renew_token()

def renew_token():
    """
    Renew or get a token to use for transactions with Midas.
    """
    pydas.token = pydas.communicator.login_with_api_key(pydas.email, pydas.api_key)
    return pydas.token

def _upload_as_item(local_file, parent_folder_id, file_path):
    """
    Function for doing an upload of a file as an item. This should be a
    building block for user-level functions. It does not do anything to renew
    tokens or anything fancy. local file is the name of the file and
    file_path is full path to the file.
    """
    new_item = pydas.communicator.create_item(pydas.token,
                                              local_file,
                                              parent_folder_id)
    current_item_id = new_item['item_id']
    up_token = pydas.communicator.generate_upload_token(pydas.token,
                                                        current_item_id,
                                                        local_file)
    pydas.communicator.perform_upload(up_token,
                                      local_file,
                                      filepath = file_path,
                                      itemid = current_item_id)

def _create_folder(local_folder, parent_folder_id):
    """
    Function for creating a remote folder and returning the id. This should
    be a building block for user-level functions. It does not do anything to
    renew tokens or anything fancy.
    """
    new_folder = pydas.communicator.create_folder(pydas.token,
                                                  local_folder,
                                                  parent_folder_id)
    return new_folder['folder_id']

def _upload_folder_recursive(local_folder,
                             parent_folder_id,
                             parent_folder_name,
                             leaf_folders_as_items=False):
    """
    Function for using os.walk to recursively upload a folder an all of its
    decendants.
    """
    if leaf_folders_as_items and _has_only_files(local_folder):
        print 'Creating Item: %s/%s' % (parent_folder_name, local_folder)
        _upload_folder_as_item(local_folder, parent_folder_id)
        return
    else:
        print 'Creating Folder: %s/%s' % (parent_folder_name, local_folder)
        new_folder_id = _create_folder(local_folder,
                                       parent_folder_id)
        folder_id_dict = dict()
        folder_id_dict[local_folder] = new_folder_id
        for top_dir, subdirs, files in os.walk(local_folder):
            if folder_id_dict.has_key(top_dir):
                current_parent_id = folder_id_dict[top_dir]
            for subdir in subdirs:
                full_path = os.path.join(top_dir, subdir)
                if leaf_folders_as_items and _has_only_files(full_path):
                    print 'Creating Item %s/%s' % (parent_folder_name,
                                                   full_path)
                    _upload_folder_as_item(full_path, current_parent_id)
                else:
                    print 'Creating Folder %s/%s' % (parent_folder_name,
                                                     full_path)
                    new_folder_id = _create_folder(subdir,
                                                   current_parent_id)
                    folder_id_dict[full_path] = new_folder_id
            for leaf_file in files:
                full_path = os.path.join(top_dir, leaf_file)
                print 'Uploading Item %s/%s' % (parent_folder_name, full_path)
                _upload_as_item(leaf_file,
                                current_parent_id,
                                full_path)

def _has_only_files(local_folder):
    """Returns whether a folder has only files. This will be false if the
    folder contains any subdirectories."""
    for entry in os.listdir(local_folder):
        full_entry = os.path.join(local_folder, entry)
        if os.path.isdir(full_entry):
            return False
    return True
    
def _upload_folder_as_item(local_folder, parent_folder_id):
    """will take a filesystem directory subdir, a subdirectory of top_dir,
       will try to create a midas item under parent_folder_id,
       then upload all files in that subdirectory as a bitstream of the
       newly created item"""
    # create the item for the subdir
    new_item = pydas.communicator.create_item(pydas.token,
                                              os.path.basename(local_folder),
                                              parent_folder_id)
    item_id = new_item['item_id']
    subdircontents = os.listdir(local_folder)
    # for each file in the subdir, add it to the item
    filecount = len(subdircontents)
    for (ind, current_file) in enumerate(subdircontents):
        print "Uploading Bitstream: %s (%d of %d)" % (current_file,
                                                     ind+1,
                                                     filecount)
        filepath = os.path.join(local_folder, current_file)
        upload_token = pydas.communicator.generate_upload_token(pydas.token,
                                                                item_id,
                                                                current_file)
        pydas.communicator.perform_upload(upload_token,
                                          current_file,
                                          filepath = filepath,
                                          itemid = item_id)

def upload(file_pattern, destination = 'Private', leaf_folders_as_items=False):
    """
    Upload a pattern of files. This will recursively walk down every tree in
    the file pattern to create a hierarchy on the server. As of right now, this
    places the file into the currently logged in user's home directory.
    """
    if pydas.api_key:
        pydas.renew_token()
    else:
        pydas.login()

    # Logic for finding the proper folder to place the files in.
    parent_folder_id = None
    parent_folder_name = None
    user_folders = pydas.communicator.list_user_folders(pydas.token)
    for cur_folder in user_folders:
        if cur_folder['name'] == destination:
            parent_folder_id = cur_folder['folder_id']
            parent_folder_name = cur_folder['name']
    if parent_folder_id is None:
        print 'Unable to locate specified destination. ',
        print 'Defaulting to %s' % user_folders[0]['name']
        parent_folder_id = user_folders[0]['folder_id']
        parent_folder_name = user_folders[0]['name']

    for current_file in glob.iglob(file_pattern):
        if os.path.isfile(current_file):
            print 'Uploading Item: %s/%s' % (parent_folder_name, current_file)
            _upload_as_item(os.path.basename(current_file),
                            parent_folder_id,
                            current_file)
        else:
            _upload_folder_recursive(current_file,
                                     parent_folder_id,
                                     parent_folder_name,
                                     leaf_folders_as_items)
