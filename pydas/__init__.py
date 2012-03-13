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
pydas.item_upload_callbacks = []

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

def add_item_upload_callback(callback):
    """Pass a function to be called when an item is created. This can be quite
    useful for performing actions such as notifications of upload progress as
    well as calling additional api functions.

    :param callback: A function that takes thre arguments. The first argument is
    the communicator object of the current pydas context, the second is the
    currently active API token and the third is the id of the item that was
    created to result in the callback function's invocatation.
    """
    pydas.item_upload_callbacks.append(callback)

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
    for callback in pydas.item_upload_callbacks:
        callback(pydas.communicator, pydas.token, current_item_id)

def _create_folder(local_folder, parent_folder_id):
    """
    Function for creating a remote folder and returning the id. This should
    be a building block for user-level functions. It does not do anything to
    renew tokens or anything fancy.
    """
    new_folder = pydas.communicator.create_folder(pydas.token,
                                                  os.path.basename(local_folder),
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
        print 'Creating Item from %s' % local_folder
        _upload_folder_as_item(local_folder, parent_folder_id)
        return
    else:
        print 'Creating Folder from %s' % local_folder
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
                    print 'Creating Item from %s.' % full_path
                    _upload_folder_as_item(full_path, current_parent_id)
                else:
                    print 'Creating Folder from %s.' % full_path
                    new_folder_id = _create_folder(subdir,
                                                   current_parent_id)
                    folder_id_dict[full_path] = new_folder_id
            for leaf_file in files:
                full_path = os.path.join(top_dir, leaf_file)
                print 'Uploading Item from %s' % full_path
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
    """Take a folder and use its base name as the name of a new item. Then,
    upload its containing files into the new item as bitstreams.

    :param local_folder: The path to the folder to be uploaded.
    :param parent_folder_id: The id of the destination folder for the new item.
    """
    # create the item for the subdir
    new_item = pydas.communicator.create_item(pydas.token,
                                              os.path.basename(local_folder),
                                              parent_folder_id)
    item_id = new_item['item_id']
    subdircontents = os.listdir(local_folder)
    # for each file in the subdir, add it to the item
    filecount = len(subdircontents)
    for (ind, current_file) in enumerate(subdircontents):
        filepath = os.path.join(local_folder, current_file)
        print "Uploading Bitstream from %s (%d of %d)" % (filepath,
                                                          ind+1,
                                                          filecount)
        upload_token = pydas.communicator.generate_upload_token(pydas.token,
                                                                item_id,
                                                                current_file)
        pydas.communicator.perform_upload(upload_token,
                                          current_file,
                                          filepath = filepath,
                                          itemid = item_id)
    for callback in pydas.item_upload_callbacks:
        callback(pydas.communicator, pydas.token, item_id)

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
            print 'Uploading Item from %s' % current_file
            _upload_as_item(os.path.basename(current_file),
                            parent_folder_id,
                            current_file)
        else:
            _upload_folder_recursive(current_file,
                                     parent_folder_id,
                                     parent_folder_name,
                                     leaf_folders_as_items)



def _descend_folder_for_id(parsed_path, folder_id):
    """Descend a parsed path to return a folder id starting from folder_id
    
    :param parsed_path: a list of folders from top to bottom of a hierarchy
    :param folder_id: The id of the folder from which to start the decent
    :returns: The id of the found folder or -1
    """
    if len(parsed_path) == 0:
        return folder_id
    if pydas.api_key:
        pydas.renew_token()
    else:
        pydas.login()
    base_folder = pydas.communicator.folder_get(pydas.token,
                                                folder_id)
    cur_folder_id = -1
    for path_part in parsed_path:
        cur_folder_id = base_folder['folder_id']
        cur_children = pydas.communicator.folder_children(pydas.token,
                                                          cur_folder_id)
        found = False
        for inner_folder in cur_children['folders']:
            if inner_folder['name'] == path_part:
                base_folder = pydas.communicator.folder_get(pydas.token,
                                                            inner_folder['folder_id'])
                cur_folder_id = base_folder['folder_id']
                found = True
                break
        if not found:
            return -1
    return cur_folder_id

def _search_folder_for_item_or_folder(name, folder_id):
    """Find an item or folder matching the name (folder first if both are
    present).

    :param name: The name of the resource
    :param folder_id: The folder to search within
    :returns: A tuple indicating whether the resource is an item an the id of
    said resoure. i.e. (True, item_id) or (False, folder_id). Note that in the
    event that we do not find a result return (False, -1)
    """
    if pydas.api_key:
        pydas.renew_token()
    else:
        pydas.login()
    children = pydas.communicator.folder_children(pydas.token, folder_id)
    for folder in children['folders']:
        if folder['name'] == name:
            return False, folder['folder_id'] # Found a folder
    for item in children['items']:
        if item['name'] == name:
            return True, item['item_id'] # Found an item
    return False, -1 # Found nothing
                                                

def _find_resource_id_from_path(path):
    """Get a folder id from a path on the server.

    Warning: This is NOT efficient at all.
    
    The schema for this path is:
    path := "/users/<name>/" | "/communities/<name>" , {<subfolder>/}
    name := <firstname> , "_" , <lastname>

    :param path: The virtual path on the server.
    :returns: a tuple indicating True or False about whether the resource is an
    item and id of the resource i.e. (True, item_id) or (False, folder_id)
    """
    if pydas.api_key:
        pydas.renew_token()
    else:
        pydas.login()
    parsed_path = path.split('/')
    if parsed_path[-1] == '':
        parsed_path.pop()
    if path.startswith('/users/'):
        parsed_path.pop(0) # remove '' before /
        parsed_path.pop(0) # remove 'users'
        name = parsed_path.pop(0) # remove '<firstname>_<lastname>'
        firstname, lastname = name.split('_')
        end = parsed_path.pop()
        user = pydas.communicator.get_user_by_name(firstname, lastname)
        leaf_folder_id = _descend_folder_for_id(parsed_path, user['folder_id'])
        return _search_folder_for_item_or_folder(end, leaf_folder_id)
    elif path.startswith('/communities/'):
        parsed_path.pop(0) # remove '' before /
        parsed_path.pop(0) # remove 'communities'
        community_name = parsed_path.pop(0) # remove '<community>'
        end = parsed_path.pop()
        community = pydas.communicator.get_community_by_name(community_name)
        leaf_folder_id =  _descend_folder_for_id(parsed_path,
                                                 community['folder_id'])
        return _search_folder_for_item_or_folder(end, leaf_folder_id)
    else:
        return False, -1
        
    
def _download_folder_recursive(folder_id, path='.'):
    """Download a folder to the specified path along with any children.

    :param folder_id: The id of the target folder
    :param path: (optional) the location to download the folder
    """
    if pydas.api_key:
        pydas.renew_token()
    else:
        pydas.login()
    cur_folder = pydas.communicator.folder_get(pydas.token, folder_id)
    folder_path = os.path.join(path, cur_folder['name'])
    print 'Creating Folder at %s' % folder_path
    os.mkdir(folder_path)
    cur_children = pydas.communicator.folder_children(pydas.token, folder_id)
    for item in cur_children['items']:
        _download_item(item['item_id'], folder_path)
    for folder in cur_children['folders']:
        _download_folder_recursive(folder['folder_id'], folder_path)

def _download_item(item_id, path='.'):
    """Download the requested item to the specified path.

    :param item_id: The id of the item to be downloaded
    :param path: (optional) the location to download the item
    """
    if pydas.api_key:
        pydas.renew_token()
    else:
        pydas.login()
    filename, content_iter =  pydas.communicator.download_item(item_id,
                                                               pydas.token)
    item_path = os.path.join(path, filename)
    print 'Creating File at %s' % item_path
    outFile = open(item_path, 'wb')
    for block in content_iter:
        outFile.write(block)
    outFile.close()

def download(server_path, local_path = '.'):
    """Recursively download a file or item from Midas.

    :param server_path: The location on the server to find the resource to download
    :param local_path: The location on the client to store the downloaded data
    """
    if pydas.api_key:
        pydas.renew_token()
    else:
        pydas.login()
    is_item, resource_id = _find_resource_id_from_path(server_path)
    if resource_id == -1:
        print 'Unable to Locate %s' % server_path
    else:
        if is_item:
            _download_item(resource_id, local_path)
        else:
            _download_folder_recursive(resource_id, local_path)
    
