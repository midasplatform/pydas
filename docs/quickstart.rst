pydas Quick Start
=================


Module level method examples
----------------------------

The easiest way to use pydas is by using high level module level methods.

Login to your Midas Server instance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

>>> import pydas
>>> pydas.login()
Server URL: http://domain/midas3
Email: email@email.com
Password: PASSWORD
'FK0uEYfciJcjBbaAadfTC123213s12810Favf0PJPULX'

For reference, this last string is your session token, but you will probably not need to use it.

Simple upload example
^^^^^^^^^^^^^^^^^^^^^

Let's say you have a subdirectory under your current location called myfiles, with 2 files in it::

    myfiles
        file1.txt
        file2.txt

After we have logged in to pydas, we want to upload this directory to our Midas Server 3 instance.

>>> pydas.upload('myfiles')
Creating Folder from myfiles
Uploading Item from myfiles/file1.txt
Uploading Item from myfiles/file2.txt

By default, this will create a folder under your Midas Server 3 user's private folder called myfiles, with 2 items, one for each of the files.

This upload method will upload recursively, so if you have subdirectories under your uploaded directory, they will have corresponding folders created on the Midas Server to mirror the directory structure in your local machine.


Upload example treating leaf folders as items
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Let's say you have some folders with only files in them (call them leaf folders), and you want each of the leaf folders to have all files in them uploaded to the same item.

Here we have a top level folder folders_as_items, which has two subfolders.  Each of the subfolders has two files::

    folders_as_items
        item1
            bitstream1_1.txt
            bitstream1_2.txt
        item2
            bitstream2_1.txt
            bitstream2_2.txt

>>> pydas.upload('folders_as_items',  leaf_folders_as_items=True)
Creating Folder from folders_as_items
Creating Item from folders_as_items/item1.
Uploading Bitstream from folders_as_items/item1/bitstream1_1.txt (1 of 2)
Uploading Bitstream from folders_as_items/item1/bitstream1_2.txt (2 of 2)
Creating Item from folders_as_items/item2.
Uploading Bitstream from folders_as_items/item2/bitstream2_1.txt (1 of 2)
Uploading Bitstream from folders_as_items/item2/bitstream2_2.txt (2 of 2)

This upload will create a folder in your Midas Server private folder called folders_as_items, and in that folder will create two items, item1 and item2.  item1 will have 2 bitstreams, and item2 will have two bitstreams, corresponding to the files that are in each of the leaf folders.


Upload example for DICOM data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Let's say you have a folder that contains subfolders, each of the subfolders is a DICOM series.  You would like to upload these subfolders such that all of the files in the subfolders are combined into one item, and once the item is created, DICOM Metadata is extracted from the item.  In this case we will treat the subfolders as leaf folders, and we will also add a callback after the upload of the item to extract DICOM Metadata::

    dicom_data
        series1
            00380001.dcm
            00380002.dcm
            00380003.dcm
            00380004.dcm
        series2
            00500001.dcm
            00500002.dcm
            00500003.dcm
            00500004.dcm


>>> extract_dicom_callback = lambda communicator, token, item_id: communicator.extract_dicommetadata(token, item_id)
>>> pydas.add_item_upload_callback(extract_dicom_callback)
>>> pydas.upload('dicom_data', leaf_folders_as_items=True)
Creating Folder from dicom_data
Creating Item from dicom_data/series2.
Uploading Bitstream from dicom_data/series2/00500002.dcm (1 of 4)
Uploading Bitstream from dicom_data/series2/00500003.dcm (2 of 4)
Uploading Bitstream from dicom_data/series2/00500004.dcm (3 of 4)
Uploading Bitstream from dicom_data/series2/00500001.dcm (4 of 4)
Creating Item from dicom_data/series1.
Uploading Bitstream from dicom_data/series1/00380001.dcm (1 of 4)
Uploading Bitstream from dicom_data/series1/00380003.dcm (2 of 4)
Uploading Bitstream from dicom_data/series1/00380002.dcm (3 of 4)
Uploading Bitstream from dicom_data/series1/00380004.dcm (4 of 4)

